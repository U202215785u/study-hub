// Study Hub Bing 搜索助手浮窗 v3.0
// 彻底重构：修复所有交互bug，简化逻辑，增强健壮性

(function() {
  'use strict';

  // ==================== 配置 ====================
  const CONFIG = {
    STORAGE_STATE: 'studyhub_v3_state',
    STORAGE_PREFS: 'studyhub_assistant_prefs',
    PANEL_WIDTH: 360,
    GUIDE_MAX: 3,
  };

  // ==================== 状态（全部放在 app 对象里，避免全局变量污染）====================
  const app = {
    panel: null,          // 面板 DOM
    dot: null,            // 小圆点 DOM
    shadow: null,         // Shadow Root
    scene: null,          // 当前场景
    rules: null,          // 场景规则
    query: '',            // 当前搜索词
    pinned: false,        // 默认不固定，随时可拖拽
    collapsed: false,     // 是否收起
    closed: false,        // 是否关闭（显示小圆点）
    dragging: false,      // 是否拖拽中
    dragStart: { x: 0, y: 0, panelX: 0, panelY: 0 },
    guideCount: 0,
    initialized: false,
  };

  // ==================== 初始化 ====================

  async function main() {
    if (app.initialized) return;
    if (!isBingSearch()) return;

    console.log('[StudyHub] 初始化...');
    app.initialized = true;

    // 解析 URL
    const params = new URLSearchParams(location.search);
    app.query = params.get('q') || '';

    // 加载数据
    await loadSceneRules();
    await loadState();
    await loadPrefs();

    // 匹配场景
    const urlScene = params.get('scene');
    const isFilterRefresh = app.query.includes('site:');
    restoreFilterState(isFilterRefresh, urlScene);

    // 渲染
    if (app.closed) {
      showDot();
    } else {
      showPanel();
    }

    // 监听
    watchUrl();
    bindGlobalEvents();
  }

  // ==================== 数据加载 ====================

  async function loadSceneRules() {
    try {
      const url = chrome.runtime.getURL('data/scene-rules.json');
      const res = await fetch(url);
      app.rules = await res.json();
    } catch (e) {
      app.rules = getBuiltinRules();
    }
  }

  async function loadState() {
    try {
      const data = await chrome.storage.local.get([CONFIG.STORAGE_STATE]);
      const s = data[CONFIG.STORAGE_STATE];
      if (s) {
        app.pinned = s.pinned === true;
        app.collapsed = !!s.collapsed;
        app.closed = !!s.closed;
        // 位置在 showPanel 中恢复
      }
    } catch (e) {}
  }

  async function saveState() {
    try {
      const state = {
        pinned: app.pinned,
        collapsed: app.collapsed,
        closed: app.closed,
      };
      if (!app.pinned && app.panel) {
        const rect = app.panel.getBoundingClientRect();
        state.x = rect.left;
        state.y = rect.top;
      }
      await chrome.storage.local.set({ [CONFIG.STORAGE_STATE]: state });
    } catch (e) {}
  }

  async function loadPrefs() {
    try {
      const data = await chrome.storage.sync.get([CONFIG.STORAGE_PREFS]);
      const p = data[CONFIG.STORAGE_PREFS] || {};
      app.guideCount = p.guideCount || 0;

      // 恢复当前场景的勾选状态
      if (p.sources && app.scene) {
        const saved = p.sources[app.scene.id];
        if (saved) {
          app.scene.sources.forEach(src => {
            const key = src.domain || src.name;
            if (saved.includes(key)) {
              src.checked = true;
              src.fromMemory = true;
            }
          });
        }
      }
    } catch (e) {}
  }

  async function savePrefs() {
    try {
      const data = await chrome.storage.sync.get([CONFIG.STORAGE_PREFS]);
      const p = data[CONFIG.STORAGE_PREFS] || {};
      if (!p.sources) p.sources = {};
      if (app.scene) {
        p.sources[app.scene.id] = app.scene.sources
          .filter(s => s.checked)
          .map(s => s.domain || s.name);
      }
      p.guideCount = app.guideCount;
      await chrome.storage.sync.set({ [CONFIG.STORAGE_PREFS]: p });
    } catch (e) {}
  }

  // ==================== 场景匹配 ====================

  function restoreFilterState(isFilterRefresh, urlScene) {
    // sessionStorage 恢复
    const raw = sessionStorage.getItem('studyhub_filter_state');
    let restoredSources = null;
    let targetScene = urlScene;

    if (raw) {
      try {
        const fs = JSON.parse(raw);
        if (Date.now() - fs.timestamp < 5 * 60 * 1000) {
          if (isFilterRefresh && fs.sceneId) targetScene = fs.sceneId;
          restoredSources = fs.checkedSources || [];
        } else {
          sessionStorage.removeItem('studyhub_filter_state');
        }
      } catch (e) {}
    }

    // 确定场景
    app.scene = targetScene
      ? app.rules.scenes.find(s => s.id === targetScene)
      : matchScene(app.query);
    if (!app.scene) {
      app.scene = app.rules.scenes.find(s => s.id === app.rules.defaultScene);
    }

    // 恢复勾选
    if (restoredSources) {
      app.scene.sources.forEach(src => {
        const key = src.domain || src.name;
        if (restoredSources.includes(key)) {
          src.checked = true;
          src.fromMemory = true;
        }
      });
    }
  }

  function matchScene(query) {
    if (!query) return null;
    const q = query.toLowerCase();
    for (const s of app.rules.scenes) {
      for (const kw of s.keywords) {
        if (q.includes(kw.toLowerCase())) return s;
      }
    }
    return null;
  }

  // ==================== 面板生命周期 ====================

  function showPanel() {
    cleanupPanel();
    cleanupDot();

    const host = document.createElement('div');
    host.id = 'studyhub-assistant-host';
    document.body.appendChild(host);

    app.shadow = host.attachShadow({ mode: 'open' });

    // CSS
    const style = document.createElement('style');
    style.textContent = getCSS();
    app.shadow.appendChild(style);

    // 面板
    app.panel = document.createElement('div');
    app.panel.className = 'sh-panel' + (app.collapsed ? ' collapsed' : '') + (isDark() ? ' dark' : '');
    app.panel.innerHTML = renderPanel();
    app.shadow.appendChild(app.panel);

    // 恢复位置
    restorePosition();

    // 事件
    bindPanelEvents();

    // 引导
    if (app.guideCount < CONFIG.GUIDE_MAX) {
      showGuide();
      app.guideCount++;
      savePrefs();
    }

    adjustBing(true);
    app.closed = false;
    saveState();
  }

  function cleanupPanel() {
    const host = document.getElementById('studyhub-assistant-host');
    if (host) {
      host.remove();
      app.panel = null;
      app.shadow = null;
    }
  }

  function showDot() {
    cleanupDot();
    app.dot = document.createElement('div');
    app.dot.className = 'sh-dot';
    app.dot.innerHTML = '\u2728'; // ✨
    app.dot.title = 'Study Hub';
    app.dot.addEventListener('click', () => {
      cleanupDot();
      showPanel();
    });
    document.body.appendChild(app.dot);
    adjustBing(false);
  }

  function cleanupDot() {
    if (app.dot) {
      app.dot.remove();
      app.dot = null;
    }
  }

  function closePanel() {
    if (app.panel) {
      app.panel.style.transform = 'translateX(120%)';
      app.panel.style.opacity = '0';
      setTimeout(() => {
        cleanupPanel();
        showDot();
      }, 250);
    }
    app.closed = true;
    app.collapsed = false;
    saveState();
  }

  // ==================== 位置与拖拽 ====================

  function restorePosition() {
    if (!app.panel) return;
    if (app.pinned) {
      app.panel.style.top = '72px';
      app.panel.style.right = '16px';
      app.panel.style.left = 'auto';
    } else {
      // 非固定模式：如果没有设置过位置，默认也在右上角
      if (!app.panel.style.left || app.panel.style.left === 'auto') {
        app.panel.style.top = '72px';
        app.panel.style.right = '16px';
      }
    }
  }

  function bindPanelEvents() {
    if (!app.shadow) return;

    // 事件委托：所有点击走这一个处理器
    app.shadow.addEventListener('click', handlePanelClick);

    // 拖拽：只在 header 上触发
    const header = app.shadow.querySelector('.sh-header');
    if (header) {
      header.addEventListener('mousedown', startDrag);
    }
  }

  function handlePanelClick(e) {
    const t = e.target;

    // 关闭
    if (t.closest('.sh-btn-close')) {
      closePanel();
      return;
    }

    // 收起/展开
    if (t.closest('.sh-btn-collapse')) {
      toggleCollapse();
      return;
    }

    // 固定/取消固定
    if (t.closest('.sh-btn-pin')) {
      togglePin();
      return;
    }

    // 场景切换
    const tab = t.closest('.sh-tab');
    if (tab) {
      const sid = tab.dataset.scene;
      if (sid && sid !== app.scene.id) switchScene(sid);
      return;
    }

    // 关联场景
    const rel = t.closest('.sh-related-item');
    if (rel) {
      const sid = rel.dataset.scene;
      if (sid && sid !== app.scene.id) switchScene(sid);
      return;
    }

    // 来源勾选
    const filter = t.closest('.sh-filter-item');
    if (filter) {
      toggleSource(filter);
      return;
    }

    // 恢复默认
    if (t.closest('.sh-btn-reset')) {
      resetSources();
      return;
    }

    // 应用筛选
    if (t.closest('.sh-btn-apply')) {
      applyFilter();
      return;
    }

    // AI 折叠
    if (t.closest('.sh-ai-header')) {
      const section = app.shadow.querySelector('.sh-ai-section');
      if (section) section.classList.toggle('collapsed');
    }
  }

  function startDrag(e) {
    if (e.button !== 0) return;
    e.preventDefault();

    app.dragging = true;
    const rect = app.panel.getBoundingClientRect();
    app.dragStart = {
      x: e.clientX,
      y: e.clientY,
      panelX: rect.left,
      panelY: rect.top,
    };
    app.panel.classList.add('dragging');
  }

  function onDragMove(e) {
    if (!app.dragging || !app.panel) return;
    e.preventDefault();

    const dx = e.clientX - app.dragStart.x;
    const dy = e.clientY - app.dragStart.y;

    let nx = app.dragStart.panelX + dx;
    let ny = app.dragStart.panelY + dy;

    // 边界限制
    const maxX = window.innerWidth - app.panel.offsetWidth;
    const maxY = window.innerHeight - app.panel.offsetHeight;
    nx = Math.max(0, Math.min(nx, maxX));
    ny = Math.max(0, Math.min(ny, maxY));

    app.panel.style.left = nx + 'px';
    app.panel.style.top = ny + 'px';
    app.panel.style.right = 'auto';
  }

  function onDragEnd() {
    if (!app.dragging) return;
    app.dragging = false;
    if (app.panel) {
      app.panel.classList.remove('dragging');
      saveState();
    }
  }

  // ==================== 面板操作 ====================

  function toggleCollapse() {
    app.collapsed = !app.collapsed;
    if (app.panel) {
      app.panel.classList.toggle('collapsed', app.collapsed);
    }
    // 收起后面板宽度变窄，展开后恢复宽度并调整Bing布局
    if (app.collapsed) {
      // 收起：只留窄边距，恢复Bing右侧栏
      adjustBing(false);
    } else {
      // 展开：隐藏Bing右侧栏，给面板留空间
      adjustBing(true);
    }
    saveState();
  }

  function togglePin() {
    app.pinned = !app.pinned;
    updatePinUI();
    saveState();
  }

  function updatePinUI() {
    if (!app.shadow) return;
    const btn = app.shadow.querySelector('.sh-btn-pin');
    if (btn) {
      btn.textContent = app.pinned ? '\ud83d\udccc' : '\ud83d\udccd';
      btn.title = app.pinned ? '\u5df2\u56fa\u5b9a\uff08\u70b9\u51fb\u53d6\u6d88\u56fa\u5b9a\uff0c\u53ef\u62d6\u62fd\uff09' : '\u672a\u56fa\u5b9a\uff08\u70b9\u51fb\u56fa\u5b9a\uff09';
    }
    if (app.panel) {
      app.panel.style.cursor = app.pinned ? 'default' : 'move';
      if (app.pinned) restorePosition();
    }
  }

  function switchScene(sceneId) {
    const newScene = app.rules.scenes.find(s => s.id === sceneId);
    if (!newScene || newScene.id === app.scene.id) return;
    app.scene = newScene;

    loadPrefs().then(() => {
      if (!app.shadow || !app.panel) return;

      // 局部更新：tabs + body
      const tabs = app.shadow.querySelector('.sh-tabs');
      const body = app.shadow.querySelector('.sh-body');

      if (tabs) {
        tabs.innerHTML = renderTabs();
      }
      if (body) {
        body.innerHTML = renderBody();
      }

      // 更新 URL
      const url = new URL(location.href);
      url.searchParams.set('scene', sceneId);
      history.replaceState({}, '', url);

      savePrefs();
    });
  }

  // ==================== 来源筛选 ====================

  function toggleSource(item) {
    const cb = item.querySelector('.sh-checkbox');
    const name = item.dataset.source;
    if (!cb) return;

    cb.classList.toggle('checked');
    const checked = cb.classList.contains('checked');

    const src = app.scene.sources.find(s => (s.domain || s.name) === name);
    if (src) {
      src.checked = checked;
      src.fromMemory = false;
    }
    savePrefs();
    updateAIHint();
  }

  function resetSources() {
    app.scene.sources.forEach(s => { s.checked = false; s.fromMemory = false; });
    if (app.shadow) {
      app.shadow.querySelectorAll('.sh-checkbox').forEach(cb => cb.classList.remove('checked'));
      app.shadow.querySelectorAll('.sh-memory').forEach(m => m.remove());
    }
    savePrefs();
    updateAIHint();
  }

  function updateAIHint() {
    if (!app.shadow) return;
    const content = app.shadow.querySelector('.sh-ai-content');
    const section = app.shadow.querySelector('.sh-ai-section');
    if (!content || !section) return;

    const checked = app.scene.sources.filter(s => s.checked).length;
    if (checked === 0) {
      content.innerHTML = '<div class="sh-ai-hint"><span>\u2728</span><span>\u52fe\u9009\u6765\u6e90\u5e76\u70b9\u51fb"\u5e94\u7528\u7b5b\u9009"\uff0cAI \u5c06\u5206\u6790\u641c\u7d22\u7ed3\u679c</span></div>';
      section.classList.remove('collapsed');
    } else {
      content.innerHTML = `<div class="sh-ai-hint"><span>\u2705</span><span>\u5df2\u52fe\u9009 ${checked} \u4e2a\u6765\u6e90</span></div>`;
      section.classList.add('collapsed');
    }
  }

  function applyFilter() {
    const checked = app.scene.sources.filter(s => s.checked);
    if (checked.length === 0) {
      if (app.shadow) {
        const content = app.shadow.querySelector('.sh-ai-content');
        const section = app.shadow.querySelector('.sh-ai-section');
        if (content) content.innerHTML = '<div class="sh-ai-hint"><span>\u26a0\ufe0f</span><span>\u8bf7\u5148\u52fe\u9009\u81f3\u5c11\u4e00\u4e2a\u6765\u6e90</span></div>';
        if (section) section.classList.remove('collapsed');
      }
      return;
    }

    const filters = checked.filter(s => s.domain).map(s => 'site:' + s.domain).join(' OR ');
    const url = new URL(location.href);
    let q = app.query;
    if (filters) {
      if (q.includes('site:')) q = q.replace(/\s*site:\S+(\s+OR\s+site:\S+)*/g, '').trim();
      q = q + ' ' + filters;
    }
    url.searchParams.set('q', q);
    url.searchParams.set('scene', app.scene.id);

    sessionStorage.setItem('studyhub_filter_state', JSON.stringify({
      sceneId: app.scene.id,
      checkedSources: checked.map(s => s.domain || s.name),
      timestamp: Date.now(),
    }));

    location.href = url.toString();
  }

  // ==================== Bing 布局 ====================

  function adjustBing(panelVisible) {
    const kp = document.querySelector('#b_context');
    const results = document.querySelector('#b_results');

    if (panelVisible) {
      // 面板展开：隐藏Bing右侧栏，给面板留空间
      if (kp) kp.style.display = 'none';
      if (results) results.style.marginRight = '376px';
    } else {
      // 面板收起或关闭：恢复Bing右侧栏
      if (kp) kp.style.display = '';
      if (results) results.style.marginRight = '';
    }

    if (results) results.style.transition = 'margin-right 0.25s ease';
  }

  // ==================== URL 监听 ====================

  function watchUrl() {
    let last = location.href;

    const check = () => {
      const current = location.href;
      if (current === last) return;
      last = current;

      if (!isBingSearch()) {
        cleanupAll();
        return;
      }

      const newQuery = new URLSearchParams(location.search).get('q') || '';
      if (newQuery !== app.query) {
        app.query = newQuery;
        sessionStorage.removeItem('studyhub_filter_state');

        const matched = matchScene(app.query);
        if (matched && matched.id !== app.scene.id) {
          app.scene = matched;
          loadPrefs().then(() => {
            if (app.shadow && app.panel) {
              const tabs = app.shadow.querySelector('.sh-tabs');
              const body = app.shadow.querySelector('.sh-body');
              if (tabs) tabs.innerHTML = renderTabs();
              if (body) body.innerHTML = renderBody();
            }
          });
        }
      }
    };

    // 多种方式监听
    window.addEventListener('popstate', check);
    window.addEventListener('hashchange', check);

    // Bing 用 history API  pushState，需要拦截
    const originalPush = history.pushState;
    const originalReplace = history.replaceState;
    history.pushState = function(...args) {
      originalPush.apply(this, args);
      setTimeout(check, 50);
    };
    history.replaceState = function(...args) {
      originalReplace.apply(this, args);
      setTimeout(check, 50);
    };
  }

  // ==================== 全局事件 ====================

  function bindGlobalEvents() {
    document.addEventListener('mousemove', onDragMove);
    document.addEventListener('mouseup', onDragEnd);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && app.panel && !app.closed) {
        closePanel();
      }
    });
  }

  function cleanupAll() {
    cleanupPanel();
    cleanupDot();
    adjustBing(false);
  }

  // ==================== 渲染 ====================

  function renderPanel() {
    return `
      <div class="sh-header">
        <div class="sh-header-left">
          <span>\ud83e\udd16</span>
          <span class="sh-header-text">Study Hub</span>
        </div>
        <div class="sh-header-right">
          <button class="sh-btn sh-btn-collapse" title="${app.collapsed ? '\u5c55\u5f00' : '\u6536\u8d77'}">${app.collapsed ? '\u25b6' : '\u25c0'}</button>
          <button class="sh-btn sh-btn-pin" title="${app.pinned ? '\u5df2\u56fa\u5b9a' : '\u672a\u56fa\u5b9a'}">${app.pinned ? '\ud83d\udccc' : '\ud83d\udccd'}</button>
          <button class="sh-btn sh-btn-close" title="\u5173\u95ed">\u2715</button>
        </div>
      </div>
      <div class="sh-tabs">${renderTabs()}</div>
      <div class="sh-body">${renderBody()}</div>
    `;
  }

  function renderTabs() {
    return app.rules.scenes.map(s => `
      <button class="sh-tab ${s.id === app.scene.id ? 'active' : ''}" data-scene="${s.id}">
        ${s.icon} ${s.name}
      </button>
    `).join('');
  }

  function renderBody() {
    const recs = app.scene.recommendations?.length
      ? app.scene.recommendations.map(r => `
        <a class="sh-rec" href="${r.url}" target="_blank" rel="noopener">
          <span class="sh-rec-icon">\ud83d\udd17</span>
          <div class="sh-rec-body">
            <div class="sh-rec-name">${r.name}</div>
            <div class="sh-rec-desc">${r.desc}</div>
          </div>
        </a>
      `).join('')
      : `<div class="sh-empty"><div class="sh-empty-icon">\ud83d\udd0d</div><div class="sh-empty-title">\u6682\u65e0\u63a8\u8350</div><div class="sh-empty-desc">\u5207\u6362\u573a\u666f\u6216\u7b5b\u9009\u6765\u6e90</div></div>`;

    const tips = app.scene.tips.map(t => `
      <div class="sh-tip"><span>\u26a0\ufe0f</span><span>${t}</span></div>
    `).join('');

    const sources = app.scene.sources.map(s => `
      <div class="sh-filter-item" data-source="${s.domain || s.name}">
        <div class="sh-checkbox ${s.checked ? 'checked' : ''}"></div>
        <span class="sh-filter-icon">${s.icon}</span>
        <span class="sh-filter-name">${s.name}</span>
        ${s.fromMemory ? '<span class="sh-memory" title="\u8bb0\u5fc6\u4e2d"></span>' : ''}
      </div>
    `).join('');

    const related = app.rules.scenes
      .filter(s => s.id !== app.scene.id)
      .slice(0, 2)
      .map(s => `<span class="sh-related-item" data-scene="${s.id}">${s.icon} ${s.name}</span>`)
      .join('');

    const checkedCount = app.scene.sources.filter(s => s.checked).length;
    const aiCollapsed = checkedCount > 0;

    return `
      <div class="sh-scene-title"><span>${app.scene.icon}</span><span>${app.scene.name}</span></div>
      <div class="sh-scene-sub">\u641c\u7d22\uff1a${escape(app.query)}</div>
      ${tips}
      <div class="sh-section">
        <div class="sh-section-title">\u2b50 \u63a8\u8350</div>
        ${recs}
      </div>
      <div class="sh-filter-section">
        <div class="sh-filter-header">
          <div class="sh-filter-title">\u2699\ufe0f \u6765\u6e90\u7b5b\u9009</div>
          <button class="sh-btn-reset">\u6062\u590d\u9ed8\u8ba4</button>
        </div>
        <div class="sh-filter-list">${sources}</div>
        <button class="sh-btn-apply">\u5e94\u7528\u7b5b\u9009\u5e76\u641c\u7d22</button>
      </div>
      <div class="sh-ai-section ${aiCollapsed ? 'collapsed' : ''}">
        <div class="sh-ai-header">
          <span class="sh-ai-title">\ud83e\udd16 AI \u5206\u6790</span>
          <span class="sh-ai-arrow">\u25bc</span>
        </div>
        <div class="sh-ai-content">
          <div class="sh-ai-hint">
            <span>${checkedCount > 0 ? '\u2705' : '\u2728'}</span>
            <span>${checkedCount > 0 ? `\u5df2\u52fe\u9009 ${checkedCount} \u4e2a\u6765\u6e90` : '\u52fe\u9009\u6765\u6e90\u5e76\u70b9\u51fb"\u5e94\u7528\u7b5b\u9009"\uff0cAI \u5c06\u5206\u6790\u641c\u7d22\u7ed3\u679c'}</span>
          </div>
        </div>
      </div>
      ${related ? `<div class="sh-related"><div class="sh-related-title">\u4f60\u53ef\u80fd\u4e5f\u60f3\u770b</div>${related}</div>` : ''}
    `;
  }

  function showGuide() {
    if (!app.shadow) return;
    const guide = document.createElement('div');
    guide.className = 'sh-guide';
    guide.textContent = 'Study Hub \u00b7 \u5207\u6362\u573a\u666f\u3001\u7b5b\u9009\u6765\u6e90\uff0cESC \u5173\u95ed';
    app.shadow.querySelector('.sh-panel').appendChild(guide);
    setTimeout(() => {
      guide.style.opacity = '0';
      guide.style.transition = 'opacity 0.5s';
      setTimeout(() => guide.remove(), 500);
    }, 5000);
  }

  // ==================== CSS ====================

  function getCSS() {
    return `
      .sh-panel {
        position: fixed; top: 72px; right: 16px;
        width: 360px; max-height: calc(100vh - 100px);
        background: #fff; border-radius: 12px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
        overflow: hidden; display: flex; flex-direction: column;
        z-index: 999999;
        transition: transform 0.25s ease, opacity 0.25s ease, width 0.25s ease;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      .sh-panel.collapsed { width: 60px; overflow: hidden; }
      .sh-panel.collapsed .sh-body, .sh-panel.collapsed .sh-tabs { display: none; }
      .sh-panel.collapsed .sh-header-text { display: none; }
      .sh-panel.dragging { transition: none; }
      .sh-panel.dark { background: #1a1a2e; }

      .sh-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 16px; flex-shrink: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; font-size: 14px; font-weight: 600;
        user-select: none;
      }
      .sh-header-left { display: flex; align-items: center; gap: 8px; }
      .sh-header-right { display: flex; align-items: center; gap: 4px; }
      .sh-btn {
        width: 28px; height: 28px; border-radius: 6px;
        background: rgba(255,255,255,0.15); color: white;
        border: none; cursor: pointer; font-size: 13px;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.2s;
      }
      .sh-btn:hover { background: rgba(255,255,255,0.3); }

      .sh-tabs {
        display: flex; gap: 4px; padding: 8px 12px 0;
        border-bottom: 1px solid #e5e7eb; overflow-x: auto; flex-shrink: 0;
        scrollbar-width: none;
      }
      .sh-tabs::-webkit-scrollbar { display: none; }
      .sh-tab {
        padding: 6px 12px; border-radius: 8px 8px 0 0;
        font-size: 12px; font-weight: 500; color: #6b7280;
        cursor: pointer; white-space: nowrap; border: none;
        background: transparent; transition: all 0.2s;
      }
      .sh-tab:hover { color: #4b5563; background: #f3f4f6; }
      .sh-tab.active { color: #667eea; background: #eef2ff; font-weight: 600; }

      .sh-body { flex: 1; overflow-y: auto; padding: 16px; }
      .sh-scene-title { font-size: 16px; font-weight: 700; color: #111; margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }
      .sh-scene-sub { font-size: 12px; color: #6b7280; margin-bottom: 16px; }
      .sh-tip { display: flex; align-items: flex-start; gap: 8px; padding: 10px 12px; background: #fef3c7; border-radius: 8px; margin-bottom: 16px; font-size: 12px; color: #92400e; }
      .sh-section { margin-bottom: 16px; }
      .sh-section-title { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px; }
      .sh-rec { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; background: #f9fafb; border-radius: 8px; margin-bottom: 8px; text-decoration: none; color: inherit; transition: all 0.2s; }
      .sh-rec:hover { background: #f3f4f6; transform: translateX(2px); }
      .sh-rec-name { font-size: 13px; font-weight: 600; color: #111; }
      .sh-rec-desc { font-size: 11px; color: #6b7280; }
      .sh-empty { text-align: center; padding: 20px 12px; color: #9ca3af; }
      .sh-empty-icon { font-size: 28px; margin-bottom: 8px; }

      .sh-filter-section { border-top: 1px solid #e5e7eb; padding-top: 16px; margin-top: 16px; }
      .sh-filter-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
      .sh-filter-title { font-size: 13px; font-weight: 600; color: #374151; }
      .sh-btn-reset { font-size: 11px; color: #667eea; background: none; border: none; cursor: pointer; }
      .sh-filter-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.15s; }
      .sh-filter-item:hover { background: #f3f4f6; }
      .sh-checkbox { width: 16px; height: 16px; border: 2px solid #d1d5db; border-radius: 4px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
      .sh-checkbox.checked { background: #667eea; border-color: #667eea; }
      .sh-checkbox.checked::after { content: '\\2713'; color: white; font-size: 11px; font-weight: bold; }
      .sh-filter-name { font-size: 12px; color: #374151; flex: 1; }
      .sh-memory { width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; }
      .sh-btn-apply { width: 100%; padding: 10px; margin-top: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
      .sh-btn-apply:hover { opacity: 0.9; }

      .sh-ai-section { border-top: 1px solid #e5e7eb; padding-top: 16px; margin-top: 16px; }
      .sh-ai-section.collapsed .sh-ai-content { display: none; }
      .sh-ai-section.collapsed .sh-ai-arrow { transform: rotate(-90deg); }
      .sh-ai-header { display: flex; align-items: center; justify-content: space-between; cursor: pointer; padding: 4px 0; }
      .sh-ai-title { font-size: 13px; font-weight: 600; color: #374151; }
      .sh-ai-arrow { font-size: 11px; color: #9ca3af; transition: transform 0.2s; }
      .sh-ai-content { font-size: 12px; color: #4b5563; padding: 10px 12px; background: #f3f4f6; border-radius: 8px; margin-top: 8px; }
      .sh-ai-hint { display: flex; align-items: center; gap: 8px; color: #6b7280; }

      .sh-related { margin-top: 12px; padding-top: 12px; border-top: 1px dashed #e5e7eb; }
      .sh-related-title { font-size: 11px; color: #9ca3af; margin-bottom: 8px; }
      .sh-related-item { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #f3f4f6; border-radius: 6px; font-size: 11px; color: #4b5563; cursor: pointer; margin-right: 6px; transition: background 0.2s; }
      .sh-related-item:hover { background: #e5e7eb; }

      .sh-dot {
        position: fixed; bottom: 24px; right: 24px;
        width: 48px; height: 48px; border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; display: flex; align-items: center; justify-content: center;
        font-size: 20px; cursor: pointer;
        box-shadow: 0 4px 16px rgba(102,126,234,0.4); z-index: 999999;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      .sh-dot:hover { transform: scale(1.1); box-shadow: 0 6px 24px rgba(102,126,234,0.5); }

      .sh-guide { position: absolute; bottom: -36px; left: 0; right: 0; text-align: center; font-size: 11px; color: #9ca3af; padding: 8px; background: #f9fafb; border-radius: 0 0 12px 12px; }

      @keyframes sh-slideIn { from { transform: translateX(100px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
      .sh-panel { animation: sh-slideIn 0.3s ease; }
    `;
  }

  // ==================== 工具函数 ====================

  function isBingSearch() {
    return location.hostname === 'www.bing.com' && location.pathname === '/search';
  }

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ||
           window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function escape(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  function getBuiltinRules() {
    return {
      scenes: [
        {
          id: 'tool_find', name: '\u5de5\u5177\u67e5\u627e', icon: '\ud83d\udee0\ufe0f',
          keywords: ['\u5de5\u5177', '\u6263\u56fe', '\u538b\u7f29', '\u8f6c\u6362', '\u751f\u6210\u5668', '\u7f16\u8f91\u5668', '\u8ba1\u7b97\u5668', '\u7ffb\u8bd1', '\u4e0b\u8f7d', '\u89e3\u6790', 'pdf', '\u56fe\u7247\u5904\u7406', '\u683c\u5f0f\u8f6c\u6362'],
          sources: [
            { name: 'GitHub', domain: 'github.com', icon: '\ud83d\udc19' },
            { name: 'Product Hunt', domain: 'producthunt.com', icon: '\ud83d\ude80' },
            { name: '\u5b98\u7f51', domain: '', icon: '\ud83c\udfe0' }
          ],
          tips: ['\u4f18\u5148\u9009\u62e9\u5f00\u6e90\u514d\u8d39\u5de5\u5177', '\u6ce8\u610f\u524d\u51e0\u6761\u641c\u7d22\u7ed3\u679c\u53ef\u80fd\u662f\u5e7f\u544a\u63a8\u5e7f'],
          recommendations: [
            { name: 'remove.bg', url: 'https://www.remove.bg', desc: '\u5728\u7ebf\u81ea\u52a8\u6263\u56fe\uff0c\u514d\u8d39\u7248\u591f\u7528' },
            { name: 'TinyPNG', url: 'https://tinypng.com', desc: '\u56fe\u7247\u538b\u7f29\u5de5\u5177' }
          ]
        },
        {
          id: 'tech_doc', name: '\u6280\u672f\u6587\u6863', icon: '\ud83d\udcd8',
          keywords: ['\u6587\u6863', 'API', '\u6559\u7a0b', 'UE5', 'Unity', 'React', 'Vue', 'Python', 'JavaScript', 'TypeScript', 'Node.js', 'Docker', 'Kubernetes', 'gpt', 'llm', 'ai', 'openai', 'claude', '\u6a21\u578b', '\u795e\u7ecf\u7f51\u7edc', '\u6df1\u5ea6\u5b66\u4e60', '\u673a\u5668\u5b66\u4e60'],
          sources: [
            { name: '\u5b98\u65b9\u6587\u6863', domain: '', icon: '\ud83d\udcd8' },
            { name: 'StackOverflow', domain: 'stackoverflow.com', icon: '\ud83d\udcac' },
            { name: 'GitHub Issues', domain: 'github.com', icon: '\ud83d\udc1b' },
            { name: 'MDN', domain: 'developer.mozilla.org', icon: '\ud83e\udd8a' },
            { name: 'HuggingFace', domain: 'huggingface.co', icon: '\ud83e\udd17' }
          ],
          tips: ['\u5b98\u65b9\u6587\u6863\u6700\u6743\u5a01\uff0c\u4f18\u5148\u67e5\u770b', 'AI \u9886\u57df\u66f4\u65b0\u5feb\uff0c\u6ce8\u610f\u6587\u6863\u7248\u672c\u65e5\u671f'],
          recommendations: [
            { name: 'OpenAI \u6587\u6863', url: 'https://platform.openai.com/docs', desc: 'GPT API \u5b98\u65b9\u6587\u6863' },
            { name: 'HuggingFace', url: 'https://huggingface.co/docs', desc: '\u5f00\u6e90\u6a21\u578b\u6587\u6863' }
          ]
        },
        {
          id: 'find_official', name: '\u627e\u5b98\u7f51', icon: '\ud83c\udfaf',
          keywords: ['\u5b98\u7f51', '\u5b98\u65b9\u7f51\u7ad9', '\u4e0b\u8f7d', '\u6b63\u7248', 'official'],
          sources: [
            { name: '\u5b98\u7f51', domain: '', icon: '\ud83c\udfe0' },
            { name: 'GitHub', domain: 'github.com', icon: '\ud83d\udc19' },
            { name: 'Product Hunt', domain: 'producthunt.com', icon: '\ud83d\ude80' }
          ],
          tips: ['\u8ba4\u51c6\u5b98\u65b9\u57df\u540d\uff0c\u8b66\u60d5\u5c71\u5be8\u7f51\u7ad9', '\u8f6f\u4ef6\u4e0b\u8f7d\u4f18\u5148\u9009\u62e9\u5b98\u7f51\u6216 GitHub'],
          recommendations: [
            { name: '\u5b98\u7f51\u67e5\u8be2\u6280\u5de7', url: '#', desc: '\u641c\u7d22\u8bcd\u540e\u52a0 official \u6216 github' }
          ]
        },
        {
          id: 'product_review', name: '\u4ea7\u54c1\u6d4b\u8bc4', icon: '\ud83c\udfa7',
          keywords: ['\u6d4b\u8bc4', '\u8bc4\u6d4b', '\u63a8\u8350', '\u5bf9\u6bd4', '\u8033\u673a', '\u624b\u673a', '\u76f8\u673a', '\u7b14\u8bb0\u672c', '\u663e\u793a\u5668', '\u952e\u76d8', '\u9f20\u6807', '\u97f3\u7bb1', '\u5e73\u677f', '\u624b\u8868'],
          sources: [
            { name: '\u4ec0\u4e48\u503c\u5f97\u4e70', domain: 'smzdm.com', icon: '\ud83d\udcb0' },
            { name: '\u77e5\u4e4e', domain: 'zhihu.com', icon: '\u2753' },
            { name: 'B\u7ad9', domain: 'bilibili.com', icon: '\ud83d\udcfa' },
            { name: '\u5c0f\u7ea2\u4e66', domain: 'xiaohongshu.com', icon: '\ud83d\udcd5' }
          ],
          tips: ['\u5efa\u8bae\u4f18\u5148\u770b\u56fe\u6587\u6d4b\u8bc4\u4e86\u89e3\u53c2\u6570', '\u518d\u770b\u89c6\u9891\u4e86\u89e3\u5b9e\u9645\u4f53\u9a8c', '\u6ce8\u610f\u533a\u5206\u771f\u5b9e\u6d4b\u8bc4\u548c\u8f6f\u6587\u5e26\u8d27'],
          recommendations: [
            { name: '\u5148\u770b\u8bc4\u6d4b', url: 'https://space.bilibili.com/2871017', desc: 'B\u7ad9\u77e5\u540d\u79d1\u6280\u6d4b\u8bc4UP\u4e3b' },
            { name: '\u7231\u5426\u79d1\u6280', url: 'https://space.bilibili.com/356211451', desc: '\u72ec\u7acb\u7b2c\u4e09\u65b9\u6d4b\u8bc4' }
          ]
        },
        {
          id: 'tutorial', name: '\u6559\u7a0b\u5b66\u4e60', icon: '\ud83d\udcda',
          keywords: ['\u6559\u7a0b', '\u5165\u95e8', '\u5b66\u4e60', '\u8bfe\u7a0b', '\u6307\u5357', 'how to', ' beginner', '\u65b0\u624b', '\u96f6\u57fa\u7840', '\u901f\u901a', '\u901f\u6210'],
          sources: [
            { name: 'B\u7ad9', domain: 'bilibili.com', icon: '\ud83d\udcfa' },
            { name: 'YouTube', domain: 'youtube.com', icon: '\u25b6\ufe0f' },
            { name: '\u77e5\u4e4e', domain: 'zhihu.com', icon: '\u2753' },
            { name: '\u83dc\u9e1f\u6559\u7a0b', domain: 'runoob.com', icon: '\ud83d\udc26' }
          ],
          tips: ['\u89c6\u9891\u6559\u7a0b\u9002\u5408\u5165\u95e8\uff0c\u56fe\u6587\u9002\u5408\u67e5\u9605', '\u5b98\u65b9\u6559\u7a0b\u6700\u7cfb\u7edf\uff0c\u793e\u533a\u6559\u7a0b\u66f4\u5b9e\u6218'],
          recommendations: [
            { name: 'B\u7ad9\u641c\u7d22', url: 'https://search.bilibili.com', desc: '\u4e2d\u6587\u89c6\u9891\u6559\u7a0b\u6700\u4e30\u5bcc' }
          ]
        }
      ],
      defaultScene: 'tool_find'
    };
  }

  // ==================== 启动 ====================

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', main);
  } else {
    main();
  }
})();
