// 对话提取 content script — 五层记忆系统自动收集
// 支持：① 选中文字采集 ② 可视化元素配置 ③ 自动提取模式
// 通过 background.js 代理请求，绕过 CORS

(function () {
  'use strict';

  const STORAGE_KEY = 'study_hub_dialogues';
  const AUTO_EXTRACT_KEY = 'study_hub_auto_extract';
  const CUSTOM_SELECTORS_KEY = 'study_hub_custom_selectors';
  const INTERVAL_MS = 30000;

  let adapter = null;
  let customSelector = null;
  let lastSnapshot = '';
  let lastActivity = Date.now();
  let autoExtractEnabled = true;
  let hasExtracted = false;
  let isInitialized = false;

  const AUTO_EXTRACT_CONFIG = {
    idle_threshold: 5 * 60 * 1000,
    end_signals: ['谢谢', '再见', '先这样', 'ok', '好的', '搞定了', '完成了', '没问题', '可以了', '就这样', '先到这里'],
    min_dialogue_length: 200,
  };

  // ========== 初始化 ==========

  async function init() {
    if (isInitialized) return;
    isInitialized = true;

    console.log('[study-hub] content script 初始化, hostname:', window.location.hostname);

    // 加载自定义选择器
    await loadCustomSelector();

    // 获取适配器（内置或自定义）
    adapter = getAdapterSync();
    if (!adapter) adapter = await getAdapter();

    // 加载自动提取设置
    chrome.storage.sync.get([AUTO_EXTRACT_KEY], (data) => {
      if (data[AUTO_EXTRACT_KEY] !== undefined) {
        autoExtractEnabled = data[AUTO_EXTRACT_KEY];
      }
    });

    // 注入 UI
    setTimeout(() => {
      injectCaptureButton();
      if (adapter) {
        scan();
        setInterval(scan, INTERVAL_MS);
        window.addEventListener('beforeunload', () => scan());
      }
    }, 2000);

    // 监听用户活动
    document.addEventListener('input', () => { lastActivity = Date.now(); });
    document.addEventListener('click', () => { lastActivity = Date.now(); });
    document.addEventListener('keydown', () => { lastActivity = Date.now(); });
  }

  // ========== 自定义选择器管理 ==========

  async function loadCustomSelector() {
    return new Promise((resolve) => {
      const hostname = window.location.hostname;
      chrome.storage.sync.get([CUSTOM_SELECTORS_KEY], (data) => {
        const selectors = data[CUSTOM_SELECTORS_KEY] || {};
        if (selectors[hostname]) {
          customSelector = selectors[hostname];
          console.log('[study-hub] 加载自定义选择器:', hostname, customSelector);
        }
        resolve();
      });
    });
  }

  function saveCustomSelector(selector) {
    const hostname = window.location.hostname;
    chrome.storage.sync.get([CUSTOM_SELECTORS_KEY], (data) => {
      const selectors = data[CUSTOM_SELECTORS_KEY] || {};
      selectors[hostname] = selector;
      chrome.storage.sync.set({ [CUSTOM_SELECTORS_KEY]: selectors }, () => {
        console.log('[study-hub] 保存自定义选择器:', hostname, selector);
        customSelector = selector;
        adapter = null; // 清除内置适配器，优先使用自定义
        showToast('✅ 配置已保存，刷新页面生效');
      });
    });
  }

  // ========== 内容提取 ==========

  function extractCurrentDialogue() {
    // 优先使用自定义选择器
    if (customSelector) {
      const elements = document.querySelectorAll(customSelector);
      const texts = [];
      elements.forEach(el => {
        const text = el.textContent.trim();
        if (text.length > 5) texts.push(text);
      });
      return texts.join('\n\n---\n\n');
    }

    // 使用内置适配器
    if (!adapter || !adapter.selectors) return '';
    let elements = document.querySelectorAll(adapter.selectors.container);
    if (elements.length === 0 && adapter.selectors.fallback) {
      elements = document.querySelectorAll(adapter.selectors.fallback);
    }
    const texts = [];
    elements.forEach(el => {
      const text = adapter.extract ? adapter.extract(el) : el.textContent.trim();
      if (text) texts.push(text);
    });
    return texts.join('\n\n---\n\n');
  }

  // ========== 网页文章提取（MarkDownload 风格）==========

  function extractArticle() {
    const url = window.location.href;
    const title = document.title || '未命名页面';

    // 1. 尝试 Readability 风格提取
    const article = extractReadableContent();
    if (article && article.content && article.content.length > 200) {
      return {
        title: article.title || title,
        content: article.content,
        url: url,
        excerpt: article.excerpt || '',
        byline: article.byline || '',
      };
    }

    // 2. fallback：简单正文提取
    const fallbackContent = extractFallbackContent();
    if (fallbackContent && fallbackContent.length > 100) {
      return {
        title: title,
        content: fallbackContent,
        url: url,
        excerpt: fallbackContent.slice(0, 200),
        byline: '',
      };
    }

    return null;
  }

  function extractReadableContent() {
    // 简化的 Readability 算法 — 基于 Mozilla Readability.js 核心逻辑
    // 1. 克隆文档，避免修改原页面
    const doc = document.cloneNode(true);

    // 2. 移除噪声元素
    const noiseSelectors = [
      'script', 'style', 'nav', 'header', 'footer', 'aside',
      '[class*="nav"]', '[class*="menu"]', '[class*="sidebar"]',
      '[class*="comment"]', '[class*="related"]', '[class*="recommend"]',
      '[class*="ad"]', '[id*="ad"]', '[class*="popup"]', '[class*="modal"]',
      '[class*="share"]', '[class*="social"]', '[class*="toolbar"]',
      'iframe', 'noscript', 'form', 'button',
    ];
    noiseSelectors.forEach(sel => {
      doc.querySelectorAll(sel).forEach(el => el.remove());
    });

    // 3. 评分算法 — 找到最佳内容容器
    const candidates = [];
    const paragraphs = doc.querySelectorAll('p, article, section, div');

    paragraphs.forEach(el => {
      const text = el.textContent || '';
      const textLength = text.trim().length;
      if (textLength < 100) return; // 太短跳过

      let score = 0;
      const tagName = el.tagName.toLowerCase();
      const className = (el.className || '').toLowerCase();
      const id = (el.id || '').toLowerCase();

      // 标签加分
      if (tagName === 'article') score += 25;
      if (tagName === 'section') score += 15;

      // 类名/ID 加分
      const positivePatterns = ['content', 'article', 'post', 'entry', 'main', 'body', 'text'];
      const negativePatterns = ['comment', 'meta', 'footer', 'sidebar', 'widget', 'header'];

      positivePatterns.forEach(p => {
        if (className.includes(p) || id.includes(p)) score += 10;
      });
      negativePatterns.forEach(p => {
        if (className.includes(p) || id.includes(p)) score -= 15;
      });

      // 文本密度加分（链接比例越低越好）
      const links = el.querySelectorAll('a');
      const linkText = Array.from(links).reduce((sum, a) => sum + (a.textContent || '').length, 0);
      const linkDensity = textLength > 0 ? linkText / textLength : 0;
      score += (1 - linkDensity) * 20;

      // 段落数量加分
      const pCount = el.querySelectorAll('p').length;
      score += pCount * 3;

      // 文本长度加分（但不过度）
      score += Math.min(textLength / 100, 50);

      candidates.push({ element: el, score, textLength });
    });

    if (candidates.length === 0) return null;

    // 4. 选择最高分候选
    candidates.sort((a, b) => b.score - a.score);
    const best = candidates[0];

    // 5. 提取内容并转为 Markdown
    const contentHtml = best.element.innerHTML;
    const markdown = htmlToMarkdown(contentHtml);

    // 6. 提取元信息
    const metaTitle = doc.querySelector('meta[property="og:title"]')?.content ||
                      doc.querySelector('meta[name="twitter:title"]')?.content ||
                      doc.title;
    const metaDesc = doc.querySelector('meta[property="og:description"]')?.content ||
                     doc.querySelector('meta[name="description"]')?.content ||
                     doc.querySelector('meta[name="twitter:description"]')?.content;
    const metaAuthor = doc.querySelector('meta[name="author"]')?.content ||
                       doc.querySelector('[class*="author"], [class*="byline"]')?.textContent;

    return {
      title: metaTitle || doc.title,
      content: markdown,
      excerpt: metaDesc || markdown.slice(0, 300),
      byline: metaAuthor || '',
    };
  }

  function htmlToMarkdown(html) {
    // 创建临时 DOM
    const tmp = document.createElement('div');
    tmp.innerHTML = html;

    // 处理代码块
    tmp.querySelectorAll('pre code').forEach(block => {
      const lang = block.className?.match(/language-(\w+)/)?.[1] || '';
      const code = block.textContent;
      block.parentElement.outerHTML = `\n\n\`\`\`${lang}\n${code}\n\`\`\`\n\n`;
    });

    // 处理行内代码
    tmp.querySelectorAll('code').forEach(code => {
      if (!code.closest('pre')) {
        code.outerHTML = `\`${code.textContent}\``;
      }
    });

    // 处理标题
    const headingMap = { 'H1': '# ', 'H2': '## ', 'H3': '### ', 'H4': '#### ', 'H5': '##### ', 'H6': '###### ' };
    tmp.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
      h.outerHTML = `\n\n${headingMap[h.tagName]}${h.textContent.trim()}\n\n`;
    });

    // 处理粗体/斜体
    tmp.querySelectorAll('strong, b').forEach(el => { el.outerHTML = `**${el.textContent}**`; });
    tmp.querySelectorAll('em, i').forEach(el => { el.outerHTML = `*${el.textContent}*`; });

    // 处理链接
    tmp.querySelectorAll('a').forEach(a => {
      const href = a.getAttribute('href');
      const text = a.textContent.trim();
      if (href && text) {
        a.outerHTML = `[${text}](${href})`;
      }
    });

    // 处理图片
    tmp.querySelectorAll('img').forEach(img => {
      const src = img.getAttribute('src');
      const alt = img.getAttribute('alt') || '';
      if (src) {
        // 转为绝对路径
        const absoluteSrc = src.startsWith('http') ? src : new URL(src, window.location.href).href;
        img.outerHTML = `![${alt}](${absoluteSrc})`;
      }
    });

    // 处理列表
    tmp.querySelectorAll('ul').forEach(ul => {
      const items = Array.from(ul.querySelectorAll(':scope > li')).map(li => `- ${li.textContent.trim()}`).join('\n');
      ul.outerHTML = `\n\n${items}\n\n`;
    });
    tmp.querySelectorAll('ol').forEach(ol => {
      const items = Array.from(ol.querySelectorAll(':scope > li')).map((li, i) => `${i + 1}. ${li.textContent.trim()}`).join('\n');
      ol.outerHTML = `\n\n${items}\n\n`;
    });

    // 处理引用
    tmp.querySelectorAll('blockquote').forEach(bq => {
      const text = bq.textContent.trim().split('\n').map(l => `> ${l}`).join('\n');
      bq.outerHTML = `\n\n${text}\n\n`;
    });

    // 处理段落
    tmp.querySelectorAll('p').forEach(p => {
      p.outerHTML = `\n\n${p.textContent.trim()}\n\n`;
    });

    // 处理换行
    tmp.querySelectorAll('br').forEach(br => { br.outerHTML = '\n'; });

    // 清理多余空白
    let text = tmp.textContent;
    text = text.replace(/\n{3,}/g, '\n\n');
    text = text.replace(/^\s+|\s+$/g, '');

    return text;
  }

  function extractFallbackContent() {
    // 当 Readability 风格提取失败时的兜底方案
    // 策略：找包含最多文本的 div
    const divs = document.querySelectorAll('div, article, main');
    let bestDiv = null;
    let bestScore = 0;

    divs.forEach(div => {
      const text = div.textContent || '';
      const length = text.trim().length;
      if (length < 500) return;

      const pCount = div.querySelectorAll('p').length;
      const score = length + pCount * 100;

      if (score > bestScore) {
        bestScore = score;
        bestDiv = div;
      }
    });

    if (bestDiv) {
      return htmlToMarkdown(bestDiv.innerHTML);
    }

    // 最后兜底：所有段落
    const allParagraphs = document.querySelectorAll('p');
    if (allParagraphs.length > 3) {
      return Array.from(allParagraphs).map(p => p.textContent.trim()).filter(t => t.length > 20).join('\n\n');
    }

    return '';
  }

  function getSelectedText() {
    const selection = window.getSelection();
    return selection ? selection.toString().trim() : '';
  }

  // ========== API 请求 ==========

  function isExtensionContextValid() {
    try {
      return chrome.runtime && !!chrome.runtime.id;
    } catch (e) {
      return false;
    }
  }

  async function apiRequest(path, method, body) {
    if (!isExtensionContextValid()) {
      throw new Error('扩展已更新，请刷新页面 (F5)');
    }
    return new Promise((resolve, reject) => {
      try {
        chrome.runtime.sendMessage({
          type: 'API_REQUEST',
          path,
          method,
          body,
        }, (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
            return;
          }
          if (!response) {
            reject(new Error('无响应，Service Worker 可能已终止'));
            return;
          }
          if (response.error) {
            reject(new Error(response.error));
            return;
          }
          resolve(response.data);
        });
      } catch (e) {
        reject(e);
      }
    });
  }

  // ========== 采集功能 ==========

  async function sendToBackend(content, title) {
    if (!content || content.length < 10) {
      throw new Error('内容太短');
    }
    return await apiRequest('/upload/text', 'POST', {
      title: title || `${adapter?.name || '网页'}内容 ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`,
      content: content,
      source: 'chrome_extension',
    });
  }

  // ========== UI 组件 ==========

  function showToast(message) {
    let toast = document.getElementById('study-hub-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'study-hub-toast';
      toast.style.cssText = `
        position: fixed; bottom: 100px; right: 24px; z-index: 99999;
        padding: 10px 18px; border-radius: 12px;
        background: rgba(30,30,40,0.95); color: #fff;
        font-size: 13px; font-family: -apple-system, sans-serif;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        transition: opacity 0.3s, transform 0.3s;
        opacity: 0; transform: translateY(10px);
        pointer-events: none;
      `;
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
    }, 3000);
  }

  // ========== 主按钮组 ==========

  function injectCaptureButton() {
    if (document.getElementById('study-hub-container')) return;

    const container = document.createElement('div');
    container.id = 'study-hub-container';
    container.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; z-index: 99999;
      display: flex; flex-direction: column; gap: 8px;
      align-items: flex-end;
    `;

    // ① 选中采集按钮
    const selectBtn = document.createElement('button');
    selectBtn.textContent = '📝 记住这段';
    selectBtn.style.cssText = getButtonStyle('#7c8aff');
    selectBtn.onmouseenter = () => { selectBtn.style.transform = 'scale(1.05)'; };
    selectBtn.onmouseleave = () => { selectBtn.style.transform = 'scale(1)'; };
    selectBtn.onclick = async () => {
      const selected = getSelectedText();
      if (!selected) {
        showToast('请先选中要保存的文字');
        return;
      }
      selectBtn.textContent = '保存中…';
      selectBtn.style.opacity = '0.7';
      try {
        const data = await sendToBackend(selected, '选中内容');
        if (data.id) {
          selectBtn.textContent = `✅ 已保存 (${data.char_count}字)`;
          selectBtn.style.background = '#4ec9a0';
          showToast(`已保存到学习中枢 (${data.char_count}字)`);
        } else {
          selectBtn.textContent = '❌ 保存失败';
          selectBtn.style.background = '#ff5c7a';
        }
      } catch (e) {
        selectBtn.textContent = '❌ ' + (e.message?.slice(0, 15) || '失败');
        selectBtn.style.background = '#ff5c7a';
      }
      setTimeout(() => {
        selectBtn.textContent = '📝 记住这段';
        selectBtn.style.background = '#7c8aff';
        selectBtn.style.opacity = '1';
      }, 3000);
    };

    // ② 自动采集按钮（如果有适配器）
    const autoBtn = document.createElement('button');
    autoBtn.textContent = '🧠 采集对话';
    autoBtn.style.cssText = getButtonStyle('#4ec9a0');
    autoBtn.onmouseenter = () => { autoBtn.style.transform = 'scale(1.05)'; };
    autoBtn.onmouseleave = () => { autoBtn.style.transform = 'scale(1)'; };
    autoBtn.onclick = async () => {
      const dialogue = extractCurrentDialogue();
      if (!dialogue) {
        showToast('未检测到对话内容，请使用"配置此网站"设置选择器');
        return;
      }
      autoBtn.textContent = '采集中…';
      autoBtn.style.opacity = '0.7';
      try {
        const data = await sendToBackend(dialogue, `${adapter?.name || '网页'}对话`);
        if (data.id) {
          autoBtn.textContent = `✅ 已采集 (${data.char_count}字)`;
          showToast(`已采集到学习中枢 (${data.char_count}字)`);
        } else {
          autoBtn.textContent = '❌ 采集失败';
          autoBtn.style.background = '#ff5c7a';
        }
      } catch (e) {
        autoBtn.textContent = '❌ ' + (e.message?.slice(0, 15) || '失败');
        autoBtn.style.background = '#ff5c7a';
      }
      setTimeout(() => {
        autoBtn.textContent = '🧠 采集对话';
        autoBtn.style.background = '#4ec9a0';
        autoBtn.style.opacity = '1';
      }, 3000);
    };

    // ③ 剪藏网页按钮（非 AI 对话网站显示）
    const clipBtn = document.createElement('button');
    clipBtn.textContent = '📄 剪藏网页';
    clipBtn.style.cssText = getButtonStyle('#ff9800');
    clipBtn.onmouseenter = () => { clipBtn.style.transform = 'scale(1.05)'; };
    clipBtn.onmouseleave = () => { clipBtn.style.transform = 'scale(1)'; };
    clipBtn.onclick = async () => {
      const article = extractArticle();
      if (!article) {
        showToast('❌ 未能提取到文章内容');
        return;
      }
      clipBtn.textContent = '保存中…';
      clipBtn.style.opacity = '0.7';
      try {
        const data = await sendToBackend(
          `# ${article.title}\n\n> 来源: [${article.title}](${article.url})\n> 作者: ${article.byline || '未知'}\n\n${article.content}`,
          article.title
        );
        if (data.id) {
          clipBtn.textContent = `✅ 已剪藏 (${data.char_count}字)`;
          showToast(`已剪藏到知识库 (${data.char_count}字)`);
        } else {
          clipBtn.textContent = '❌ 保存失败';
          clipBtn.style.background = '#ff5c7a';
        }
      } catch (e) {
        clipBtn.textContent = '❌ ' + (e.message?.slice(0, 15) || '失败');
        clipBtn.style.background = '#ff5c7a';
      }
      setTimeout(() => {
        clipBtn.textContent = '📄 剪藏网页';
        clipBtn.style.background = '#ff9800';
        clipBtn.style.opacity = '1';
      }, 3000);
    };

    // ④ 配置按钮
    const configBtn = document.createElement('button');
    configBtn.textContent = '⚙️ 配置此网站';
    configBtn.style.cssText = getButtonStyle('#666');
    configBtn.onmouseenter = () => { configBtn.style.transform = 'scale(1.05)'; };
    configBtn.onmouseleave = () => { configBtn.style.transform = 'scale(1)'; };
    configBtn.onclick = () => { startElementPicker(); };

    container.appendChild(selectBtn);
    container.appendChild(autoBtn);
    container.appendChild(clipBtn);
    container.appendChild(configBtn);
    document.body.appendChild(container);
  }

  function getButtonStyle(color) {
    return `
      padding: 10px 18px; border-radius: 20px; border: none;
      background: ${color}; color: #fff; font-size: 14px; font-weight: 600;
      cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      transition: transform 0.15s, opacity 0.15s;
      font-family: -apple-system, sans-serif;
      white-space: nowrap;
    `;
  }

  // ========== 可视化元素选择器 ==========

  function startElementPicker() {
    // 防止重复启动
    if (document.getElementById('study-hub-picker-overlay')) return;

    showToast('🖱️ 点击要采集的对话元素，按 ESC 取消');

    const overlay = document.createElement('div');
    overlay.id = 'study-hub-picker-overlay';
    overlay.style.cssText = `
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      z-index: 2147483647; cursor: crosshair;
      background: transparent;
    `;

    let highlighted = null;
    let highlightBox = null;

    // 创建高亮框
    function createHighlight() {
      if (highlightBox) return;
      highlightBox = document.createElement('div');
      highlightBox.style.cssText = `
        position: fixed; z-index: 9999999;
        border: 2px solid #7c8aff; border-radius: 4px;
        background: rgba(124,138,255,0.1);
        pointer-events: none;
        transition: all 0.1s;
      `;
      document.body.appendChild(highlightBox);
    }

    // 更新高亮位置
    function updateHighlight(element) {
      if (!highlightBox) createHighlight();
      const rect = element.getBoundingClientRect();
      highlightBox.style.left = rect.left + 'px';
      highlightBox.style.top = rect.top + 'px';
      highlightBox.style.width = rect.width + 'px';
      highlightBox.style.height = rect.height + 'px';
      highlightBox.style.display = 'block';
    }

    // 隐藏高亮
    function hideHighlight() {
      if (highlightBox) highlightBox.style.display = 'none';
    }

    // 生成选择器
    function generateSelector(element) {
      // 优先使用 class
      if (element.className && typeof element.className === 'string') {
        const classes = element.className.split(' ').filter(c => c.length > 0);
        if (classes.length > 0) {
          // 使用第一个有意义的 class
          const meaningful = classes.find(c => c.length > 3 && !c.includes(' '));
          if (meaningful) {
            return '.' + meaningful;
          }
        }
      }
      // 使用标签名 + 属性
      const tag = element.tagName.toLowerCase();
      if (element.id) return `#${element.id}`;
      // 使用父元素 + 子元素路径
      let path = tag;
      let parent = element.parentElement;
      while (parent && parent.tagName !== 'BODY') {
        const parentTag = parent.tagName.toLowerCase();
        if (parent.className && typeof parent.className === 'string') {
          const classes = parent.className.split(' ').filter(c => c.length > 0);
          if (classes.length > 0) {
            path = '.' + classes[0] + ' > ' + path;
            break;
          }
        }
        path = parentTag + ' > ' + path;
        parent = parent.parentElement;
        if (path.split('>').length > 4) break; // 限制路径长度
      }
      return path;
    }

    // 鼠标移动
    overlay.onmousemove = (e) => {
      // 临时隐藏 overlay 才能获取下面的元素
      overlay.style.display = 'none';
      const element = document.elementFromPoint(e.clientX, e.clientY);
      overlay.style.display = 'block';
      
      if (element && element !== overlay && element !== highlightBox && !element.closest('#study-hub-container')) {
        highlighted = element;
        updateHighlight(element);
      }
    };

    // 点击选择
    overlay.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (highlighted) {
        const selector = generateSelector(highlighted);
        // 测试选择器
        const matches = document.querySelectorAll(selector);
        if (matches.length === 0) {
          showToast('❌ 选择器无效，请重试');
          return;
        }
        // 保存
        saveCustomSelector(selector);
        // 清理
        cleanup();
        showToast(`✅ 已配置，匹配 ${matches.length} 个元素，刷新页面生效`);
      }
    };

    // ESC 取消
    function onKeyDown(e) {
      if (e.key === 'Escape') {
        cleanup();
        showToast('已取消配置');
      }
    }

    // 清理
    function cleanup() {
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      if (highlightBox && highlightBox.parentNode) highlightBox.parentNode.removeChild(highlightBox);
      document.removeEventListener('keydown', onKeyDown);
    }

    document.addEventListener('keydown', onKeyDown);
    document.body.appendChild(overlay);
  }

  // ========== 自动提取 ==========

  function getLastMessages(n) {
    const dialogue = extractCurrentDialogue();
    if (!dialogue) return [];
    const parts = dialogue.split('\n\n---\n\n');
    return parts.slice(-n);
  }

  function detectConversationEnd() {
    const idle = Date.now() - lastActivity;
    const lastMessages = getLastMessages(3);
    const hasEndSignal = lastMessages.some(m =>
      AUTO_EXTRACT_CONFIG.end_signals.some(s => m.includes(s))
    );
    return idle > AUTO_EXTRACT_CONFIG.idle_threshold || hasEndSignal;
  }

  function scan() {
    const current = extractCurrentDialogue();
    if (!current) return;
    if (current !== lastSnapshot) {
      const newContent = current.slice(lastSnapshot.length).trim();
      if (newContent) {
        try {
          chrome.storage.local.get([STORAGE_KEY], (data) => {
            if (chrome.runtime.lastError) return;
            const existing = data[STORAGE_KEY] || '';
            chrome.storage.local.set({ [STORAGE_KEY]: existing + '\n' + newContent });
          });
        } catch (e) {
          window.__study_hub_fallback = (window.__study_hub_fallback || '') + '\n' + newContent;
        }
      }
      lastSnapshot = current;
      lastActivity = Date.now();
      hasExtracted = false;
    }
    if (autoExtractEnabled && !hasExtracted && detectConversationEnd()) {
      const dialogue = extractCurrentDialogue();
      if (dialogue.length >= AUTO_EXTRACT_CONFIG.min_dialogue_length) {
        autoExtract(dialogue);
        hasExtracted = true;
      }
    }
  }

  async function autoExtract(dialogue) {
    try {
      const data = await apiRequest('/memory/summarize_and_extract', 'POST', {
        conversation: dialogue,
        source_tool: adapter?.name || 'unknown',
        source_ref: window.location.href,
      });
      if (data.added > 0) {
        showToast(`🧠 已提取 ${data.added} 条记忆`);
      }
    } catch (e) {
      console.error('[study-hub] 自动提取失败:', e);
    }
  }

  // ========== 抖音收藏采集 ==========

  function extractDouyinVideoLinks() {
    /** 从当前页面上提取所有抖音视频/图文链接。返回去重后的完整 URL 列表。 */
    const links = new Set();
    const host = 'https://www.douyin.com';

    // 策略1：查找所有 <a> 标签的 href 属性中包含 /video/ 或 /note/ 的链接
    const anchors = document.querySelectorAll('a[href*="/video/"], a[href*="/note/"]');
    anchors.forEach(a => {
      const href = a.getAttribute('href');
      if (!href) return;
      // 过滤掉非视频/图文页的链接（如 /video/ 可能是其他页面）
      const match = href.match(/\/(video|note)\/(\d+)/);
      if (match) {
        const fullUrl = href.startsWith('http') ? href : host + href;
        links.add(fullUrl);
      }
    });

    // 策略2：查找包含 video_id 或 aweme_id 的 data 属性
    const cards = document.querySelectorAll('[data-e2e="feed-active-item"], [data-e2e="user-like-item"], [data-e2e*="video"], [data-e2e*="item"]');
    cards.forEach(card => {
      // 在这些卡片内部搜索链接
      const innerLinks = card.querySelectorAll('a[href]');
      innerLinks.forEach(a => {
        const href = a.getAttribute('href');
        if (!href) return;
        const match = href.match(/\/(video|note)\/(\d+)/);
        if (match) {
          const fullUrl = href.startsWith('http') ? href : host + href;
          links.add(fullUrl);
        }
      });
    });

    // 策略3：扫描页面所有链接，匹配抖音视频/图文 URL 模式
    if (links.size === 0) {
      document.querySelectorAll('a[href]').forEach(a => {
        const href = a.getAttribute('href');
        if (!href) return;
        // 匹配 douyin.com/video/数字 或 douyin.com/note/数字
        if (/douyin\.com\/(video|note)\/\d+/.test(href)) {
          const fullUrl = href.startsWith('http') ? href : host + href;
          links.add(fullUrl);
        }
      });
    }

    // 策略4：从页面 HTML 源码中用正则提取（兜底）
    if (links.size === 0) {
      const html = document.documentElement.innerHTML;
      const regex = /(?:https?:)?\/\/(?:www\.)?douyin\.com\/(video|note)\/(\d+)/g;
      let m;
      while ((m = regex.exec(html)) !== null) {
        const fullUrl = m[0].startsWith('http') ? m[0] : 'https:' + m[0];
        links.add(fullUrl);
      }
    }

    return Array.from(links);
  }

  async function scrollAndCollectDouyinFavorites(maxScrolls = 30) {
    /** 滚动页面加载更多收藏内容，然后提取所有视频链接。
     *  maxScrolls: 最大滚动次数（默认30次，每次间隔1.5s）
     *  返回 { links: string[], scrolled: number, total: number }
     */
    let prevCount = 0;
    let noNewCount = 0;
    const maxNoNew = 5; // 连续5次没有新内容就停止

    for (let i = 0; i < maxScrolls; i++) {
      // 滚动到页面底部
      window.scrollTo(0, document.body.scrollHeight);
      // 等待内容加载
      await new Promise(r => setTimeout(r, 1500));

      const currentLinks = extractDouyinVideoLinks();
      if (currentLinks.length === prevCount) {
        noNewCount++;
        if (noNewCount >= maxNoNew) break; // 没有更多内容了
      } else {
        noNewCount = 0;
        prevCount = currentLinks.length;
      }
    }

    // 滚动回顶部
    window.scrollTo(0, 0);

    const allLinks = extractDouyinVideoLinks();
    return {
      links: allLinks,
      scrolled: Math.min(maxScrolls, prevCount > 0 ? Math.floor(prevCount / 10) + 1 : 0),
      total: allLinks.length,
    };
  }

  // ========== 消息监听 ==========

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'CLIP_PAGE') {
      const article = extractArticle();
      if (article) {
        sendResponse({
          success: true,
          title: article.title,
          content: `# ${article.title}\n\n> 来源: [${article.title}](${article.url})\n> 作者: ${article.byline || '未知'}\n\n${article.content}`,
          url: article.url,
          excerpt: article.excerpt,
        });
      } else {
        sendResponse({ success: false, error: '未能提取到文章内容' });
      }
      return true;
    }

    if (message.type === 'EXTRACT_DOUYIN_FAVORITES') {
      // 先快速提取当前可见链接
      const quickLinks = extractDouyinVideoLinks();
      sendResponse({ status: 'collecting', visible: quickLinks.length });

      // 然后滚动加载更多
      scrollAndCollectDouyinFavorites(message.maxScrolls || 30).then(result => {
        // 通过 runtime.sendMessage 发回结果
        chrome.runtime.sendMessage({
          type: 'DOUYIN_FAVORITES_RESULT',
          data: result,
        }).catch(() => {
          // popup 可能已关闭，忽略
        });
      }).catch(err => {
        chrome.runtime.sendMessage({
          type: 'DOUYIN_FAVORITES_RESULT',
          data: { links: [], scrolled: 0, total: 0, error: err.message },
        }).catch(() => {});
      });

      return true; // 保持消息通道开启以支持异步 sendResponse
    }

    if (message.type === 'GET_DOUYIN_LINKS_QUICK') {
      const links = extractDouyinVideoLinks();
      sendResponse({ links, total: links.length });
      return true;
    }
  });

  // ========== 启动 ==========

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
