

    // 注入 CSS 到 Shadow DOM
    const style = document.createElement('style');
    style.textContent = getPanelCSS();
    shadow.appendChild(style);// Study Hub Bing \u641c\u7d22\u52a9\u624b\u6d6e\u7a97
// \u5728 Bing \u641c\u7d22\u7ed3\u679c\u9875\u6ce8\u5165\u8f85\u52a9\u6d6e\u7a97

(function() {
  'use strict';

  // ===== \u914d\u7f6e =====
  const CONFIG = {
    REF_PARAM: 'ref=studyhub',
    PANEL_WIDTH: 360,
    PANEL_COLLAPSED_WIDTH: 60,
    STORAGE_KEY_STATE: 'studyhub_assistant_state',
    STORAGE_KEY_PREFERENCES: 'studyhub_assistant_prefs',
    GUIDE_DISMISS_COUNT: 3, // \u5f15\u5bfc\u663e\u793a\u6b21\u6570
  };

  // ===== \u72b6\u6001 =====
  let panelEl = null;
  let dotEl = null;
  let isDragging = false;
  let dragOffset = { x: 0, y: 0 };
  let currentScene = null;
  let sceneRules = null;
  let searchQuery = '';
  let sessionId = '';
  let isPinned = true;
  let isCollapsed = false;
  let guideShownCount = 0;

  // ===== \u521d\u59cb\u5316 =====

  async function init() {
    console.log('[studyhub-assistant] ===== \u521d\u59cb\u5316\u5f00\u59cb =====');
    console.log('[studyhub-assistant] URL:', window.location.href);
    console.log('[studyhub-assistant] \u641c\u7d22\u53c2\u6570:', window.location.search);

    // \u68c0\u67e5\u662f\u5426\u662f\u6765\u81ea Study Hub \u7684\u641c\u7d22
    if (!isFromStudyHub()) {
      console.log('[studyhub-assistant] \u975e Study Hub \u6765\u6e90，\u4e0d\u6ce8\u5165\u6d6e\u7a97');
      console.log('[studyhub-assistant] \u5f53\u524dURL\u4e0d\u542b ref=studyhub');
      return;
    }

    console.log('[studyhub-assistant] \u2705 \u68c0\u6d4b\u5230 Study Hub \u641c\u7d22\uff0c\u521d\u59cb\u5316\u6d6e\u7a97');

    // \u89e3\u6790 URL \u53c2\u6570
    const urlParams = new URLSearchParams(window.location.search);
    searchQuery = urlParams.get('q') || '';
    sessionId = urlParams.get('sid') || generateSessionId();
    let initialScene = urlParams.get('scene');

    // \u52a0\u8f7d\u573a\u666f\u89c4\u5219
    await loadSceneRules();

    // \u5c1d\u8bd5\u4ece sessionStorage \u6062\u590d\u7b5b\u9009\u72b6\u6001（\u9875\u9762\u5237\u65b0\u540e）
    const savedFilterState = sessionStorage.getItem('studyhub_filter_state');
    let restoredSources = null;
    if (savedFilterState) {
      try {
        const filterState = JSON.parse(savedFilterState);
        // \u68c0\u67e5\u662f\u5426\u5728 5 \u5206\u949f\u5185（\u907f\u514d\u8fc7\u671f\u72b6\u6001）
        if (Date.now() - filterState.timestamp < 5 * 60 * 1000) {
          if (filterState.sceneId) {
            initialScene = filterState.sceneId;
          }
          restoredSources = filterState.checkedSources || [];
          console.log('[studyhub-assistant] \u4ece sessionStorage \u6062\u590d\u7b5b\u9009\u72b6\u6001:', restoredSources);
        } else {
          // \u8fc7\u671f，\u6e05\u9664
          sessionStorage.removeItem('studyhub_filter_state');
        }
      } catch (e) {
        console.warn('[studyhub-assistant] \u89e3\u6790\u7b5b\u9009\u72b6\u6001\u5931\u8d25:', e);
      }
    }

    // \u5339\u914d\u573a\u666f
    currentScene = initialScene
      ? sceneRules.scenes.find(s => s.id === initialScene)
      : matchScene(searchQuery);

    if (!currentScene) {
      currentScene = sceneRules.scenes.find(s => s.id === sceneRules.defaultScene);
    }

    // \u52a0\u8f7d\u7528\u6237\u504f\u597d
    await loadPreferences();

    // \u5982\u679c\u6709\u6062\u590d\u7684\u7b5b\u9009\u72b6\u6001，\u5e94\u7528\u5230\u5f53\u524d\u573a\u666f
    if (restoredSources && currentScene) {
      currentScene.sources.forEach(source => {
        const key = source.domain || source.name;
        if (restoredSources.includes(key)) {
          source.checked = true;
          source.fromMemory = true;
        }
      });
    }

    // \u521b\u5efa\u6d6e\u7a97
    createPanel();

    // \u8c03\u6574 Bing \u5e03\u5c40
    adjustBingLayout();

    // \u76d1\u542c\u9875\u9762\u53d8\u5316（Bing \u662f SPA，\u641c\u7d22\u65f6\u4e0d\u4f1a\u5237\u65b0\u9875\u9762）
    observeUrlChanges();
  }

  function isFromStudyHub() {
    const hasRef = window.location.search.includes(CONFIG.REF_PARAM);
    console.log('[studyhub-assistant] \u68c0\u67e5 ref=studyhub:', hasRef, 'URL:', window.location.search);
    return hasRef;
  }

  function generateSessionId() {
    return 'sh_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 6);
  }

  // ===== \u573a\u666f\u89c4\u5219\u52a0\u8f7d =====

  async function loadSceneRules() {
    try {
      // \u68c0\u67e5 chrome.runtime \u662f\u5426\u53ef\u7528
      if (typeof chrome === "undefined" || !chrome.runtime || !chrome.runtime.getURL) {
        console.warn("[studyhub-assistant] chrome.runtime \u4e0d\u53ef\u7528，\u4f7f\u7528\u5185\u7f6e\u89c4\u5219");
        sceneRules = getBuiltinSceneRules();
        return;
      }
      // \u5c1d\u8bd5\u4ece\u6269\u5c55\u8d44\u6e90\u52a0\u8f7d
      const url = chrome.runtime.getURL("data/scene-rules.json");
      // \u9a8c\u8bc1 URL \u662f\u5426\u6709\u6548（\u4e0d\u662f chrome-extension://invalid/）
      if (url.includes("chrome-extension://invalid/")) {
        console.warn("[studyhub-assistant] \u6269\u5c55 URL \u65e0\u6548，\u4f7f\u7528\u5185\u7f6e\u89c4\u5219");
        sceneRules = getBuiltinSceneRules();
        return;
      }
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      sceneRules = await response.json();
    } catch (e) {
      console.warn("[studyhub-assistant] \u52a0\u8f7d\u573a\u666f\u89c4\u5219\u5931\u8d25，\u4f7f\u7528\u5185\u7f6e\u89c4\u5219:", e);
      // \u5185\u7f6e\u5907\u7528\u89c4\u5219
      sceneRules = getBuiltinSceneRules();
    }
  }

  function getBuiltinSceneRules() {
    return {
      scenes: [
        {
          id: 'tool_find',
          name: '\u5de5\u5177\u67e5\u627e',
          icon: '🛠️',
          keywords: ['\u5de5\u5177', '\u62a0\u56fe', '\u538b\u7f29', '\u8f6c\u6362'],
          sources: [
            { name: 'GitHub', domain: 'github.com', icon: '🐙' },
            { name: '\u5b98\u7f51', domain: '', icon: '🏠' }
          ],
          tips: ['\u4f18\u5148\u9009\u62e9\u5f00\u6e90\u514d\u8d39\u5de5\u5177'],
          recommendations: [
            { name: 'remove.bg', url: 'https://www.remove.bg', desc: '\u5728\u7ebf\u81ea\u52a8\u62a0\u56fe' }
          ]
        },
        {
          id: 'product_review',
          name: '\u4ea7\u54c1\u6d4b\u8bc4',
          icon: '🎧',
          keywords: ['\u6d4b\u8bc4', '\u8bc4\u6d4b', '\u63a8\u8350', '\u5bf9\u6bd4', '\u8033\u673a', '\u624b\u673a'],
          sources: [
            { name: '\u4ec0\u4e48\u503c\u5f97\u4e70', domain: 'smzdm.com', icon: '💰' },
            { name: '\u77e5\u4e4e', domain: 'zhihu.com', icon: '❓' },
            { name: 'B\u7ad9', domain: 'bilibili.com', icon: '📺' }
          ],
          tips: ['\u5efa\u8bae\u4f18\u5148\u770b\u56fe\u6587\u6d4b\u8bc4\u4e86\u89e3\u53c2\u6570', '\u518d\u770b\u89c6\u9891\u4e86\u89e3\u5b9e\u9645\u4f53\u9a8c'],
          recommendations: [
            { name: '\u5148\u770b\u8bc4\u6d4b', url: 'https://space.bilibili.com/2871017', desc: 'B\u7ad9\u77e5\u540d\u79d1\u6280\u6d4b\u8bc4UP\u4e3b' }
          ]
        }
      ],
      defaultScene: 'tool_find'
    };
  }

  function matchScene(query) {
    if (!query) return null;
    const lowerQuery = query.toLowerCase();

    for (const scene of sceneRules.scenes) {
      for (const keyword of scene.keywords) {
        if (lowerQuery.includes(keyword.toLowerCase())) {
          return scene;
        }
      }
    }
    return null;
  }

  // ===== \u7528\u6237\u504f\u597d =====

  async function loadPreferences() {
    try {
      const data = await chrome.storage.sync.get([CONFIG.STORAGE_KEY_PREFERENCES]);
      const prefs = data[CONFIG.STORAGE_KEY_PREFERENCES] || {};
      guideShownCount = prefs.guideShownCount || 0;

      // \u6062\u590d\u8be5\u573a\u666f\u7684\u6765\u6e90\u52fe\u9009
      if (prefs.sceneSources && currentScene) {
        const saved = prefs.sceneSources[currentScene.id];
        if (saved) {
          currentScene.sources.forEach(source => {
            source.checked = saved.includes(source.domain || source.name);
            source.fromMemory = source.checked;
          });
        }
      }
    } catch (e) {
      console.warn('[studyhub-assistant] \u52a0\u8f7d\u504f\u597d\u5931\u8d25:', e);
    }
  }

  async function savePreferences() {
    try {
      const data = await chrome.storage.sync.get([CONFIG.STORAGE_KEY_PREFERENCES]);
      const prefs = data[CONFIG.STORAGE_KEY_PREFERENCES] || {};

      // \u4fdd\u5b58\u573a\u666f\u6765\u6e90\u52fe\u9009
      if (!prefs.sceneSources) prefs.sceneSources = {};
      if (currentScene) {
        prefs.sceneSources[currentScene.id] = currentScene.sources
          .filter(s => s.checked)
          .map(s => s.domain || s.name);
      }
      prefs.guideShownCount = guideShownCount;

      await chrome.storage.sync.set({ [CONFIG.STORAGE_KEY_PREFERENCES]: prefs });
    } catch (e) {
      console.warn('[studyhub-assistant] \u4fdd\u5b58\u504f\u597d\u5931\u8d25:', e);
    }
  }

  // ===== \u6d6e\u7a97\u521b\u5efa =====

  function createPanel() {
    // \u68c0\u67e5\u662f\u5426\u5df2\u5b58\u5728\u4e14\u6709\u6709\u6548\u7684 shadow root
    const existingHost = document.getElementById('studyhub-assistant-host');
    if (existingHost) {
      try {
        const existingShadow = existingHost.shadowRoot;
        if (existingShadow && existingShadow.querySelector('.studyhub-panel')) {
          return; // \u771f\u6b63\u5df2\u5b58\u5728，\u76f4\u63a5\u8fd4\u56de
        }
        // host \u5b58\u5728\u4f46\u6ca1\u6709 shadow，\u79fb\u9664\u91cd\u65b0\u521b\u5efa
        existingHost.remove();
      } catch(e) {
        existingHost.remove();
      }
    }

    // \u521b\u5efa Shadow DOM host
    const host = document.createElement('div');
    host.id = 'studyhub-assistant-host';
    document.body.appendChild(host);

    const shadow = host.attachShadow({ mode: 'open' });

    // \u521b\u5efa\u9762\u677f
    panelEl = document.createElement('div');
    panelEl.className = 'studyhub-panel animating';
    if (isDarkMode()) {
      panelEl.classList.add('dark-mode');
    }

    panelEl.innerHTML = renderPanelHTML();
    shadow.appendChild(panelEl);

    // \u7ed1\u5b9a\u4e8b\u4ef6
    bindPanelEvents(shadow);

    // \u663e\u793a\u5f15\u5bfc（\u524d3\u6b21），\u4f46\u4ec5\u5728\u975e\u6062\u590d\u72b6\u6001\u65f6\u663e\u793a
    const hasRestoredState = sessionStorage.getItem('studyhub_filter_state');
    if (guideShownCount < CONFIG.GUIDE_DISMISS_COUNT && !hasRestoredState) {
      showGuide(shadow);
      guideShownCount++;
      savePreferences();
    }

    // \u79fb\u9664\u52a8\u753b\u7c7b
    setTimeout(() => {
      panelEl.classList.remove('animating');
    }, 300);
  }

  function renderPanelHTML() {
    const scenes = sceneRules.scenes;
    const sceneTabs = scenes.map(s => `
      <button class="studyhub-tab ${s.id === currentScene.id ? 'active' : ''}" data-scene="${s.id}">
        ${s.icon} ${s.name}
      </button>
    `).join('');

    const recs = currentScene.recommendations && currentScene.recommendations.length > 0
      ? currentScene.recommendations.map(r => `
        <a class="studyhub-rec-item" href="${r.url}" target="_blank" rel="noopener noreferrer">
          <span class="studyhub-rec-icon">🔗</span>
          <div class="studyhub-rec-content">
            <div class="studyhub-rec-name">${r.name}</div>
            <div class="studyhub-rec-desc">${r.desc}</div>
          </div>
        </a>
      `).join('')
      : '<div style="font-size:12px;color:#9ca3af;padding:8px;">\u6682\u65e0\u63a8\u8350\uff0c\u5c1d\u8bd5\u5207\u6362\u573a\u666f</div>';

    const tips = currentScene.tips.map(t => `
      <div class="studyhub-tip">
        <span class="studyhub-tip-icon">⚠️</span>
        <span>${t}</span>
      </div>
    `).join('');

    const sources = currentScene.sources.map(s => `
      <div class="studyhub-filter-item" data-source="${s.domain || s.name}">
        <div class="studyhub-filter-checkbox ${s.checked ? 'checked' : ''}"></div>
        <span class="studyhub-filter-icon">${s.icon}</span>
        <span class="studyhub-filter-name">${s.name}</span>
        ${s.fromMemory ? '<div class="studyhub-filter-memory" title="\u6839\u636e\u4f60\u4e0a\u6b21\u7684\u9009\u62e9\u81ea\u52a8\u52fe\u9009"></div>' : ''}
      </div>
    `).join('');

    // \u5173\u8054\u573a\u666f（\u6392\u9664\u5f53\u524d\u573a\u666f）
    const relatedScenes = scenes
      .filter(s => s.id !== currentScene.id)
      .slice(0, 2);
    const relatedHTML = relatedScenes.length > 0
      ? `
        <div class="studyhub-related">
          <div class="studyhub-related-title">\u4f60\u53ef\u80fd\u4e5f\u60f3\u770b</div>
          ${relatedScenes.map(s => `
            <span class="studyhub-related-item" data-scene="${s.id}">
              ${s.icon} ${s.name}
            </span>
          `).join('')}
        </div>
      `
      : '';

    return `
      <div class="studyhub-header">
        <div class="studyhub-header-left">
          <span>\ud83e\udd16</span>
          <span class="studyhub-header-text">Study Hub \u52a9\u624b</span>
        </div>
        <div class="studyhub-header-right">
          <button class="studyhub-btn" id="sh-pin" title="\u56fa\u5b9a/\u62d6\u62fd">\ud83d\udccc</button>
          <button class="studyhub-btn" id="sh-collapse" title="\u6536\u8d77">\u25c0</button>
          <button class="studyhub-btn" id="sh-close" title="\u5173\u95ed">\u2715</button>
        </div>
      </div>
      <div class="studyhub-tabs">
        ${sceneTabs}
      </div>
      <div class="studyhub-body">
        <div class="studyhub-scene-title">
          <span>${currentScene.icon}</span>
          <span>${currentScene.name}</span>
        </div>
        <div class="studyhub-scene-subtitle">\u641c\u7d22\uff1a${escapeHtml(searchQuery)}</div>

        ${tips}

        <div class="studyhub-section">
          <div class="studyhub-section-title">⭐ \u63a8\u8350</div>
          ${recs}
        </div>

        <div class="studyhub-filter-section">
          <div class="studyhub-filter-header">
            <div class="studyhub-filter-title">\u2699\ufe0f \u6765\u6e90\u7b5b\u9009</div>
            <button class="studyhub-filter-reset" id="sh-reset-filter">\u6062\u590d\u9ed8\u8ba4</button>
          </div>
          <div class="studyhub-filter-list">
            ${sources}
          </div>
          <button class="studyhub-apply-btn" id="sh-apply-filter">
            \u5e94\u7528\u7b5b\u9009\u5e76\u641c\u7d22
          </button>
        </div>

        <div class="studyhub-ai-section">
          <div class="studyhub-ai-title">\ud83e\udd16 AI \u5206\u6790</div>
          <div class="studyhub-ai-content" id="sh-ai-content">
            \u70b9\u51fb"\u5e94\u7528\u7b5b\u9009"\u540e\u5c06\u6839\u636e\u641c\u7d22\u7ed3\u679c\u751f\u6210\u5206\u6790...
          </div>
        </div>

        ${relatedHTML}
      </div>
    `;
  }

  function bindPanelEvents(shadow) {
    const panel = shadow.querySelector('.studyhub-panel');
    const header = shadow.querySelector('.studyhub-header');

    // \u5173\u95ed\u6309\u94ae
    shadow.getElementById('sh-close').addEventListener('click', () => {
      closePanel();
    });

    // \u6536\u8d77\u6309\u94ae
    shadow.getElementById('sh-collapse').addEventListener('click', () => {
      toggleCollapse();
    });

    // \u56fa\u5b9a/\u62d6\u62fd\u5207\u6362
    shadow.getElementById('sh-pin').addEventListener('click', () => {
      togglePin();
    });

    // \u573a\u666f\u6807\u7b7e\u5207\u6362
    shadow.querySelectorAll('.studyhub-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const sceneId = tab.dataset.scene;
        switchScene(sceneId);
      });
    });

    // \u5173\u8054\u573a\u666f\u70b9\u51fb
    shadow.querySelectorAll('.studyhub-related-item').forEach(item => {
      item.addEventListener('click', () => {
        const sceneId = item.dataset.scene;
        switchScene(sceneId);
      });
    });

    // \u6765\u6e90\u7b5b\u9009\u52fe\u9009
    shadow.querySelectorAll('.studyhub-filter-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (e.target.closest('.studyhub-filter-item') === item) {
          toggleSource(item);
        }
      });
    });

    // \u6062\u590d\u9ed8\u8ba4
    shadow.getElementById('sh-reset-filter').addEventListener('click', () => {
      resetSources();
    });

    // \u5e94\u7528\u7b5b\u9009
    shadow.getElementById('sh-apply-filter').addEventListener('click', () => {
      applyFilter();
    });

    // \u62d6\u62fd
    header.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', endDrag);

    // \u53cc\u51fb\u6807\u9898\u680f\u5207\u6362\u56fa\u5b9a/\u62d6\u62fd
    header.addEventListener('dblclick', (e) => {
      e.preventDefault();
      togglePin();
    });
  }

  // ===== \u9762\u677f\u64cd\u4f5c =====

  function closePanel() {
    if (panelEl) {
      panelEl.style.transform = 'translateX(400px)';
      panelEl.style.opacity = '0';
      setTimeout(() => {
        const host = document.getElementById('studyhub-assistant-host');
        if (host) host.remove();
        panelEl = null;
      }, 300);
    }
    // \u6062\u590d Bing \u5e03\u5c40
    restoreBingLayout();
    createDot();
  }

  function restoreBingLayout() {
    const kp = document.querySelector('#b_context');
    const results = document.querySelector('#b_results');
    if (kp) kp.style.display = '';
    if (results) results.style.marginRight = '';
  }

  function createDot() {
    if (dotEl) return;

    dotEl = document.createElement('div');
    dotEl.className = 'studyhub-dot';
    dotEl.innerHTML = '\ud83d\udca1';
    dotEl.title = 'Study Hub \u641c\u7d22\u52a9\u624b';
    dotEl.addEventListener('click', () => {
      dotEl.remove();
      dotEl = null;
      createPanel();
      adjustBingLayout();
    });
    document.body.appendChild(dotEl);
  }

  function toggleCollapse() {
    isCollapsed = !isCollapsed;
    if (panelEl) {
      panelEl.classList.toggle('collapsed', isCollapsed);
      // \u6536\u8d77\u65f6\u6062\u590d Bing \u5e03\u5c40\u7a7a\u95f4，\u5c55\u5f00\u65f6\u91cd\u65b0\u8c03\u6574
      if (isCollapsed) {
        const results = document.querySelector('#b_results');
        if (results) results.style.marginRight = '80px';
      } else {
        const results = document.querySelector('#b_results');
        if (results) results.style.marginRight = '376px';
      }
    }
  }

  function togglePin() {
    isPinned = !isPinned;
    const shadow = document.getElementById('studyhub-assistant-host')?.shadowRoot;
    if (shadow) {
      updatePinButton(shadow);
    }
    // \u56fa\u5b9a\u65f6\u91cd\u7f6e\u5230\u9ed8\u8ba4\u4f4d\u7f6e
    if (isPinned && panelEl) {
      panelEl.style.top = '72px';
      panelEl.style.left = 'auto';
      panelEl.style.right = '16px';
    }
  }

  function updatePinButton(shadow) {
    const btn = shadow.getElementById('sh-pin');
    if (btn) {
      btn.textContent = isPinned ? '\ud83d\udccc' : '\ud83d\udccd';
      btn.title = isPinned ? '\u56fa\u5b9a\uff08\u70b9\u51fb\u89e3\u9664\uff09' : '\u62d6\u62fd\u6a21\u5f0f\uff08\u70b9\u51fb\u56fa\u5b9a\uff09';
    }
    if (panelEl) {
      panelEl.style.cursor = isPinned ? 'default' : 'move';
    }
  }

  // ===== \u573a\u666f\u5207\u6362 =====

  function switchScene(sceneId) {
    const newScene = sceneRules.scenes.find(s => s.id === sceneId);
    if (!newScene || newScene.id === currentScene.id) return;

    currentScene = newScene;

    // \u91cd\u65b0\u52a0\u8f7d\u8be5\u573a\u666f\u7684\u504f\u597d
    loadPreferences().then(() => {
      // \u91cd\u65b0\u6e32\u67d3\u9762\u677f\u5185\u5bb9
      const shadow = document.getElementById('studyhub-assistant-host')?.shadowRoot;
      if (shadow) {
        const body = shadow.querySelector('.studyhub-body');
        const tabs = shadow.querySelector('.studyhub-tabs');

        // \u66f4\u65b0\u6807\u7b7e\u9875
        tabs.innerHTML = sceneRules.scenes.map(s => `
          <button class="studyhub-tab ${s.id === currentScene.id ? 'active' : ''}" data-scene="${s.id}">
            ${s.icon} ${s.name}
          </button>
        `).join('');

        // \u91cd\u65b0\u7ed1\u5b9a\u6807\u7b7e\u4e8b\u4ef6
        tabs.querySelectorAll('.studyhub-tab').forEach(tab => {
          tab.addEventListener('click', () => {
            switchScene(tab.dataset.scene);
          });
        });

        // \u66f4\u65b0\u5185\u5bb9
        body.innerHTML = renderBodyHTML();
        bindBodyEvents(shadow);
      }

      // \u66f4\u65b0 URL scene \u53c2\u6570
      updateUrlScene(sceneId);
    });
  }

  function renderBodyHTML() {
    const recs = currentScene.recommendations && currentScene.recommendations.length > 0
      ? currentScene.recommendations.map(r => `
        <a class="studyhub-rec-item" href="${r.url}" target="_blank" rel="noopener noreferrer">
          <span class="studyhub-rec-icon">🔗</span>
          <div class="studyhub-rec-content">
            <div class="studyhub-rec-name">${r.name}</div>
            <div class="studyhub-rec-desc">${r.desc}</div>
          </div>
        </a>
      `).join('')
      : '<div style="font-size:12px;color:#9ca3af;padding:8px;">\u6682\u65e0\u63a8\u8350，\u5c1d\u8bd5\u5207\u6362\u573a\u666f</div>';

    const tips = currentScene.tips.map(t => `
      <div class="studyhub-tip">
        <span class="studyhub-tip-icon">⚠️</span>
        <span>${t}</span>
      </div>
    `).join('');

    const sources = currentScene.sources.map(s => `
      <div class="studyhub-filter-item" data-source="${s.domain || s.name}">
        <div class="studyhub-filter-checkbox ${s.checked ? 'checked' : ''}"></div>
        <span class="studyhub-filter-icon">${s.icon}</span>
        <span class="studyhub-filter-name">${s.name}</span>
        ${s.fromMemory ? '<div class="studyhub-filter-memory" title="\u6839\u636e\u4f60\u4e0a\u6b21\u7684\u9009\u62e9\u81ea\u52a8\u52fe\u9009"></div>' : ''}
      </div>
    `).join('');

    const relatedScenes = sceneRules.scenes
      .filter(s => s.id !== currentScene.id)
      .slice(0, 2);
    const relatedHTML = relatedScenes.length > 0
      ? `
        <div class="studyhub-related">
          <div class="studyhub-related-title">\u4f60\u53ef\u80fd\u4e5f\u60f3\u770b</div>
          ${relatedScenes.map(s => `
            <span class="studyhub-related-item" data-scene="${s.id}">
              ${s.icon} ${s.name}
            </span>
          `).join('')}
        </div>
      `
      : '';

    return `
      <div class="studyhub-scene-title">
        <span>${currentScene.icon}</span>
        <span>${currentScene.name}</span>
      </div>
      <div class="studyhub-scene-subtitle">\u641c\u7d22：${escapeHtml(searchQuery)}</div>

      ${tips}

      <div class="studyhub-section">
        <div class="studyhub-section-title">⭐ \u63a8\u8350</div>
        ${recs}
      </div>

      <div class="studyhub-filter-section">
        <div class="studyhub-filter-header">
          <div class="studyhub-filter-title">\u2699\ufe0f \u6765\u6e90\u7b5b\u9009</div>
          <button class="studyhub-filter-reset" id="sh-reset-filter">\u6062\u590d\u9ed8\u8ba4</button>
        </div>
        <div class="studyhub-filter-list">
          ${sources}
        </div>
        <button class="studyhub-apply-btn" id="sh-apply-filter">
          \u5e94\u7528\u7b5b\u9009\u5e76\u641c\u7d22
        </button>
      </div>

      <div class="studyhub-ai-section">
        <div class="studyhub-ai-title">\ud83e\udd16 AI \u5206\u6790</div>
        <div class="studyhub-ai-content" id="sh-ai-content">
          \u70b9\u51fb"\u5e94\u7528\u7b5b\u9009"\u540e\u5c06\u6839\u636e\u641c\u7d22\u7ed3\u679c\u751f\u6210\u5206\u6790...
        </div>
      </div>

      ${relatedHTML}
    `;
  }

  function bindBodyEvents(shadow) {
    // \u5173\u8054\u573a\u666f
    shadow.querySelectorAll('.studyhub-related-item').forEach(item => {
      item.addEventListener('click', () => {
        switchScene(item.dataset.scene);
      });
    });

    // \u6765\u6e90\u7b5b\u9009
    shadow.querySelectorAll('.studyhub-filter-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (e.target.closest('.studyhub-filter-item') === item) {
          toggleSource(item);
        }
      });
    });

    // \u6062\u590d\u9ed8\u8ba4
    const resetBtn = shadow.getElementById('sh-reset-filter');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        resetSources();
      });
    }

    // \u5e94\u7528\u7b5b\u9009
    const applyBtn = shadow.getElementById('sh-apply-filter');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => {
        applyFilter();
      });
    }
  }

  function updateUrlScene(sceneId) {
    const url = new URL(window.location.href);
    url.searchParams.set('scene', sceneId);
    window.history.replaceState({}, '', url.toString());
  }

  // ===== \u6765\u6e90\u7b5b\u9009 =====

  function toggleSource(item) {
    const checkbox = item.querySelector('.studyhub-filter-checkbox');
    const sourceName = item.dataset.source;

    checkbox.classList.toggle('checked');
    const isChecked = checkbox.classList.contains('checked');

    // \u66f4\u65b0\u573a\u666f\u6570\u636e
    const source = currentScene.sources.find(s => (s.domain || s.name) === sourceName);
    if (source) {
      source.checked = isChecked;
      source.fromMemory = false; // \u7528\u6237\u624b\u52a8\u64cd\u4f5c\u540e，\u4e0d\u518d\u6807\u8bb0\u4e3a\u8bb0\u5fc6
    }

    // \u4fdd\u5b58\u504f\u597d
    savePreferences();
  }

  function resetSources() {
    currentScene.sources.forEach(s => {
      s.checked = false;
      s.fromMemory = false;
    });

    const shadow = document.getElementById('studyhub-assistant-host')?.shadowRoot;
    if (shadow) {
      shadow.querySelectorAll('.studyhub-filter-checkbox').forEach(cb => {
        cb.classList.remove('checked');
      });
      shadow.querySelectorAll('.studyhub-filter-memory').forEach(m => m.remove());
    }

    savePreferences();
  }

  function applyFilter() {
    const checkedSources = currentScene.sources.filter(s => s.checked);

    if (checkedSources.length === 0) {
      // \u6ca1\u6709\u52fe\u9009，\u63d0\u793a\u7528\u6237
      const shadow = document.getElementById('studyhub-assistant-host')?.shadowRoot;
      const aiContent = shadow?.getElementById('sh-ai-content');
      if (aiContent) {
        aiContent.textContent = '\u8bf7\u5148\u52fe\u9009\u81f3\u5c11\u4e00\u4e2a\u6765\u6e90\uff0c\u6216\u70b9\u51fb"\u6062\u590d\u9ed8\u8ba4"\u6e05\u9664\u7b5b\u9009\u3002';
      }
      return;
    }

    // \u6784\u5efa site: \u8fc7\u6ee4
    const siteFilters = checkedSources
      .filter(s => s.domain)
      .map(s => `site:${s.domain}`)
      .join(' OR ');

    // \u6784\u5efa\u65b0 URL
    const url = new URL(window.location.href);
    let newQuery = searchQuery;

    if (siteFilters) {
      // \u68c0\u67e5\u662f\u5426\u5df2\u6709 site: \u8fc7\u6ee4，\u6709\u5219\u66ff\u6362
      if (newQuery.includes('site:')) {
        newQuery = newQuery.replace(/\s*site:\S+(\s+OR\s+site:\S+)*/g, '').trim();
      }
      newQuery = `${newQuery} ${siteFilters}`;
    }

    url.searchParams.set('q', newQuery);
    url.searchParams.set('scene', currentScene.id);

    // \u4fdd\u5b58\u72b6\u6001（\u7528\u4e8e\u5237\u65b0\u540e\u6062\u590d）
    saveState({
      scene: currentScene.id,
      sources: checkedSources.map(s => s.domain || s.name),
      position: isPinned ? null : { x: panelEl?.offsetLeft, y: panelEl?.offsetTop },
      isPinned,
      isCollapsed
    });

    // \u4fdd\u5b58\u7b5b\u9009\u72b6\u6001\u5230 session storage（\u7528\u4e8e\u9875\u9762\u5237\u65b0\u540e\u6062\u590d\u6d6e\u7a97\u72b6\u6001）
    const filterState = {
      sceneId: currentScene.id,
      checkedSources: checkedSources.map(s => s.domain || s.name),
      timestamp: Date.now()
    };
    sessionStorage.setItem('studyhub_filter_state', JSON.stringify(filterState));

    // \u539f\u5730\u91cd\u8f7d
    window.location.href = url.toString();
  }

  async function saveState(state) {
    try {
      await chrome.storage.local.set({
        [`${CONFIG.STORAGE_KEY_STATE}_${sessionId}`]: state
      });
    } catch (e) {
      console.warn('[studyhub-assistant] \u4fdd\u5b58\u72b6\u6001\u5931\u8d25:', e);
    }
  }

  // ===== \u62d6\u62fd =====

  function startDrag(e) {
    if (isPinned) return;
    // \u53ea\u54cd\u5e94\u6807\u9898\u680f\u62d6\u62fd
    if (!e.target.closest('.studyhub-header')) return;
    isDragging = true;
    const rect = panelEl.getBoundingClientRect();
    dragOffset.x = e.clientX - rect.left;
    dragOffset.y = e.clientY - rect.top;
    panelEl.classList.add('dragging');
    e.preventDefault();
  }

  function onDrag(e) {
    if (!isDragging || !panelEl) return;
    e.preventDefault();
    const x = e.clientX - dragOffset.x;
    const y = e.clientY - dragOffset.y;

    // \u9650\u5236\u5728\u53ef\u89c6\u533a\u57df\u5185
    const maxX = window.innerWidth - panelEl.offsetWidth;
    const maxY = window.innerHeight - panelEl.offsetHeight;

    panelEl.style.left = `${Math.max(0, Math.min(x, maxX))}px`;
    panelEl.style.top = `${Math.max(0, Math.min(y, maxY))}px`;
    panelEl.style.right = 'auto';
  }

  function endDrag() {
    if (!isDragging) return;
    isDragging = false;
    if (panelEl) {
      panelEl.classList.remove('dragging');
      // \u4fdd\u5b58\u62d6\u62fd\u540e\u7684\u4f4d\u7f6e
      saveState({
        scene: currentScene?.id,
        sources: currentScene?.sources?.filter(s => s.checked).map(s => s.domain || s.name) || [],
        position: { x: panelEl.offsetLeft, y: panelEl.offsetTop },
        isPinned: false,
        isCollapsed
      });
    }
  }

  // ===== Bing \u5e03\u5c40\u8c03\u6574 =====

  function adjustBingLayout() {
    // \u68c0\u67e5\u662f\u5426\u6709 Knowledge Panel
    const kp = document.querySelector('#b_context');
    const results = document.querySelector('#b_results');

    if (kp) {
      // \u9690\u85cf Knowledge Panel，\u7ed9\u6d6e\u7a97\u817e\u4f4d\u7f6e
      kp.style.display = 'none';
    }

    if (results) {
      // \u7ed9\u641c\u7d22\u7ed3\u679c\u533a\u52a0\u53f3\u8fb9\u8ddd
      results.style.marginRight = '376px';
      results.style.transition = 'margin-right 0.3s ease';
    }
  }

  // ===== URL \u53d8\u5316\u76d1\u542c（Bing \u662f SPA）=====

  function observeUrlChanges() {
    let lastUrl = window.location.href;

    const observer = new MutationObserver(() => {
      const currentUrl = window.location.href;
      if (currentUrl !== lastUrl) {
        lastUrl = currentUrl;
        // URL \u53d8\u4e86，\u68c0\u67e5\u662f\u5426\u8fd8\u662f\u6765\u81ea Study Hub
        if (isFromStudyHub()) {
          // \u91cd\u65b0\u521d\u59cb\u5316
          const newQuery = new URLSearchParams(window.location.search).get('q') || '';
          if (newQuery !== searchQuery) {
            searchQuery = newQuery;
            // \u6e05\u9664\u65e7\u7684\u7b5b\u9009\u72b6\u6001，\u907f\u514d\u6c61\u67d3\u65b0\u641c\u7d22
            sessionStorage.removeItem('studyhub_filter_state');
            currentScene = matchScene(searchQuery) || currentScene;
            // \u91cd\u65b0\u6e32\u67d3
            const shadow = document.getElementById('studyhub-assistant-host')?.shadowRoot;
            if (shadow && panelEl) {
              const body = shadow.querySelector('.studyhub-body');
              if (body) {
                body.innerHTML = renderBodyHTML();
                bindBodyEvents(shadow);
              }
            }
          }
        } else {
          // \u4e0d\u518d\u6765\u81ea Study Hub，\u6e05\u7406\u6d6e\u7a97
          const host = document.getElementById('studyhub-assistant-host');
          if (host) {
            host.remove();
            panelEl = null;
          }
          if (dotEl) {
            dotEl.remove();
            dotEl = null;
          }
          restoreBingLayout();
        }
      }
    });

    observer.observe(document, { subtree: true, childList: true });
  }

  // ===== \u5de5\u5177\u51fd\u6570 =====

  function isDarkMode() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ||
      window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function showGuide(shadow) {
    const guide = document.createElement('div');
    guide.className = 'studyhub-guide';
    guide.innerHTML = 'Study Hub \u641c\u7d22\u52a9\u624b \u00b7 \u53ef\u5207\u6362\u573a\u666f\u3001\u7b5b\u9009\u6765\u6e90';
    shadow.querySelector('.studyhub-panel').appendChild(guide);

    // 5\u79d2\u540e\u81ea\u52a8\u6d88\u5931
    setTimeout(() => {
      guide.style.opacity = '0';
      guide.style.transition = 'opacity 0.5s';
      setTimeout(() => guide.remove(), 500);
    }, 5000);
  }

  // ===== \u542f\u52a8 =====

  console.log('[studyhub-assistant] \u811a\u672c\u52a0\u8f7d，readyState:', document.readyState);

  function start() {
    console.log('[studyhub-assistant] \u5f00\u59cb\u542f\u52a8...');
    init().catch(err => {
      console.error('[studyhub-assistant] \u521d\u59cb\u5316\u5931\u8d25:', err);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }


  // ===== Shadow DOM CSS =====

  function getPanelCSS() {
    return `/* Study Hub 搜索助手浮窗样式 */
/* 完全自包含，不依赖 Bing 页面 CSS */

#studyhub-assistant-host {
  all: initial !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

#studyhub-assistant-host * {
  all: unset;
  box-sizing: border-box !important;
  font-family: inherit !important;
}

.studyhub-panel {
  position: fixed !important;
  top: 72px !important;
  right: 16px !important;
  width: 360px !important;
  max-height: calc(100vh - 100px) !important;
  background: #ffffff !important;
  border-radius: 12px !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05) !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
  z-index: 999999 !important;
  transition: transform 0.3s ease, opacity 0.3s ease, width 0.3s ease !important;
}

.studyhub-panel.dark-mode {
  background: #1a1a2e !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.08) !important;
}

.studyhub-panel.collapsed {
  width: 60px !important;
  overflow: hidden !important;
}

.studyhub-panel.collapsed .studyhub-body,
.studyhub-panel.collapsed .studyhub-tabs {
  display: none !important;
}

.studyhub-panel.collapsed .studyhub-header-text {
  display: none !important;
}

/* 标题栏 */
.studyhub-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding: 12px 16px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  cursor: move !important;
  user-select: none !important;
  flex-shrink: 0 !important;
}

.studyhub-panel.dark-mode .studyhub-header {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
}

.studyhub-header-left {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}

.studyhub-header-right {
  display: flex !important;
  align-items: center !important;
  gap: 4px !important;
}

.studyhub-btn {
  width: 28px !important;
  height: 28px !important;
  border-radius: 6px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  background: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  font-size: 13px !important;
  transition: background 0.2s !important;
  border: none !important;
}

.studyhub-btn:hover {
  background: rgba(255, 255, 255, 0.3) !important;
}

/* 场景标签页 */
.studyhub-tabs {
  display: flex !important;
  gap: 4px !important;
  padding: 8px 12px 0 !important;
  border-bottom: 1px solid #e5e7eb !important;
  overflow-x: auto !important;
  flex-shrink: 0 !important;
  scrollbar-width: none !important;
}

.studyhub-panel.dark-mode .studyhub-tabs {
  border-bottom-color: #374151 !important;
}

.studyhub-tabs::-webkit-scrollbar {
  display: none !important;
}

.studyhub-tab {
  padding: 6px 12px !important;
  border-radius: 8px 8px 0 0 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  color: #6b7280 !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  transition: all 0.2s !important;
  border: none !important;
  background: transparent !important;
}

.studyhub-panel.dark-mode .studyhub-tab {
  color: #9ca3af !important;
}

.studyhub-tab:hover {
  color: #4b5563 !important;
  background: #f3f4f6 !important;
}

.studyhub-panel.dark-mode .studyhub-tab:hover {
  color: #d1d5db !important;
  background: #374151 !important;
}

.studyhub-tab.active {
  color: #667eea !important;
  background: #eef2ff !important;
  font-weight: 600 !important;
}

.studyhub-panel.dark-mode .studyhub-tab.active {
  color: #a78bfa !important;
  background: #3730a3 !important;
}

/* 内容区 */
.studyhub-body {
  flex: 1 !important;
  overflow-y: auto !important;
  padding: 16px !important;
  scrollbar-width: thin !important;
  scrollbar-color: #d1d5db transparent !important;
}

.studyhub-body::-webkit-scrollbar {
  width: 4px !important;
}

.studyhub-body::-webkit-scrollbar-thumb {
  background: #d1d5db !important;
  border-radius: 2px !important;
}

/* 场景标题 */
.studyhub-scene-title {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  color: #111827 !important;
  margin-bottom: 4px !important;
}

.studyhub-panel.dark-mode .studyhub-scene-title {
  color: #f9fafb !important;
}

.studyhub-scene-subtitle {
  font-size: 12px !important;
  color: #6b7280 !important;
  margin-bottom: 16px !important;
}

.studyhub-panel.dark-mode .studyhub-scene-subtitle {
  color: #9ca3af !important;
}

/* 推荐列表 */
.studyhub-section {
  margin-bottom: 16px !important;
}

.studyhub-section-title {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #374151 !important;
  margin-bottom: 8px !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
}

.studyhub-panel.dark-mode .studyhub-section-title {
  color: #d1d5db !important;
}

.studyhub-rec-item {
  display: flex !important;
  align-items: flex-start !important;
  gap: 10px !important;
  padding: 10px 12px !important;
  background: #f9fafb !important;
  border-radius: 8px !important;
  margin-bottom: 8px !important;
  cursor: pointer !important;
  transition: all 0.2s !important;
  text-decoration: none !important;
}

.studyhub-panel.dark-mode .studyhub-rec-item {
  background: #1f2937 !important;
}

.studyhub-rec-item:hover {
  background: #f3f4f6 !important;
  transform: translateX(2px) !important;
}

.studyhub-panel.dark-mode .studyhub-rec-item:hover {
  background: #374151 !important;
}

.studyhub-rec-icon {
  font-size: 20px !important;
  flex-shrink: 0 !important;
}

.studyhub-rec-content {
  flex: 1 !important;
  min-width: 0 !important;
}

.studyhub-rec-name {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #111827 !important;
  margin-bottom: 2px !important;
}

.studyhub-panel.dark-mode .studyhub-rec-name {
  color: #f9fafb !important;
}

.studyhub-rec-desc {
  font-size: 11px !important;
  color: #6b7280 !important;
  line-height: 1.4 !important;
}

.studyhub-panel.dark-mode .studyhub-rec-desc {
  color: #9ca3af !important;
}

/* 提示 */
.studyhub-tip {
  display: flex !important;
  align-items: flex-start !important;
  gap: 8px !important;
  padding: 10px 12px !important;
  background: #fef3c7 !important;
  border-radius: 8px !important;
  margin-bottom: 16px !important;
  font-size: 12px !important;
  color: #92400e !important;
  line-height: 1.5 !important;
}

.studyhub-panel.dark-mode .studyhub-tip {
  background: #451a03 !important;
  color: #fcd34d !important;
}

.studyhub-tip-icon {
  font-size: 14px !important;
  flex-shrink: 0 !important;
  margin-top: 1px !important;
}

/* 来源筛选 */
.studyhub-filter-section {
  border-top: 1px solid #e5e7eb !important;
  padding-top: 16px !important;
  margin-top: 16px !important;
}

.studyhub-panel.dark-mode .studyhub-filter-section {
  border-top-color: #374151 !important;
}

.studyhub-filter-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  margin-bottom: 10px !important;
}

.studyhub-filter-title {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #374151 !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
}

.studyhub-panel.dark-mode .studyhub-filter-title {
  color: #d1d5db !important;
}

.studyhub-filter-reset {
  font-size: 11px !important;
  color: #667eea !important;
  cursor: pointer !important;
  background: none !important;
  border: none !important;
}

.studyhub-panel.dark-mode .studyhub-filter-reset {
  color: #a78bfa !important;
}

.studyhub-filter-list {
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
}

.studyhub-filter-item {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 6px 8px !important;
  border-radius: 6px !important;
  cursor: pointer !important;
  transition: background 0.15s !important;
}

.studyhub-filter-item:hover {
  background: #f3f4f6 !important;
}

.studyhub-panel.dark-mode .studyhub-filter-item:hover {
  background: #374151 !important;
}

.studyhub-filter-checkbox {
  width: 16px !important;
  height: 16px !important;
  border: 2px solid #d1d5db !important;
  border-radius: 4px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  cursor: pointer !important;
  transition: all 0.2s !important;
}

.studyhub-filter-checkbox.checked {
  background: #667eea !important;
  border-color: #667eea !important;
}

.studyhub-panel.dark-mode .studyhub-filter-checkbox.checked {
  background: #8b5cf6 !important;
  border-color: #8b5cf6 !important;
}

.studyhub-filter-checkbox.checked::after {
  content: '✓' !important;
  color: white !important;
  font-size: 11px !important;
  font-weight: bold !important;
}

.studyhub-filter-icon {
  font-size: 14px !important;
}

.studyhub-filter-name {
  font-size: 12px !important;
  color: #374151 !important;
  flex: 1 !important;
}

.studyhub-panel.dark-mode .studyhub-filter-name {
  color: #d1d5db !important;
}

.studyhub-filter-memory {
  width: 6px !important;
  height: 6px !important;
  border-radius: 50% !important;
  background: #9ca3af !important;
  flex-shrink: 0 !important;
}

/* 记忆标记 tooltip */
.studyhub-filter-item[data-memory="true"] .studyhub-filter-memory {
  background: #667eea !important;
}

/* 应用筛选按钮 */
.studyhub-apply-btn {
  width: 100% !important;
  padding: 10px !important;
  margin-top: 12px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: opacity 0.2s !important;
}

.studyhub-apply-btn:hover {
  opacity: 0.9 !important;
}

/* AI 分析区域 */
.studyhub-ai-section {
  border-top: 1px solid #e5e7eb !important;
  padding-top: 16px !important;
  margin-top: 16px !important;
}

.studyhub-panel.dark-mode .studyhub-ai-section {
  border-top-color: #374151 !important;
}

.studyhub-ai-title {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #374151 !important;
  margin-bottom: 8px !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
}

.studyhub-panel.dark-mode .studyhub-ai-title {
  color: #d1d5db !important;
}

.studyhub-ai-content {
  font-size: 12px !important;
  color: #4b5563 !important;
  line-height: 1.6 !important;
  padding: 10px 12px !important;
  background: #f3f4f6 !important;
  border-radius: 8px !important;
}

.studyhub-panel.dark-mode .studyhub-ai-content {
  color: #d1d5db !important;
  background: #1f2937 !important;
}

/* 关联场景 */
.studyhub-related {
  margin-top: 12px !important;
  padding-top: 12px !important;
  border-top: 1px dashed #e5e7eb !important;
}

.studyhub-panel.dark-mode .studyhub-related {
  border-top-color: #374151 !important;
}

.studyhub-related-title {
  font-size: 11px !important;
  color: #9ca3af !important;
  margin-bottom: 8px !important;
}

.studyhub-related-item {
  display: inline-flex !important;
  align-items: center !important;
  gap: 4px !important;
  padding: 4px 10px !important;
  background: #f3f4f6 !important;
  border-radius: 6px !important;
  font-size: 11px !important;
  color: #4b5563 !important;
  cursor: pointer !important;
  margin-right: 6px !important;
  margin-bottom: 6px !important;
  transition: background 0.2s !important;
}

.studyhub-panel.dark-mode .studyhub-related-item {
  background: #374151 !important;
  color: #d1d5db !important;
}

.studyhub-related-item:hover {
  background: #e5e7eb !important;
}

.studyhub-panel.dark-mode .studyhub-related-item:hover {
  background: #4b5563 !important;
}

/* 小圆点（关闭后恢复） */
.studyhub-dot {
  position: fixed !important;
  bottom: 24px !important;
  right: 24px !important;
  width: 48px !important;
  height: 48px !important;
  border-radius: 50% !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 20px !important;
  cursor: pointer !important;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4) !important;
  z-index: 999999 !important;
  transition: transform 0.2s, box-shadow 0.2s !important;
}

.studyhub-dot:hover {
  transform: scale(1.1) !important;
  box-shadow: 0 6px 24px rgba(102, 126, 234, 0.5) !important;
}

/* 首次引导 */
.studyhub-guide {
  position: absolute !important;
  bottom: -36px !important;
  left: 0 !important;
  right: 0 !important;
  text-align: center !important;
  font-size: 11px !important;
  color: #9ca3af !important;
  padding: 8px !important;
  background: #f9fafb !important;
  border-radius: 0 0 12px 12px !important;
}

.studyhub-panel.dark-mode .studyhub-guide {
  background: #1f2937 !important;
  color: #6b7280 !important;
}

/* 动画 */
@keyframes studyhub-slideIn {
  from {
    transform: translateX(100px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.studyhub-panel.animating {
  animation: studyhub-slideIn 0.3s ease !important;
}

/* 拖拽中 */
.studyhub-panel.dragging {
  transition: none !important;
  cursor: move !important;
}
`;
  }

})();
