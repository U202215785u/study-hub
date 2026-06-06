// Service Worker：五层记忆系统 + API 代理
// 代理 content script 的请求，绕过 CORS 限制

const STORAGE_KEY = 'study_hub_dialogues';
const API_BASE_CONFIG_KEY = 'study_hub_api_base';
const AUTO_EXTRACT_KEY = 'study_hub_auto_extract';
const CUSTOM_ADAPTERS_KEY = 'study_hub_custom_adapters';

// Service Worker 保活：使用 alarms API（Edge/Chrome 都支持，比 setInterval 更可靠）
chrome.alarms.create('keepAlive', { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'keepAlive') {
    console.log('[study-hub] alarm 保活触发');
  }
});

// 备用：setInterval 双重保活
function keepAlive() {
  console.log('[study-hub] Service Worker 心跳');
}
setInterval(keepAlive, 20000);

// 获取 API 地址
async function getApiBase() {
  try {
    const data = await chrome.storage.sync.get([API_BASE_CONFIG_KEY]);
    return (data[API_BASE_CONFIG_KEY] || 'http://localhost:8741').replace(/\/+$/, '');
  } catch (e) {
    console.warn('[study-hub] storage.sync 读取失败，使用默认地址:', e.message);
    return 'http://localhost:8741';
  }
}

// 检查自动提取是否开启
async function isAutoExtractEnabled() {
  try {
    const data = await chrome.storage.sync.get([AUTO_EXTRACT_KEY]);
    return data[AUTO_EXTRACT_KEY] !== false;
  } catch (e) {
    return true;
  }
}

// 代理 API 请求（content script → background → 后端）
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[study-hub] 收到消息:', request.type, request.path || '');
  
  if (request.type === 'PING') {
    sendResponse({ pong: true });
    return false;
  }
  
  if (request.type === 'API_REQUEST') {
    handleApiRequest(request, sendResponse);
    return true; // 保持通道开放，异步响应
  }
  
  // 未知消息类型
  sendResponse({ error: '未知消息类型: ' + request.type });
  return false;
});

async function handleApiRequest(request, sendResponse) {
  try {
    const apiBase = await getApiBase();
    const url = `${apiBase}${request.path}`;
    
    console.log('[study-hub] 代理请求:', request.method, url);
    
    const fetchOptions = {
      method: request.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    if (request.body && (request.method === 'POST' || request.method === 'PUT')) {
      fetchOptions.body = JSON.stringify(request.body);
    }
    
    const resp = await fetch(url, fetchOptions);
    
    if (!resp.ok) {
      const text = await resp.text();
      console.error('[study-hub] HTTP 错误:', resp.status, text);
      sendResponse({ error: `HTTP ${resp.status}: ${text}` });
      return;
    }
    
    const data = await resp.json();
    
    // 检查后端返回的业务错误
    if (data.error) {
      console.error('[study-hub] 后端错误:', data.error);
      sendResponse({ error: data.error });
      return;
    }
    
    console.log('[study-hub] 代理响应成功');
    sendResponse({ data });
  } catch (error) {
    console.error('[study-hub] API 代理失败:', error);
    sendResponse({ error: error.message || '未知错误' });
  }
}

// 标签页关闭时自动提取
chrome.tabs.onRemoved.addListener(async (tabId, removeInfo) => {
  try {
    const autoEnabled = await isAutoExtractEnabled();
    if (!autoEnabled) {
      await chrome.storage.local.remove(STORAGE_KEY);
      return;
    }

    const data = await chrome.storage.local.get([STORAGE_KEY]);
    const dialogue = data[STORAGE_KEY] || '';

    if (dialogue.trim().length < 200) {
      await chrome.storage.local.remove(STORAGE_KEY);
      return;
    }

    const apiBase = await getApiBase();
    const resp = await fetch(`${apiBase}/memory/summarize_and_extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation: dialogue,
        source_tool: 'chrome_extension',
        source_ref: `tab_${tabId}`,
      }),
    });

    const result = await resp.json();
    if (result.added > 0) {
      console.log(`[study-hub] 自动提取 ${result.added} 条记忆:`, result.added_by_layer);
    }

    await chrome.storage.local.remove(STORAGE_KEY);
  } catch (err) {
    console.error('[study-hub] 自动提取失败:', err);
  }
});

// 扩展安装/更新时初始化
chrome.runtime.onInstalled.addListener((details) => {
  console.log('[study-hub] 扩展事件:', details.reason);
  console.log('[study-hub] 五层记忆系统扩展 v2.0 已安装');

  chrome.storage.sync.get([AUTO_EXTRACT_KEY], (data) => {
    if (data[AUTO_EXTRACT_KEY] === undefined) {
      chrome.storage.sync.set({ [AUTO_EXTRACT_KEY]: true });
    }
  });

  // 创建右键菜单
  chrome.contextMenus.create({
    id: 'study-hub-clip-selection',
    title: '📝 剪藏选中内容到 Study-Hub',
    contexts: ['selection'],
  });
  chrome.contextMenus.create({
    id: 'study-hub-clip-page',
    title: '📄 剪藏整个网页到 Study-Hub',
    contexts: ['page', 'link'],
  });
});

// 右键菜单点击处理
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'study-hub-clip-selection') {
    // 剪藏选中的文本
    const selectedText = info.selectionText;
    if (!selectedText || selectedText.length < 10) return;

    try {
      const apiBase = await getApiBase();
      const resp = await fetch(`${apiBase}/upload/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `${tab.title || '选中内容'} ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`,
          content: selectedText,
          source: 'web_clipper_selection',
          source_url: tab.url,
        }),
      });
      const data = await resp.json();
      if (data.id) {
        console.log('[study-hub] 选中内容已剪藏:', data.char_count, '字');
      }
    } catch (err) {
      console.error('[study-hub] 剪藏选中内容失败:', err);
    }
  }

  if (info.menuItemId === 'study-hub-clip-page') {
    // 剪藏整个网页
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'CLIP_PAGE' });
      if (!response || !response.success) {
        console.error('[study-hub] 网页提取失败:', response?.error);
        return;
      }

      const apiBase = await getApiBase();
      const resp = await fetch(`${apiBase}/upload/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: response.title || tab.title || '网页剪藏',
          content: response.content,
          source: 'web_clipper',
          source_url: tab.url,
        }),
      });
      const data = await resp.json();
      if (data.id) {
        console.log('[study-hub] 网页已剪藏:', data.char_count, '字');
      }
    } catch (err) {
      console.error('[study-hub] 剪藏网页失败:', err);
    }
  }
});

// 扩展启动时
chrome.runtime.onStartup.addListener(() => {
  console.log('[study-hub] 浏览器启动，扩展激活');
});

console.log('[study-hub] Service Worker 已加载');
