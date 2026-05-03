// Service Worker：监听标签页关闭，采集对话数据

const STORAGE_KEY = 'study_hub_dialogues';
const API_BASE_CONFIG_KEY = 'study_hub_api_base';

async function getApiBase() {
  const data = await chrome.storage.sync.get([API_BASE_CONFIG_KEY]);
  return (data[API_BASE_CONFIG_KEY] || 'http://localhost:8741').replace(/\/+$/, '');
}

// 标签页关闭时收集对话
chrome.tabs.onRemoved.addListener(async (tabId, removeInfo) => {
  try {
    const data = await chrome.storage.session.get([STORAGE_KEY]);
    const dialogue = data[STORAGE_KEY] || '';

    if (dialogue.trim()) {
      const apiBase = await getApiBase();
      const title = `AI对话记录 ${new Date().toISOString().slice(0, 19).replace('T', ' ')}`;

      await fetch(`${apiBase}/upload/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          content: dialogue,
          source: 'ai_dialogue',
        }),
      });

      await chrome.storage.session.remove(STORAGE_KEY);
    }
  } catch (err) {
    console.error('学习中枢扩展: 对话回流失败', err);
  }
});

// 扩展安装时初始化
chrome.runtime.onInstalled.addListener(() => {
  console.log('学习中枢扩展已安装');
});
