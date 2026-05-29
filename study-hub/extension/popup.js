// Popup 控制逻辑 — 五层记忆系统 + 自定义网站配置
// 所有请求通过 background.js 代理，绕过 CORS

const STORAGE_KEY = 'study_hub_api_base';
const AUTO_EXTRACT_KEY = 'study_hub_auto_extract';
const CUSTOM_ADAPTERS_KEY = 'study_hub_custom_adapters';

document.addEventListener('DOMContentLoaded', () => {
  const apiBaseInput = document.getElementById('apiBase');
  const saveBtn = document.getElementById('saveBtn');
  const captureBtn = document.getElementById('captureBtn');
  const rememberBtn = document.getElementById('rememberBtn');
  const autoToggle = document.getElementById('autoToggle');
  const statusEl = document.getElementById('status');
  const layerStats = document.getElementById('layerStats');

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

  // 采集到知识库
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
