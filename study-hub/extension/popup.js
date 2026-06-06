// Popup 控制逻辑 — 五层记忆系统 + 自定义网站配置 + 抖音收藏导入
// 所有请求通过 background.js 代理，绕过 CORS

const STORAGE_KEY = 'study_hub_api_base';
const AUTO_EXTRACT_KEY = 'study_hub_auto_extract';
const CUSTOM_ADAPTERS_KEY = 'study_hub_custom_adapters';
const CUSTOM_SELECTORS_KEY = 'study_hub_custom_selectors';

document.addEventListener('DOMContentLoaded', () => {
  const apiBaseInput = document.getElementById('apiBase');
  const saveBtn = document.getElementById('saveBtn');
  const captureBtn = document.getElementById('captureBtn');
  const rememberBtn = document.getElementById('rememberBtn');
  const autoToggle = document.getElementById('autoToggle');
  const statusEl = document.getElementById('status');
  const layerStats = document.getElementById('layerStats');

  // 抖音收藏相关
  const douyinSection = document.getElementById('douyinSection');
  const douyinFavBtn = document.getElementById('douyinFavBtn');
  const douyinStatus = document.getElementById('douyinStatus');
  const douyinLinkList = document.getElementById('douyinLinkList');

  // 检测当前页面是否为抖音，显示/隐藏导入按钮
  checkDouyinPage();

  // 标签页切换
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
    });
  });

  // 加载配置
  chrome.storage.sync.get([STORAGE_KEY, AUTO_EXTRACT_KEY], (data) => {
    apiBaseInput.value = data[STORAGE_KEY] || 'http://localhost:8741';
    const autoEnabled = data[AUTO_EXTRACT_KEY] !== false;
    autoToggle.classList.toggle('active', autoEnabled);
  });

  loadMemoryStats();
  loadSiteList();
  loadCustomSelectors();

  // 保存配置
  saveBtn.addEventListener('click', () => {
    const url = apiBaseInput.value.trim().replace(/\/+$/, '');
    chrome.storage.sync.set({ [STORAGE_KEY]: url }, () => {
      statusEl.textContent = '配置已保存';
      setTimeout(() => { statusEl.textContent = ''; }, 2000);
    });
  });

  // 自动提取开关
  autoToggle.addEventListener('click', () => {
    const isActive = autoToggle.classList.contains('active');
    const newState = !isActive;
    autoToggle.classList.toggle('active', newState);
    chrome.storage.sync.set({ [AUTO_EXTRACT_KEY]: newState }, () => {
      statusEl.textContent = newState ? '自动提取已开启' : '自动提取已关闭';
      setTimeout(() => { statusEl.textContent = ''; }, 2000);
    });
  });

  // 🧠 提取这段对话
  rememberBtn.addEventListener('click', async () => {
    statusEl.textContent = '正在提取记忆…';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        statusEl.textContent = '未找到活跃标签页';
        return;
      }
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: extractDialogueFromPage,
      });
      const result = results[0]?.result;
      if (result?.error) {
        statusEl.textContent = result.error;
        return;
      }
      if (!result?.text) {
        statusEl.textContent = '未采集到对话内容';
        return;
      }
      const data = await apiRequest('/memory/summarize_and_extract', 'POST', {
        conversation: result.text,
        source_tool: result.source || 'chrome_extension',
        source_ref: tab.url,
      });
      if (data.added !== undefined) {
        const layers = data.added_by_layer || {};
        statusEl.innerHTML = `🧠 提取完成：角色${layers.role || 0} 项目${layers.project || 0} 工作流${layers.workflow || 0} 会话${layers.session || 0}`;
        loadMemoryStats();
      } else {
        statusEl.textContent = '提取失败: ' + (data.error || '未知错误');
      }
    } catch (err) {
      statusEl.textContent = '提取失败: ' + err.message;
    }
  });

  // 采集到知识库（AI 对话）
  captureBtn.addEventListener('click', async () => {
    statusEl.textContent = '正在采集…';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        statusEl.textContent = '未找到活跃标签页';
        return;
      }
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: extractDialogueFromPage,
      });
      const result = results[0]?.result;
      if (result?.error) {
        statusEl.textContent = result.error;
        return;
      }
      if (!result?.text) {
        statusEl.textContent = '未采集到对话内容';
        return;
      }
      const data = await apiRequest('/upload/text', 'POST', {
        title: `${result.source || 'AI'}对话 ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`,
        content: result.text,
        source: 'ai_dialogue',
      });
      if (data.id) {
        statusEl.textContent = `已采集 (${data.char_count} 字)`;
      } else {
        statusEl.textContent = '采集失败: ' + (data.error || '未知错误');
      }
    } catch (err) {
      statusEl.textContent = '采集失败: ' + err.message;
    }
  });

  // 剪藏当前网页（文章模式）
  const clipPageBtn = document.getElementById('clipPageBtn');
  clipPageBtn.addEventListener('click', async () => {
    statusEl.textContent = '正在提取网页内容…';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        statusEl.textContent = '未找到活跃标签页';
        return;
      }

      // 向 content script 发送剪藏请求
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'CLIP_PAGE' });
      if (!response || !response.success) {
        statusEl.textContent = '❌ ' + (response?.error || '提取失败');
        return;
      }

      statusEl.textContent = '正在保存…';
      const data = await apiRequest('/upload/text', 'POST', {
        title: response.title || `网页剪藏 ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`,
        content: response.content,
        source: 'web_clipper',
        source_url: response.url,
      });

      if (data.id) {
        statusEl.textContent = `✅ 已剪藏 (${data.char_count} 字)`;
      } else {
        statusEl.textContent = '保存失败: ' + (data.error || '未知错误');
      }
    } catch (err) {
      if (err.message && err.message.includes('Receiving end does not exist')) {
        statusEl.textContent = '⚠️ 请刷新页面后再试';
      } else {
        statusEl.textContent = '❌ ' + err.message;
      }
    }
  });

  // 添加新网站
  document.getElementById('addSiteBtn').addEventListener('click', async () => {
    const host = document.getElementById('newSiteHost').value.trim();
    const name = document.getElementById('newSiteName').value.trim();
    const selector = document.getElementById('newSiteSelector').value.trim();

    if (!host || !name || !selector) {
      statusEl.textContent = '请填写完整信息';
      return;
    }

    const config = {
      name: name,
      selectors: { container: selector },
      extract: 'element.textContent.trim()',
    };

    chrome.storage.sync.get([CUSTOM_ADAPTERS_KEY], (data) => {
      const custom = data[CUSTOM_ADAPTERS_KEY] || {};
      custom[host] = config;
      chrome.storage.sync.set({ [CUSTOM_ADAPTERS_KEY]: custom }, () => {
        statusEl.textContent = `已添加 ${name}`;
        document.getElementById('newSiteHost').value = '';
        document.getElementById('newSiteName').value = '';
        document.getElementById('newSiteSelector').value = '';
        loadSiteList();
        setTimeout(() => { statusEl.textContent = ''; }, 2000);
      });
    });
  });

  async function loadMemoryStats() {
    try {
      const layers = ['role', 'project', 'workflow', 'session'];
      const counts = {};
      for (const layer of layers) {
        const data = await apiRequest(`/memory/list?layer=${layer}&limit=1`, 'GET');
        counts[layer] = data.total || 0;
      }
      layerStats.innerHTML = `
        <span class="layer-stat role">角色 ${counts.role}</span>
        <span class="layer-stat project">项目 ${counts.project}</span>
        <span class="layer-stat workflow">工作流 ${counts.workflow}</span>
        <span class="layer-stat session">会话 ${counts.session}</span>
      `;
    } catch {
      // 静默失败
    }
  }

  function loadCustomSelectors() {
    const selectorList = document.getElementById('selectorList');
    if (!selectorList) return;
    
    chrome.storage.sync.get([CUSTOM_SELECTORS_KEY], (data) => {
      const selectors = data[CUSTOM_SELECTORS_KEY] || {};
      const items = Object.entries(selectors);
      
      if (items.length === 0) {
        selectorList.innerHTML = '<div style="color: #888; font-size: 13px;">暂无自定义选择器，在网页上点击"配置此网站"添加</div>';
        return;
      }
      
      selectorList.innerHTML = items.map(([host, selector]) => `
        <div class="site-item">
          <div>
            <div class="name">${host}</div>
            <div class="host" style="font-size: 11px; color: #888;">${selector}</div>
          </div>
          <span class="delete" data-host="${host}" data-type="selector">×</span>
        </div>
      `).join('');
      
      selectorList.querySelectorAll('.delete').forEach(btn => {
        btn.addEventListener('click', () => {
          const host = btn.dataset.host;
          chrome.storage.sync.get([CUSTOM_SELECTORS_KEY], (data) => {
            const selectors = data[CUSTOM_SELECTORS_KEY] || {};
            delete selectors[host];
            chrome.storage.sync.set({ [CUSTOM_SELECTORS_KEY]: selectors }, () => {
              loadCustomSelectors();
              statusEl.textContent = '已删除';
              setTimeout(() => { statusEl.textContent = ''; }, 1500);
            });
          });
        });
      });
    });
  }

  function loadSiteList() {
    const siteList = document.getElementById('siteList');
    const builtinSites = [
      { host: 'claude.ai', name: 'Claude', builtin: true },
      { host: 'chat.openai.com', name: 'ChatGPT', builtin: true },
      { host: 'chat.deepseek.com', name: 'DeepSeek', builtin: true },
      { host: 'kimi.moonshot.cn', name: 'Kimi', builtin: true },
      { host: 'kimi.com', name: 'Kimi', builtin: true },
      { host: 'www.doubao.com', name: '豆包', builtin: true },
    ];

    chrome.storage.sync.get([CUSTOM_ADAPTERS_KEY], (data) => {
      const custom = data[CUSTOM_ADAPTERS_KEY] || {};
      const customSites = Object.entries(custom).map(([host, config]) => ({
        host,
        name: config.name,
        builtin: false,
      }));

      const allSites = [...builtinSites, ...customSites];

      siteList.innerHTML = allSites.map(site => `
        <div class="site-item">
          <div>
            <div class="name">${site.name}</div>
            <div class="host">${site.host}</div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="badge ${site.builtin ? 'builtin' : 'custom'}">${site.builtin ? '内置' : '自定义'}</span>
            ${!site.builtin ? `<span class="delete" data-host="${site.host}">×</span>` : ''}
          </div>
        </div>
      `).join('');

      siteList.querySelectorAll('.delete').forEach(btn => {
        btn.addEventListener('click', () => {
          const host = btn.dataset.host;
          chrome.storage.sync.get([CUSTOM_ADAPTERS_KEY], (data) => {
            const custom = data[CUSTOM_ADAPTERS_KEY] || {};
            delete custom[host];
            chrome.storage.sync.set({ [CUSTOM_ADAPTERS_KEY]: custom }, () => {
              loadSiteList();
              statusEl.textContent = '已删除';
              setTimeout(() => { statusEl.textContent = ''; }, 1500);
            });
          });
        });
      });
    });
  }

  // ========== 抖音收藏导入 ==========

  async function checkDouyinPage() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.url && tab.url.includes('douyin.com')) {
        douyinSection.style.display = 'block';
      }
    } catch {
      // 静默失败
    }
  }

  // 自包含的抖音链接采集函数 — 通过 chrome.scripting.executeScript 注入页面
  // 注意：此函数被序列化后注入到目标页面运行，不能引用外部变量
  function collectDouyinLinks(maxScrolls, maxNoNew) {
    function extractLinks() {
      const links = new Set();
      const host = 'https://www.douyin.com';

      // 策略1：<a> 标签
      document.querySelectorAll('a[href*="/video/"], a[href*="/note/"]').forEach(a => {
        const href = a.getAttribute('href');
        if (!href) return;
        const m = href.match(/\/(video|note)\/(\d+)/);
        if (m) links.add(href.startsWith('http') ? href : host + href);
      });

      // 策略2：data-e2e 卡片
      document.querySelectorAll('[data-e2e="feed-active-item"], [data-e2e="user-like-item"], [data-e2e*="video"], [data-e2e*="item"]').forEach(card => {
        card.querySelectorAll('a[href]').forEach(a => {
          const href = a.getAttribute('href');
          if (!href) return;
          const m = href.match(/\/(video|note)\/(\d+)/);
          if (m) links.add(href.startsWith('http') ? href : host + href);
        });
      });

      // 策略3：全页扫描
      if (links.size === 0) {
        document.querySelectorAll('a[href]').forEach(a => {
          const href = a.getAttribute('href');
          if (href && /douyin\.com\/(video|note)\/\d+/.test(href)) {
            links.add(href.startsWith('http') ? href : host + href);
          }
        });
      }

      // 策略4：HTML 正则兜底
      if (links.size === 0) {
        const html = document.documentElement.innerHTML;
        const regex = /(?:https?:)?\/\/(?:www\.)?douyin\.com\/(video|note)\/(\d+)/g;
        let m;
        while ((m = regex.exec(html)) !== null) {
          links.add(m[0].startsWith('http') ? m[0] : 'https:' + m[0]);
        }
      }

      return Array.from(links);
    }

    async function scrollAndCollect() {
      let prevCount = 0;
      let noNewCount = 0;

      for (let i = 0; i < maxScrolls; i++) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 1500));

        const current = extractLinks();
        if (current.length === prevCount) {
          noNewCount++;
          if (noNewCount >= maxNoNew) break;
        } else {
          noNewCount = 0;
          prevCount = current.length;
        }
      }

      window.scrollTo(0, 0);
      const allLinks = extractLinks();
      return { links: allLinks, scrolled: Math.min(maxScrolls, prevCount > 0 ? Math.floor(prevCount / 10) + 1 : 0), total: allLinks.length };
    }

    return scrollAndCollect();
  }

  function handleDouyinResult(data) {
    if (data.error) {
      douyinStatus.textContent = '❌ 采集失败：' + data.error;
      douyinFavBtn.disabled = false;
      douyinFavBtn.textContent = '🔄 采集当前页收藏';
      return;
    }

    const { links, total } = data;
    if (total === 0) {
      douyinStatus.textContent = '⚠️ 未检测到视频链接，请确认你在抖音收藏页面';
      douyinFavBtn.disabled = false;
      douyinFavBtn.textContent = '🔄 采集当前页收藏';
      return;
    }

    // 显示链接列表
    douyinLinkList.style.display = 'block';
    douyinLinkList.innerHTML = links.slice(0, 20).map((url, i) =>
      `<div style="padding: 2px 0; border-bottom: 1px solid #2a2a3a;">${i + 1}. <a href="${url}" target="_blank" style="color: #7c8aff;">${url.split('/').pop()}</a></div>`
    ).join('') + (links.length > 20 ? `<div style="color: #888; padding: 4px 0;">...还有 ${links.length - 20} 条</div>` : '');

    douyinStatus.textContent = `✅ 采集到 ${total} 条链接，正在提交解析队列…`;

    // 提交到后端队列
    submitDouyinLinks(links);
  }

  async function submitDouyinLinks(links) {
    try {
      const data = await apiRequest('/automation/queue', 'POST', {
        module_id: 'douyin-summary',
        inputs: links,
      });
      if (data.status === 'queued') {
        douyinStatus.textContent = `✅ 成功！${data.count} 个视频已加入解析队列，去前端页面查看进度`;
      } else if (data.error) {
        douyinStatus.textContent = '❌ ' + data.error;
      } else {
        douyinStatus.textContent = '✅ 已提交';
      }
    } catch (err) {
      douyinStatus.textContent = '❌ 提交失败：' + err.message;
    } finally {
      douyinFavBtn.disabled = false;
      douyinFavBtn.textContent = '🔄 采集当前页收藏';
    }
  }

  // 抖音采集按钮 — 使用 scripting.executeScript 注入采集脚本，不依赖 content script 版本
  douyinFavBtn.addEventListener('click', async () => {
    douyinFavBtn.disabled = true;
    douyinFavBtn.textContent = '⏳ 采集中…';
    douyinStatus.textContent = '正在捕获链接…';
    douyinLinkList.style.display = 'none';
    douyinLinkList.innerHTML = '';

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        douyinStatus.textContent = '❌ 找不到当前标签页';
        douyinFavBtn.disabled = false;
        douyinFavBtn.textContent = '🔄 采集当前页收藏';
        return;
      }

      // 注入采集脚本（直接在页面 isolated world 中运行，不依赖 content script）
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        world: 'ISOLATED',
        func: collectDouyinLinks,
        args: [30, 5], // maxScrolls=30, maxNoNew=5
      });

      if (results && results[0] && results[0].result) {
        handleDouyinResult(results[0].result);
      } else {
        douyinStatus.textContent = '⚠️ 采集完成但无结果，请确认你在抖音收藏页面';
        douyinFavBtn.disabled = false;
        douyinFavBtn.textContent = '🔄 采集当前页收藏';
      }
    } catch (err) {
      if (err.message && (err.message.includes('Extension context') || err.message.includes('Cannot access'))) {
        douyinStatus.textContent = '⚠️ 请刷新抖音页面后再试（扩展刚更新过，页面需要刷新）';
      } else {
        douyinStatus.textContent = '❌ ' + (err.message || '未知错误');
      }
      douyinFavBtn.disabled = false;
      douyinFavBtn.textContent = '🔄 采集当前页收藏';
    }
  });
});

// 通过 background.js 代理请求
function apiRequest(path, method, body) {
  return new Promise((resolve, reject) => {
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
      if (response.error) {
        reject(new Error(response.error));
        return;
      }
      resolve(response.data);
    });
  });
}

// 在页面上下文中执行的函数
function extractDialogueFromPage() {
  const hostname = window.location.hostname;
  
  const adapters = {
    'claude.ai': { name: 'Claude', selectors: { container: '[data-testid="user-message"], [data-testid="assistant-message"], .font-user-message, .font-assistant-message', fallback: '.prose, [class*="message"]' } },
    'chat.openai.com': { name: 'ChatGPT', selectors: { container: '[data-message-author-role="user"], [data-message-author-role="assistant"]' } },
    'chat.deepseek.com': { name: 'DeepSeek', selectors: { container: '[class*="message"], .chat-message' } },
    'kimi.moonshot.cn': { name: 'Kimi', selectors: { container: '[class*="message"], [class*="chat-item"], [class*="bubble"]' } },
    'kimi.com': { name: 'Kimi', selectors: { container: '[class*="message"], [class*="chat-item"], [class*="bubble"]' } },
    'www.doubao.com': { name: '豆包', selectors: { container: '[class*="message"], [class*="chat"]' } },
  };

  let adapter = null;
  for (const [key, a] of Object.entries(adapters)) {
    if (hostname.includes(key)) { adapter = a; break; }
  }

  if (!adapter) {
    const genericSelectors = ['[class*="message"]', '[class*="chat"]', '[class*="bubble"]', '[data-testid*="message"]'];
    for (const sel of genericSelectors) {
      const els = document.querySelectorAll(sel);
      if (els.length >= 2) {
        adapter = { name: 'Unknown', selectors: { container: sel } };
        break;
      }
    }
  }

  if (!adapter) {
    return { error: '当前页面不是支持的 AI 网站，请在扩展设置中添加此网站' };
  }

  const selector = adapter.selectors.container;
  const elements = document.querySelectorAll(selector);
  const texts = [];
  elements.forEach(el => { const t = el.textContent?.trim(); if (t) texts.push(t); });
  
  return {
    text: texts.join('\n\n---\n\n'),
    source: adapter.name,
    elementCount: elements.length,
  };
}
