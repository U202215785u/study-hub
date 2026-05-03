// Popup 控制逻辑

const STORAGE_KEY = 'study_hub_api_base';

document.addEventListener('DOMContentLoaded', () => {
  const apiBaseInput = document.getElementById('apiBase');
  const saveBtn = document.getElementById('saveBtn');
  const captureBtn = document.getElementById('captureBtn');
  const statusEl = document.getElementById('status');

  // 加载已保存的 API_BASE
  chrome.storage.sync.get([STORAGE_KEY], (data) => {
    apiBaseInput.value = data[STORAGE_KEY] || 'http://localhost:8741';
  });

  // 保存配置
  saveBtn.addEventListener('click', () => {
    const url = apiBaseInput.value.trim().replace(/\/+$/, '');
    chrome.storage.sync.set({ [STORAGE_KEY]: url }, () => {
      statusEl.textContent = '配置已保存';
      setTimeout(() => { statusEl.textContent = ''; }, 2000);
    });
  });

  // 立即采集当前页面
  captureBtn.addEventListener('click', async () => {
    statusEl.textContent = '正在采集…';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        statusEl.textContent = '未找到活跃标签页';
        return;
      }
      // 向当前标签页注入采集脚本
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const adapter = (() => {
            const hn = window.location.hostname;
            if (hn.includes('claude.ai')) return { name: 'Claude', selectors: { container: '[class*="message"]', fallback: '.prose' } };
            if (hn.includes('chat.openai.com')) return { name: 'ChatGPT', selectors: { container: '[data-message-author-role]' } };
            if (hn.includes('chat.deepseek.com')) return { name: 'DeepSeek', selectors: { container: '[class*="message"]' } };
            if (hn.includes('kimi.moonshot.cn')) return { name: 'Kimi', selectors: { container: '[class*="message"]' } };
            if (hn.includes('doubao.com')) return { name: '豆包', selectors: { container: '[class*="message"]' } };
            return null;
          })();
          if (!adapter) return { error: '当前页面不是支持的 AI 网站' };
          const selector = adapter.selectors.container;
          const elements = document.querySelectorAll(selector);
          const texts = [];
          elements.forEach(el => { const t = el.textContent?.trim(); if (t) texts.push(t); });
          return { text: texts.join('\n\n---\n\n'), title: `${adapter.name}对话 ${new Date().toISOString().slice(0, 16).replace('T', ' ')}` };
        },
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
      // 发送到后端
      const apiBase = apiBaseInput.value.trim().replace(/\/+$/, '') || 'http://localhost:8741';
      const resp = await fetch(`${apiBase}/upload/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: result.title, content: result.text, source: 'ai_dialogue' }),
      });
      const data = await resp.json();
      if (data.id) {
        statusEl.textContent = `已采集 (${data.char_count} 字)`;
      } else {
        statusEl.textContent = '采集失败: ' + (data.error || '未知错误');
      }
    } catch (err) {
      statusEl.textContent = '采集失败: ' + err.message;
    }
  });
});
