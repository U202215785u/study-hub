// AI 网站适配器配置
// 内置默认适配器 + 用户自定义适配器

const DEFAULT_ADAPTERS = {
  'claude.ai': {
    name: 'Claude',
    selectors: {
      container: '[data-testid="user-message"], [data-testid="assistant-message"], .font-user-message, .font-assistant-message',
      fallback: '.prose, [class*="message"]',
    },
    extract(element) {
      return element.textContent.trim();
    },
  },
  'chat.openai.com': {
    name: 'ChatGPT',
    selectors: {
      container: '[data-message-author-role="user"], [data-message-author-role="assistant"]',
      fallback: '.text-message, [class*="markdown"]',
    },
    extract(element) {
      return element.textContent.trim();
    },
  },
  'chat.deepseek.com': {
    name: 'DeepSeek',
    selectors: {
      container: '[class*="message"], .chat-message',
      fallback: '[class*="bubble"]',
    },
    extract(element) {
      return element.textContent.trim();
    },
  },
  'kimi.moonshot.cn': {
    name: 'Kimi',
    selectors: {
      container: '[class*="message"], [class*="chat-item"], [class*="bubble"]',
      fallback: 'div[class*="md"]',
    },
    extract(element) {
      return element.textContent.trim();
    },
  },
  'kimi.com': {
    name: 'Kimi',
    selectors: {
      // 主选择器：Kimi 对话消息的主容器
      container: '[class*="conversation"], [class*="message-list"] > div, [class*="chat-message"]',
      // 精确选择器：用户和 AI 的消息
      fallback: '[data-testid="user-message"], [data-testid="assistant-message"], .message-item, [class*="message-content"]',
    },
    extract(element) {
      // 过滤掉推荐内容、广告等非对话元素
      const text = element.textContent.trim();
      // 排除过短的内容（可能是按钮、标签）
      if (text.length < 5) return '';
      // 排除包含特定广告/推荐文本的内容
      if (text.includes('一键接入') && text.includes('platform.kimi.com')) return '';
      if (text.includes('API 走起')) return '';
      return text;
    },
  },
  'www.doubao.com': {
    name: '豆包',
    selectors: {
      container: '[class*="message"], [class*="chat"]',
      fallback: '[class*="bubble"]',
    },
    extract(element) {
      return element.textContent.trim();
    },
  },
};

// 存储键
const CUSTOM_ADAPTERS_KEY = 'study_hub_custom_adapters';

// 获取所有适配器（默认 + 用户自定义）
async function getAllAdapters() {
  return new Promise((resolve) => {
    chrome.storage.sync.get([CUSTOM_ADAPTERS_KEY], (data) => {
      const custom = data[CUSTOM_ADAPTERS_KEY] || {};
      resolve({ ...DEFAULT_ADAPTERS, ...custom });
    });
  });
}

// 保存自定义适配器
async function saveCustomAdapter(hostname, config) {
  return new Promise((resolve) => {
    chrome.storage.sync.get([CUSTOM_ADAPTERS_KEY], (data) => {
      const custom = data[CUSTOM_ADAPTERS_KEY] || {};
      custom[hostname] = config;
      chrome.storage.sync.set({ [CUSTOM_ADAPTERS_KEY]: custom }, resolve);
    });
  });
}

// 删除自定义适配器
async function deleteCustomAdapter(hostname) {
  return new Promise((resolve) => {
    chrome.storage.sync.get([CUSTOM_ADAPTERS_KEY], (data) => {
      const custom = data[CUSTOM_ADAPTERS_KEY] || {};
      delete custom[hostname];
      chrome.storage.sync.set({ [CUSTOM_ADAPTERS_KEY]: custom }, resolve);
    });
  });
}

// 根据当前 hostname 获取适配器
async function getAdapter() {
  const hostname = window.location.hostname;
  const adapters = await getAllAdapters();
  
  // 优先精确匹配
  if (adapters[hostname]) {
    return adapters[hostname];
  }
  
  // 模糊匹配
  for (const [key, adapter] of Object.entries(adapters)) {
    if (hostname.includes(key) || key.includes(hostname)) {
      return adapter;
    }
  }
  
  return null;
}

// 检测页面对话元素（用于可视化配置）
function detectChatElements() {
  const candidates = [];
  
  // 常见对话容器特征
  const patterns = [
    { selector: '[class*="message"]', weight: 10 },
    { selector: '[class*="chat"]', weight: 8 },
    { selector: '[class*="bubble"]', weight: 8 },
    { selector: '[data-testid*="message"]', weight: 10 },
    { selector: '[data-message-author-role]', weight: 10 },
    { selector: 'article', weight: 3 },
    { selector: 'div[role="listitem"]', weight: 5 },
  ];
  
  for (const { selector, weight } of patterns) {
    try {
      const elements = document.querySelectorAll(selector);
      if (elements.length >= 2) {
        // 检查内容是否像对话
        const texts = Array.from(elements).map(el => el.textContent?.trim()).filter(Boolean);
        const avgLength = texts.reduce((a, b) => a + b.length, 0) / texts.length;
        
        if (avgLength > 10 && avgLength < 5000) {
          candidates.push({
            selector,
            count: elements.length,
            avgLength: Math.round(avgLength),
            sample: texts[0]?.slice(0, 50) + '...',
            score: weight * Math.min(elements.length, 20),
          });
        }
      }
    } catch (e) {
      // 忽略无效选择器
    }
  }
  
  return candidates.sort((a, b) => b.score - a.score);
}

// 测试选择器是否有效
function testSelector(selector) {
  try {
    const elements = document.querySelectorAll(selector);
    const texts = Array.from(elements).map(el => el.textContent?.trim()).filter(Boolean);
    return {
      valid: elements.length > 0,
      count: elements.length,
      texts: texts.slice(0, 3),
      totalLength: texts.reduce((a, b) => a + b.length, 0),
    };
  } catch (e) {
    return { valid: false, error: e.message };
  }
}

// 导出给 content.js 使用（保持同步兼容）
function getAdapterSync() {
  const hostname = window.location.hostname;
  
  // 先检查默认适配器
  if (DEFAULT_ADAPTERS[hostname]) {
    return DEFAULT_ADAPTERS[hostname];
  }
  
  for (const [key, adapter] of Object.entries(DEFAULT_ADAPTERS)) {
    if (hostname.includes(key) || key.includes(hostname)) {
      return adapter;
    }
  }
  
  return null;
}
