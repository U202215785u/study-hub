// 对话提取 content script — 五层记忆系统自动收集
// 通过 background.js 代理请求，绕过 CORS

(function () {
  'use strict';
  
  const STORAGE_KEY = 'study_hub_dialogues';
  const AUTO_EXTRACT_KEY = 'study_hub_auto_extract';
  const INTERVAL_MS = 30000;

  let adapter = null;
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

  // 检查扩展是否可用
  function checkExtensionAvailable() {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage({ type: 'PING' }, (response) => {
          if (chrome.runtime.lastError) {
            console.log('[study-hub] 扩展不可用:', chrome.runtime.lastError.message);
            resolve(false);
          } else {
            resolve(true);
          }
        });
      } catch (e) {
        console.log('[study-hub] 扩展检查失败:', e);
        resolve(false);
      }
    });
  }

  async function init() {
    if (isInitialized) return;
    isInitialized = true;
    
    console.log('[study-hub] content script 初始化, hostname:', window.location.hostname);
    
    // 检查扩展是否可用
    const available = await checkExtensionAvailable();
    if (!available) {
      console.log('[study-hub] 扩展不可用，显示降级模式');
      showFallbackUI();
      return;
    }
    
    // 获取适配器
    adapter = getAdapterSync();
    if (!adapter) {
      adapter = await getAdapter();
    }
    
    if (!adapter) {
      console.log('[study-hub] 当前页面未配置:', window.location.hostname);
      injectConfigButton();
      return;
    }

    console.log('[study-hub] 使用适配器:', adapter.name);

    // 加载设置
    chrome.storage.sync.get([AUTO_EXTRACT_KEY], (data) => {
      if (data[AUTO_EXTRACT_KEY] !== undefined) {
        autoExtractEnabled = data[AUTO_EXTRACT_KEY];
      }
    });

    // 启动扫描
    setTimeout(() => {
      scan();
      injectCaptureButton();
    }, 3000);

    setInterval(scan, INTERVAL_MS);
    window.addEventListener('beforeunload', () => scan());

    // 监听用户活动
    document.addEventListener('input', () => { lastActivity = Date.now(); });
    document.addEventListener('click', () => { lastActivity = Date.now(); });
    document.addEventListener('keydown', () => { lastActivity = Date.now(); });
  }

  // 降级模式：扩展不可用时显示提示
  function showFallbackUI() {
    const div = document.createElement('div');
    div.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; z-index: 99999;
      padding: 12px 16px; border-radius: 12px;
      background: #ff9800; color: #fff; font-size: 13px;
      font-family: -apple-system, sans-serif; cursor: pointer;
      box-shadow: 0 4px 16px rgba(255,152,0,0.4);
    `;
    div.textContent = '⚠️ 扩展未激活，请刷新扩展';
    div.onclick = () => {
      alert('请按以下步骤操作：\n1. 打开 chrome://extensions/\n2. 找到"学习中枢"扩展\n3. 点击刷新按钮\n4. 刷新当前页面');
    };
    document.body.appendChild(div);
  }

  function extractCurrentDialogue() {
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

  function getLastMessages(n) {
    if (!adapter || !adapter.selectors) return [];
    const elements = document.querySelectorAll(adapter.selectors.container);
    const texts = [];
    const arr = Array.from(elements);
    const lastN = arr.slice(-n);
    lastN.forEach(el => {
      const text = adapter.extract ? adapter.extract(el) : el.textContent.trim();
      if (text) texts.push(text);
    });
    return texts;
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
        chrome.storage.session.get([STORAGE_KEY], (data) => {
          const existing = data[STORAGE_KEY] || '';
          chrome.storage.session.set({ [STORAGE_KEY]: existing + '\n' + newContent });
        });
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

  // 通过 background.js 代理请求
  async function apiRequest(path, method, body) {
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

  function injectConfigButton() {
    if (document.getElementById('study-hub-config-btn')) return;
    const btn = document.createElement('button');
    btn.id = 'study-hub-config-btn';
    btn.textContent = '⚙️ 配置此网站';
    btn.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; z-index: 99999;
      padding: 10px 18px; border-radius: 20px; border: none;
      background: #ff9800; color: #fff; font-size: 14px; font-weight: 600;
      cursor: pointer; box-shadow: 0 4px 16px rgba(255,152,0,0.4);
      transition: transform 0.15s, opacity 0.15s;
    `;
    btn.onmouseenter = () => { btn.style.transform = 'scale(1.05)'; };
    btn.onmouseleave = () => { btn.style.transform = 'scale(1)'; };
    btn.onclick = () => { openSiteConfigModal(); };
    document.body.appendChild(btn);
  }

  function openSiteConfigModal() {
    const existing = document.getElementById('study-hub-config-modal');
    if (existing) existing.remove();

    const candidates = detectChatElements();
    const modal = document.createElement('div');
    modal.id = 'study-hub-config-modal';
    modal.style.cssText = `
      position: fixed; inset: 0; z-index: 100000;
      background: rgba(0,0,0,0.7);
      display: flex; align-items: center; justify-content: center;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    `;

    const card = document.createElement('div');
    card.style.cssText = `
      background: #1a1a24; border: 1px solid #333; border-radius: 16px;
      width: 90%; max-width: 520px; max-height: 80vh;
      overflow-y: auto; padding: 24px; color: #e0e0e8;
    `;

    const hostname = window.location.hostname;
    
    let candidatesHtml = '';
    if (candidates.length > 0) {
      candidatesHtml = `
        <div style="margin: 16px 0;">
          <div style="font-size: 13px; color: #888; margin-bottom: 8px;">检测到的对话元素（点击选择）：</div>
          ${candidates.map((c, i) => `
            <div class="sh-candidate" data-selector="${c.selector}" style="
              padding: 10px 12px; margin-bottom: 8px; border-radius: 8px;
              background: #252532; border: 1px solid #333; cursor: pointer;
              transition: all 0.2s;
            " onmouseover="this.style.borderColor='#7c8aff'" onmouseout="this.style.borderColor='#333'">
              <div style="font-size: 13px; font-weight: 600; color: #7c8aff;">${c.selector}</div>
              <div style="font-size: 12px; color: #888; margin-top: 4px;">
                找到 ${c.count} 个元素 | 平均长度 ${c.avgLength} 字
              </div>
              <div style="font-size: 11px; color: #666; margin-top: 2px; font-style: italic;">
                ${c.sample}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h3 style="margin: 0; font-size: 16px;">⚙️ 配置新网站</h3>
        <button id="sh-close-modal" style="background: none; border: none; color: #888; font-size: 20px; cursor: pointer;">×</button>
      </div>
      <div style="font-size: 13px; color: #888; margin-bottom: 12px;">
        当前网站: <span style="color: #7c8aff;">${hostname}</span>
      </div>
      <div style="margin-bottom: 12px;">
        <label style="display: block; font-size: 12px; color: #888; margin-bottom: 4px;">网站名称</label>
        <input id="sh-site-name" type="text" value="${hostname.split('.')[0]}" style="
          width: 100%; padding: 8px 12px; background: #0f0f14; border: 1px solid #333;
          border-radius: 8px; color: #e0e0e8; font-size: 13px; outline: none;
        ">
      </div>
      <div style="margin-bottom: 12px;">
        <label style="display: block; font-size: 12px; color: #888; margin-bottom: 4px;">对话元素选择器（CSS Selector）</label>
        <input id="sh-selector" type="text" placeholder="例如: [class*=\"message\"]" style="
          width: 100%; padding: 8px 12px; background: #0f0f14; border: 1px solid #333;
          border-radius: 8px; color: #e0e0e8; font-size: 13px; outline: none;
        ">
      </div>
      ${candidatesHtml}
      <div style="margin-top: 16px; display: flex; gap: 8px;">
        <button id="sh-test-selector" style="
          flex: 1; padding: 10px; border-radius: 8px; border: 1px solid #333;
          background: #252532; color: #e0e0e8; font-size: 13px; cursor: pointer;
        ">🧪 测试选择器</button>
        <button id="sh-save-config" style="
          flex: 1; padding: 10px; border-radius: 8px; border: none;
          background: #7c8aff; color: #fff; font-size: 13px; cursor: pointer;
        ">💾 保存配置</button>
      </div>
      <div id="sh-test-result" style="margin-top: 12px; font-size: 12px;"></div>
    `;

    modal.appendChild(card);
    document.body.appendChild(modal);

    document.getElementById('sh-close-modal').onclick = () => modal.remove();
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };

    card.querySelectorAll('.sh-candidate').forEach(el => {
      el.onclick = () => {
        document.getElementById('sh-selector').value = el.dataset.selector;
        card.querySelectorAll('.sh-candidate').forEach(c => {
          c.style.borderColor = '#333';
          c.style.background = '#252532';
        });
        el.style.borderColor = '#4ec9a0';
        el.style.background = 'rgba(78,201,160,0.1)';
      };
    });

    document.getElementById('sh-test-selector').onclick = () => {
      const selector = document.getElementById('sh-selector').value.trim();
      const result = testSelector(selector);
      const resultEl = document.getElementById('sh-test-result');
      if (result.valid) {
        resultEl.innerHTML = `<span style="color: #4ec9a0;">✅ 找到 ${result.count} 个元素，总长度 ${result.totalLength} 字</span>
          <div style="color: #888; margin-top: 4px;">示例: ${result.texts[0]?.slice(0, 60)}...</div>`;
      } else {
        resultEl.innerHTML = `<span style="color: #ff5c7a;">❌ ${result.error || '未找到元素'}</span>`;
      }
    };

    document.getElementById('sh-save-config').onclick = async () => {
      const name = document.getElementById('sh-site-name').value.trim();
      const selector = document.getElementById('sh-selector').value.trim();
      if (!name || !selector) {
        alert('请填写网站名称和选择器');
        return;
      }
      const config = {
        name: name,
        selectors: { container: selector },
        extract: 'element.textContent.trim()',
      };
      await saveCustomAdapter(hostname, config);
      adapter = await getAdapter();
      modal.remove();
      const configBtn = document.getElementById('study-hub-config-btn');
      if (configBtn) configBtn.remove();
      injectCaptureButton();
      showToast(`✅ 已保存 ${name} 的配置`);
    };
  }

  function injectCaptureButton() {
    if (document.getElementById('study-hub-capture-btn')) return;
    const container = document.createElement('div');
    container.id = 'study-hub-capture-btn';
    container.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; z-index: 99999;
      display: flex; flex-direction: column; gap: 8px;
      font-family: -apple-system, sans-serif;
    `;

    const autoToggle = document.createElement('button');
    autoToggle.id = 'study-hub-auto-toggle';
    autoToggle.style.cssText = `
      padding: 6px 12px; border-radius: 14px; border: none;
      background: ${autoExtractEnabled ? '#4ec9a0' : '#666'};
      color: #fff; font-size: 11px; font-weight: 600;
      cursor: pointer; opacity: 0.8;
      transition: all 0.2s;
    `;
    autoToggle.textContent = autoExtractEnabled ? '🤖 自动提取开启' : '🤖 自动提取关闭';
    autoToggle.onclick = () => {
      autoExtractEnabled = !autoExtractEnabled;
      chrome.storage.sync.set({ [AUTO_EXTRACT_KEY]: autoExtractEnabled });
      autoToggle.textContent = autoExtractEnabled ? '🤖 自动提取开启' : '🤖 自动提取关闭';
      autoToggle.style.background = autoExtractEnabled ? '#4ec9a0' : '#666';
    };

    const rememberBtn = document.createElement('button');
    rememberBtn.textContent = '🧠 记住这段';
    rememberBtn.style.cssText = `
      padding: 10px 18px; border-radius: 20px; border: none;
      background: #4ec9a0; color: #fff; font-size: 14px; font-weight: 600;
      cursor: pointer; box-shadow: 0 4px 16px rgba(78,201,160,0.4);
      transition: transform 0.15s, opacity 0.15s;
    `;
    rememberBtn.onmouseenter = () => { rememberBtn.style.transform = 'scale(1.05)'; };
    rememberBtn.onmouseleave = () => { rememberBtn.style.transform = 'scale(1)'; };
    rememberBtn.onclick = async () => {
      const dialogue = extractCurrentDialogue();
      if (!dialogue) {
        rememberBtn.textContent = '未检测到对话';
        setTimeout(() => { rememberBtn.textContent = '🧠 记住这段'; }, 2000);
        return;
      }
      rememberBtn.textContent = '提取中…';
      rememberBtn.style.opacity = '0.7';
      try {
        const data = await apiRequest('/memory/summarize_and_extract', 'POST', {
          conversation: dialogue,
          source_tool: adapter?.name || 'chrome_extension',
          source_ref: window.location.href,
        });
        if (data.added !== undefined) {
          const layers = data.added_by_layer || {};
          rememberBtn.textContent = `🧠 +${data.added} 条`;
          showToast(`已提取: 角色${layers.role || 0} 项目${layers.project || 0} 工作流${layers.workflow || 0} 会话${layers.session || 0}`);
        } else {
          rememberBtn.textContent = '提取失败';
          rememberBtn.style.background = '#ff5c7a';
        }
      } catch (e) {
        console.error('[study-hub] 提取失败:', e);
        rememberBtn.textContent = '连接失败';
        rememberBtn.style.background = '#ff5c7a';
      }
      setTimeout(() => {
        rememberBtn.textContent = '🧠 记住这段';
        rememberBtn.style.background = '#4ec9a0';
        rememberBtn.style.opacity = '1';
      }, 3000);
    };

    const btn = document.createElement('button');
    btn.textContent = '采集到学习中枢';
    btn.style.cssText = `
      padding: 10px 18px; border-radius: 20px; border: none;
      background: #7c8aff; color: #fff; font-size: 14px; font-weight: 600;
      cursor: pointer; box-shadow: 0 4px 16px rgba(124,138,255,0.4);
      transition: transform 0.15s, opacity 0.15s;
    `;
    btn.onmouseenter = () => { btn.style.transform = 'scale(1.05)'; };
    btn.onmouseleave = () => { btn.style.transform = 'scale(1)'; };
    btn.onclick = async () => {
      const dialogue = extractCurrentDialogue();
      if (!dialogue) {
        btn.textContent = '未检测到对话';
        setTimeout(() => { btn.textContent = '采集到学习中枢'; }, 2000);
        return;
      }
      btn.textContent = '采集中…';
      btn.style.opacity = '0.7';
      try {
        const data = await apiRequest('/upload/text', 'POST', {
          title: `${adapter?.name || 'AI'}对话 ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`,
          content: dialogue,
          source: 'ai_dialogue',
        });
        if (data.id) {
          btn.textContent = `已采集 (${data.char_count}字)`;
          btn.style.background = '#4ec9a0';
        } else {
          btn.textContent = '采集失败';
          btn.style.background = '#ff5c7a';
        }
      } catch (e) {
        console.error('[study-hub] 采集失败:', e);
        btn.textContent = '连接失败';
        btn.style.background = '#ff5c7a';
      }
      setTimeout(() => {
        btn.textContent = '采集到学习中枢';
        btn.style.background = '#7c8aff';
        btn.style.opacity = '1';
      }, 3000);
    };

    container.appendChild(autoToggle);
    container.appendChild(rememberBtn);
    container.appendChild(btn);
    document.body.appendChild(container);
  }

  // 启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
