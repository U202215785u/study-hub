// AI 网站对话 DOM 选择器配置
// 每个适配器定义如何提取该网站的对话文本
// selector: 对话容器元素选择器
// textExtractor: 从容器提取纯文本的函数

const ADAPTERS = {
  'claude.ai': {
    name: 'Claude',
    selectors: {
      container: '[data-testid="user-message"], [data-testid="assistant-message"], .font-user-message, .font-assistant-message',
      // Claude 的 DOM 经常变，备选选择器
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
      container: '[class*="message"], [class*="chat-item"]',
      fallback: '[class*="bubble"]',
    },
    extract(element) {
      return element.textContent.trim();
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

// 根据当前 hostname 获取适配器
function getAdapter() {
  const hostname = window.location.hostname;
  for (const [key, adapter] of Object.entries(ADAPTERS)) {
    if (hostname.includes(key)) return adapter;
  }
  return null;
}
