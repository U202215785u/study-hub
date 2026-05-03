// 对话提取 content script
// 每 30 秒扫描页面，提取新增对话内容
// 注入浮动采集按钮

(function () {
  const adapter = getAdapter();
  if (!adapter) return;

  const STORAGE_KEY = 'study_hub_dialogues';
  const INTERVAL_MS = 30000;

  let lastSnapshot = '';

  function extractCurrentDialogue() {
    if (!adapter || !adapter.selectors) return '';

    let elements = document.querySelectorAll(adapter.selectors.container);
    if (elements.length === 0 && adapter.selectors.fallback) {
      elements = document.querySelectorAll(adapter.selectors.fallback);
    }

    const texts = [];
    elements.forEach(el => {
      const text = adapter.extract(el);
      if (text) texts.push(text);
    });

    return texts.join('\n\n---\n\n');
  }

  function scan() {
    const current = extractCurrentDialogue();
    if (!current) return;

    if (current !== lastSnapshot) {
      const newContent = current.slice(lastSnapshot.length).trim();
      if (newContent) {
        chrome.storage.session.get([STORAGE_KEY], (data) => {
          const existing = data[STORAGE_KEY] || '';
          chrome.storage.session.set({
            [STORAGE_KEY]: existing + '\n' + newContent,
          });
        });
      }
      lastSnapshot = current;
    }
  }

  // 注入浮动采集按钮
  function injectCaptureButton() {
    if (document.getElementById('study-hub-capture-btn')) return;

    const btn = document.createElement('button');
    btn.id = 'study-hub-capture-btn';
    btn.textContent = '采集到学习中枢';
    btn.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; z-index: 99999;
      padding: 10px 18px; border-radius: 20px; border: none;
      background: #7c8aff; color: #fff; font-size: 14px; font-weight: 600;
      cursor: pointer; box-shadow: 0 4px 16px rgba(124,138,255,0.4);
      transition: transform 0.15s, opacity 0.15s; font-family: -apple-system, sans-serif;
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
        const apiBase = await getApiBase();
        const title = `${adapter.name || 'AI'}对话 ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`;
        const resp = await fetch(`${apiBase}/upload/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content: dialogue, source: 'claude' }),
        });
        const data = await resp.json();
        if (data.id) {
          btn.textContent = `已采集 (${data.char_count}字)`;
          btn.style.background = '#4ec9a0';
        } else {
          btn.textContent = '采集失败';
          btn.style.background = '#ff5c7a';
        }
      } catch {
        btn.textContent = '连接失败';
        btn.style.background = '#ff5c7a';
      }

      setTimeout(() => {
        btn.textContent = '采集到学习中枢';
        btn.style.background = '#7c8aff';
        btn.style.opacity = '1';
      }, 3000);
    };

    document.body.appendChild(btn);
  }

  function getApiBase() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['study_hub_api_base'], (data) => {
        resolve(data['study_hub_api_base'] || 'http://localhost:8741');
      });
    });
  }

  // 启动
  setTimeout(() => {
    scan();
    if (document.body) injectCaptureButton();
    else document.addEventListener('DOMContentLoaded', injectCaptureButton);
  }, 3000);

  setInterval(scan, INTERVAL_MS);

  window.addEventListener('beforeunload', () => {
    scan();
  });
})();
