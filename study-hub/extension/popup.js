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
    douyinFavBtn.disabled = true;
    douyinFavBtn.textContent = '⏳ 采集中…';
    douyinStatus.textContent = '正在采集已显示的收藏视频…';
    douyinLinkList.style.display = 'none';
    douyinLinkList.innerHTML = '';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        douyinStatus.textContent = '未找到活跃标签页';
        return;
      }
      if (!DouyinFavorites.isDouyinFavoritesUrl(tab.url)) {
        douyinStatus.textContent = '当前不是抖音收藏页，请先打开个人中心的收藏页';
        return;
      }

      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        world: 'ISOLATED',
        func: DouyinFavorites.collectDouyinFavorites,
        args: [30, 5, 1200],
      });

      const collection = results[0]?.result;
      const links = collection?.links || [];
      if (links.length === 0) {
        douyinStatus.textContent = '未找到可导入的抖音视频，请确认收藏列表已加载';
        return;
      }

      douyinStatus.textContent = `找到 ${links.length} 个视频，正在提交解析队列…`;
      const data = await sendRuntimeMessage(DouyinFavorites.buildDouyinQueueMessage(links));
      const skippedText = data.skipped ? `，跳过 ${data.skipped} 个已存在链接` : '';
      douyinStatus.textContent = `已加入 ${data.count || 0} 个解析任务${skippedText}`;
      douyinLinkList.innerHTML = links.slice(0, 20).map((url, index) =>
        `<div>${index + 1}. ${url}</div>`
      ).join('') + (links.length > 20 ? `<div>还有 ${links.length - 20} 条…</div>` : '');
      douyinLinkList.style.display = 'block';
    } catch (err) {
      douyinStatus.textContent = '后端不可用或提交失败：' + (err.message || '未知错误');
    } finally {
      douyinFavBtn.disabled = false;
      douyinFavBtn.textContent = '🔄 采集当前页收藏';
    }
  });

  function sendRuntimeMessage(message) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        if (!response) {
          reject(new Error('未收到后端响应'));
          return;
        }
        if (response.error) {
          reject(new Error(response.error));
          return;
        }
        resolve(response.data || {});
      });
    });
  }

  async function getApiBase() {
    const data = await chrome.storage.sync.get([STORAGE_KEY]);
    return (data[STORAGE_KEY] || 'http://localhost:8741').replace(/\/+$/, '');
  }

  async function checkDouyinPage() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.url && tab.url.includes('douyin.com')) {
        douyinSection.style.display = 'block';
        if (!DouyinFavorites.isDouyinFavoritesUrl(tab.url)) {
          douyinStatus.textContent = '当前不是抖音收藏页，请先打开个人中心的收藏页';
        }
      }
    } catch (e) {
      // ignore
    }
  }
});
