// Popup 控制逻辑 — 网页剪藏 + 抖音收藏导入
// 所有请求通过 background.js 代理，绕过 CORS

const STORAGE_KEY = 'study_hub_api_base';

document.addEventListener('DOMContentLoaded', () => {
  const apiBaseInput = document.getElementById('apiBase');
  const saveBtn = document.getElementById('saveBtn');
  const captureBtn = document.getElementById('captureBtn');
  const clipPageBtn = document.getElementById('clipPageBtn');
  const statusEl = document.getElementById('status');

  // 抖音收藏相关
  const douyinSection = document.getElementById('douyinSection');
  const douyinFavBtn = document.getElementById('douyinFavBtn');
  const douyinStatus = document.getElementById('douyinStatus');
  const douyinLinkList = document.getElementById('douyinLinkList');

  checkDouyinPage();

  // 加载配置
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

  // 📄 采集到知识库
  captureBtn.addEventListener('click', async () => {
    statusEl.textContent = '正在采集…';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        statusEl.textContent = '未找到活跃标签页';
        return;
      }
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'CLIP_PAGE' });
      if (!response || !response.success) {
        statusEl.textContent = '采集失败: ' + (response?.error || '未知错误');
        return;
      }

      const apiBase = await getApiBase();
      const resp = await fetch(`${apiBase}/upload/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: response.title || tab.title || '网页采集',
          content: response.content,
          source: 'web_capture',
          source_url: tab.url,
        }),
      });
      const data = await resp.json();
      if (data.id) {
        statusEl.textContent = `✅ 已采集 ${data.char_count} 字`;
      } else {
        statusEl.textContent = '采集失败';
      }
    } catch (err) {
      statusEl.textContent = '采集失败: ' + err.message;
    }
  });

  // 📄 剪藏当前网页
  clipPageBtn.addEventListener('click', async () => {
    statusEl.textContent = '正在剪藏…';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        statusEl.textContent = '未找到活跃标签页';
        return;
      }
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'CLIP_PAGE' });
      if (!response || !response.success) {
        statusEl.textContent = '剪藏失败: ' + (response?.error || '未知错误');
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
        statusEl.textContent = `✅ 已剪藏 ${data.char_count} 字`;
      } else {
        statusEl.textContent = '剪藏失败';
      }
    } catch (err) {
      statusEl.textContent = '剪藏失败: ' + err.message;
    }
  });

  // 📹 抖音收藏导入
  douyinFavBtn.addEventListener('click', async () => {
    douyinStatus.textContent = '正在采集收藏列表…';
    douyinLinkList.style.display = 'none';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        douyinStatus.textContent = '未找到活跃标签页';
        return;
      }
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const links = [];
          document.querySelectorAll('a[href*="/video/"]').forEach(a => {
            const match = a.href.match(/\/video\/(\d+)/);
            if (match) links.push(match[1]);
          });
          return [...new Set(links)];
        },
      });
      const videoIds = results[0]?.result || [];
      if (videoIds.length === 0) {
        douyinStatus.textContent = '未找到收藏视频，请确认在抖音收藏页面';
        return;
      }
      douyinStatus.textContent = `找到 ${videoIds.length} 个视频，正在提交…`;

      const apiBase = await getApiBase();
      const resp = await fetch(`${apiBase}/automation/douyin_fav`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_ids: videoIds }),
      });
      const data = await resp.json();
      if (data.task_id) {
        douyinStatus.textContent = `✅ 已提交 ${videoIds.length} 个视频，任务ID: ${data.task_id}`;
        douyinLinkList.innerHTML = videoIds.map(id => `<div>• ${id}</div>`).join('');
        douyinLinkList.style.display = 'block';
      } else {
        douyinStatus.textContent = '提交失败: ' + (data.error || '未知错误');
      }
    } catch (err) {
      douyinStatus.textContent = '采集失败: ' + err.message;
    }
  });

  async function getApiBase() {
    const data = await chrome.storage.sync.get([STORAGE_KEY]);
    return (data[STORAGE_KEY] || 'http://localhost:8741').replace(/\/+$/, '');
  }

  async function checkDouyinPage() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.url && tab.url.includes('douyin.com')) {
        douyinSection.style.display = 'block';
      }
    } catch (e) {
      // ignore
    }
  }
});
