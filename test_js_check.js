// ===== 配置 =====
const API_BASE = (() => {
  const stored = localStorage.getItem('api_base');
  if (stored) return stored;
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1' && window.location.port !== '') {
    return window.location.origin;
  }
  return window.location.origin || 'http://localhost:8741';
})();

// ===== 默认数据 =====
const DEFAULT_SHORTCUTS = [
  { name: '抖音', url: 'https://www.douyin.com', icon: '🎵' },
  { name: 'GitHub', url: 'https://github.com', icon: '🐙' },
  { name: 'VSCode', url: 'https://vscode.dev', icon: '💻' },
  { name: 'B站', url: 'https://www.bilibili.com', icon: '📺' },
  { name: '翻译', url: 'https://translate.google.com', icon: '🌐' },
  { name: 'Gmail', url: 'https://mail.google.com', icon: '📧' },
];

const DEFAULT_AIS = [
  { name: 'Claude', url: 'https://claude.ai', icon: '🧠' },
  { name: 'ChatGPT', url: 'https://chat.openai.com', icon: '🤖' },
  { name: 'DeepSeek', url: 'https://chat.deepseek.com', icon: '🔮' },
  { name: 'Kimi', url: 'https://kimi.moonshot.cn', icon: '🌙' },
];

// ===== 帮助函数 =====
function $(id) { return document.getElementById(id); }
function qs(sel) { return document.querySelector(sel); }
function qsa(sel) { return document.querySelectorAll(sel); }

function toast(msg, isError) {
  const t = $('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isError ? ' error' : '');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.className = 'toast'; }, 2500);
}

function getData(key, def) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : def; }
  catch { return def; }
}
function setData(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
}

// ===== 常用网站 =====
let shortcuts = getData('shortcuts', DEFAULT_SHORTCUTS);
let editingShortcutIdx = -1;

function renderShortcuts() {
  const grid = $('shortcutsGrid');
  grid.innerHTML = shortcuts.map((s, i) => `
    <a class="shortcut-card" href="${s.url}" target="_blank" data-idx="${i}"
       oncontextmenu="return deleteShortcut(event, ${i})">
      <span class="icon">${s.icon}</span>
      <span class="name">${s.name}</span>
      <button class="delete-btn" onclick="deleteShortcut(event, ${i})" title="删除">×</button>
    </a>
  `).join('') + `
    <div class="shortcut-card add-card" onclick="openShortcutModal()">
      <span class="icon">+</span>
      <span class="name">添加</span>
    </div>
  `;
  setData('shortcuts', shortcuts);
}

function deleteShortcut(e, idx) {
  e.preventDefault();
  shortcuts.splice(idx, 1);
  renderShortcuts();
}

function openShortcutModal(idx) {
  editingShortcutIdx = idx !== undefined ? idx : -1;
  $('shortcutModalTitle').textContent = editingShortcutIdx >= 0 ? '编辑快捷方式' : '添加快捷方式';
  $('shortcutName').value = editingShortcutIdx >= 0 ? shortcuts[editingShortcutIdx].name : '';
  $('shortcutUrl').value = editingShortcutIdx >= 0 ? shortcuts[editingShortcutIdx].url : '';
  $('shortcutIcon').value = editingShortcutIdx >= 0 ? shortcuts[editingShortcutIdx].icon : '';
  $('shortcutModal').classList.add('visible');
  $('shortcutName').focus();
}

$('shortcutCancel').onclick = () => { $('shortcutModal').classList.remove('visible'); };
$('shortcutSave').onclick = () => {
  const name = $('shortcutName').value.trim();
  const url = $('shortcutUrl').value.trim();
  const icon = $('shortcutIcon').value.trim() || '🔗';
  if (!name || !url) { toast('请填写名称和 URL', true); return; }
  if (editingShortcutIdx >= 0) {
    shortcuts[editingShortcutIdx] = { name, url, icon };
  } else {
    shortcuts.push({ name, url, icon });
  }
  renderShortcuts();
  $('shortcutModal').classList.remove('visible');
};

// 右键菜单编辑
document.addEventListener('contextmenu', (e) => {
  const card = e.target.closest('.shortcut-card');
  if (card && card.dataset.idx !== undefined) {
    e.preventDefault();
    const idx = parseInt(card.dataset.idx);
    openShortcutModal(idx);
  }
});

// ===== AI 启动器 =====
let ais = getData('ais', DEFAULT_AIS);

function renderAIs() {
  const grid = $('aiGrid');
  grid.innerHTML = ais.map((a, i) => `
    <div class="ai-card" onclick="launchAI(${i})">
      <span class="ai-icon">${a.icon}</span>
      <span class="ai-name">${a.name}</span>
      <span class="ai-url">${a.url}</span>
    </div>
  `).join('') + `
    <div class="ai-card add-ai" onclick="openAIModal()">
      <span class="ai-icon">+</span>
      <span class="ai-name">添加 AI</span>
    </div>
  `;
  setData('ais', ais);
}

function launchAI(idx) {
  window.open(ais[idx].url, '_blank');
}

$('aiCancel').onclick = () => { $('aiModal').classList.remove('visible'); };
$('aiSave').onclick = () => {
  const name = $('aiNameInput').value.trim();
  const url = $('aiUrlInput').value.trim();
  const icon = $('aiIconInput').value.trim() || '🤖';
  if (!name || !url) { toast('请填写名称和 URL', true); return; }
  ais.push({ name, url, icon });
  renderAIs();
  $('aiModal').classList.remove('visible');
};

function openAIModal() {
  $('aiNameInput').value = '';
  $('aiUrlInput').value = '';
  $('aiIconInput').value = '';
  $('aiModal').classList.add('visible');
  $('aiNameInput').focus();
}

// ===== 搜索 =====
const searchInput = $('searchInput');
const searchResult = $('searchResult');
const searchHint = $('searchHint');

searchInput.addEventListener('input', () => {
  const val = searchInput.value;
  if (val.startsWith('!')) {
    searchHint.textContent = '全网搜索';
  } else if (val.startsWith('>')) {
    searchHint.textContent = '命令模式';
  } else if (val.length > 0) {
    searchHint.textContent = '知识库搜索';
  } else {
    searchHint.textContent = '';
  }
});

searchInput.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter') return;
  const val = searchInput.value.trim();
  if (!val) return;

  if (val.startsWith('!')) {
    const q = val.slice(1).trim();
    if (q) window.location.href = `https://www.google.com/search?q=${encodeURIComponent(q)}`;
    return;
  }

  if (val.startsWith('>')) {
    handleCommand(val.slice(1).trim());
    return;
  }

  // 知识库搜索
  doKBQuery(val);
});

async function doKBQuery(question) {
  searchResult.className = 'search-result loading';
  searchResult.innerHTML = '<span>正在搜索知识库…</span>';
  try {
    const res = await fetch(`${API_BASE}/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    if (data.error) {
      searchResult.className = 'search-result visible';
      searchResult.innerHTML = `<div class="error">${escapeHtml(data.answer || data.error)}</div>`;
      return;
    }
    const sourcesHtml = data.sources?.length
      ? `<div class="sources">来源：${data.sources.map(s => escapeHtml(s)).join('；')}</div>`
      : '';
    searchResult.className = 'search-result visible';
    searchResult.innerHTML = `
      <div class="answer">${escapeHtml(data.answer)}</div>
      ${sourcesHtml}
    `;
  } catch (err) {
    searchResult.className = 'search-result visible';
    searchResult.innerHTML = `<div class="error">无法连接后端服务。请确认后端已启动 (${API_BASE})</div>`;
  }
}

function handleCommand(cmd) {
  if (cmd === 'notes') {
    toast('正在打开记事本…');
    // 浏览器无法直接打开本地程序，提示用户
    toast('浏览器无法直接打开记事本。请用 Win+R → notepad', true);
  } else if (cmd === 'folder') {
    toast('项目文件夹：study-hub/');
  } else {
    // 自定义命令
    const commands = getData('commands', {});
    const url = commands[cmd];
    if (url) { window.open(url, '_blank'); }
    else { toast(`未知命令: ${cmd}`, true); }
  }
}

// 知识库搜索按钮
$('kbSearchBtn').onclick = () => {
  const q = searchInput.value.trim().replace(/^[!>]/, '').trim();
  if (!q) { searchInput.focus(); return; }
  doKBQuery(q);
};

// ===== 知识库 =====
$('fileInput').onchange = async () => {
  const files = $('fileInput').files;
  if (!files.length) return;
  for (const file of files) {
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (data.id) {
        toast(`"${file.name}" 上传成功 (${data.char_count} 字)`);
      } else {
        toast(`上传失败: ${data.detail || '未知错误'}`, true);
      }
    } catch (err) {
      toast(`上传失败: 无法连接后端`, true);
    }
  }
  $('fileInput').value = '';
  loadDocuments();
};

async function loadDocuments() {
  const list = $('kbDocList');
  try {
    const res = await fetch(`${API_BASE}/documents`);
    const docs = await res.json();
    if (!docs.length) {
      list.innerHTML = '<li class="kb-empty">知识库为空，请上传文档</li>';
      return;
    }
    list.innerHTML = docs.slice(0, 10).map(d => `
      <li>
        <span class="doc-meta" onclick="viewDocument(${d.id})" style="cursor:pointer;flex:1;">
          <span class="doc-title">${escapeHtml(d.title)}</span>
          <span class="doc-meta">${d.created_at?.slice(0,10) || ''} · ${d.char_count || 0}字</span>
        </span>
        <button class="btn send-claude-btn" data-id="${d.id}" data-title="${escapeHtml(d.title).replace(/"/g, '&quot;')}" title="复制文档内容并打开 Claude" style="font-size:11px;padding:4px 10px;">发送到 Claude</button>
      </li>
    `).join('');
  } catch {
    list.innerHTML = '<li class="kb-empty">无法连接后端，请确认服务已启动</li>';
  }
}

async function openInbox() {
  try {
    const res = await fetch(`${API_BASE}/inbox/open`, { method: 'POST' });
    const data = await res.json();
    if (data.error) {
      toast(`打开收件箱失败: ${data.error}`, true);
    } else {
      toast(`收件箱已打开: ${data.path}`);
    }
  } catch {
    toast('打开收件箱失败，请确认后端已启动', true);
  }
}

// 事件委托：发送到 Claude 按钮
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.send-claude-btn');
  if (!btn) return;
  e.stopPropagation();
  const id = parseInt(btn.dataset.id);
  const title = btn.dataset.title;
  sendToClaude(id, title);
});

// ===== Claude 桥梁 =====
async function sendToClaude(docId, title) {
  try {
    const res = await fetch(`${API_BASE}/documents/${docId}`);
    const doc = await res.json();
    const content = doc.content || '';
    await navigator.clipboard.writeText(content);
    toast(`"${title}" 已复制到剪贴板，请粘贴到 Claude Desktop`);
  } catch {
    toast('获取文档失败', true);
  }
}

// 粘贴 Claude 对话
$('pasteClaudeBtn').onclick = () => {
  $('pasteContent').value = '';
  $('pasteTitle').value = 'Claude对话 ' + new Date().toISOString().slice(0, 16).replace('T', ' ');
  $('pasteModal').classList.add('visible');
  $('pasteContent').focus();
};
$('pasteCancel').onclick = () => { $('pasteModal').classList.remove('visible'); };
$('pasteSave').onclick = async () => {
  const content = $('pasteContent').value.trim();
  const title = $('pasteTitle').value.trim() || ('Claude对话 ' + new Date().toISOString().slice(0, 16).replace('T', ' '));
  if (!content) { toast('请粘贴对话内容', true); return; }
  try {
    const res = await fetch(`${API_BASE}/upload/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content, source: 'claude' }),
    });
    const data = await res.json();
    if (data.id) {
      toast(`已存入知识库 (${data.char_count} 字)`);
      $('pasteModal').classList.remove('visible');
      loadDocuments();
    } else {
      toast('存入失败: ' + (data.error || '未知错误'), true);
    }
  } catch {
    toast('存入失败: 无法连接后端', true);
  }
};

async function viewDocument(id) {
  try {
    const res = await fetch(`${API_BASE}/documents/${id}`);
    const doc = await res.json();
    $('docModalTitle').textContent = doc.title;
    $('docModalContent').textContent = doc.content;
    $('docModal').classList.add('visible');
  } catch {
    toast('加载文档失败', true);
  }
}

$('docModalClose').onclick = () => { $('docModal').classList.remove('visible'); };

// ===== 每日复盘 =====
$('reviewPolishBtn').onclick = async () => {
  const rawText = $('reviewInput').value.trim();
  if (!rawText) { toast('请先输入今天的笔记', true); return; }

  $('reviewPolishBtn').disabled = true;
  $('reviewStatus').textContent = '正在润色…';

  try {
    const today = new Date().toISOString().slice(0, 10);
    const res = await fetch(`${API_BASE}/review/polish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: rawText, date: today }),
    });
    const data = await res.json();

    $('reviewPolished').textContent = data.polished || '';
    $('reviewSuggestions').innerHTML = (data.suggestions || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');
    $('reviewRelated').innerHTML = (data.related_docs || []).map(d => `关联：${escapeHtml(d)}`).join('<br>');
    $('reviewResult').classList.add('visible');
    $('reviewStatus').textContent = '完成';

    loadReviewHistory();
  } catch {
    toast('润色失败，请确认后端已启动', true);
    $('reviewStatus').textContent = '';
  } finally {
    $('reviewPolishBtn').disabled = false;
  }
};

$('reviewWeeklyBtn').onclick = async () => {
  $('reviewWeeklyBtn').disabled = true;
  $('reviewStatus').textContent = '正在生成周报…';
  try {
    const res = await fetch(`${API_BASE}/review/weekly`);
    const data = await res.json();
    $('reviewPolished').textContent = data.report || '';
    $('reviewSuggestions').innerHTML = '';
    $('reviewRelated').innerHTML = '';
    $('reviewResult').classList.add('visible');
    $('reviewStatus').textContent = '完成';
  } catch {
    toast('周报生成失败', true);
    $('reviewStatus').textContent = '';
  } finally {
    $('reviewWeeklyBtn').disabled = false;
  }
};

async function loadReviewHistory() {
  try {
    const res = await fetch(`${API_BASE}/review/list`);
    const data = await res.json();
    if (!data.length) return;
    $('reviewHistory').style.display = 'block';
    $('reviewHistoryList').innerHTML = data.slice(0, 7).map(r => `
      <div class="history-item" onclick="viewReview(${r.id})">
        ${escapeHtml(r.date)} — ${escapeHtml((r.raw_text || '').slice(0, 50))}…
      </div>
    `).join('');
  } catch {}
}

async function viewReview(id) {
  // 简单展示：重新获取列表找到对应项
  try {
    const res = await fetch(`${API_BASE}/review/list`);
    const data = await res.json();
    const r = data.find(d => d.id === id);
    if (r) {
      $('reviewPolished').textContent = r.polished || r.raw_text || '';
      $('reviewSuggestions').innerHTML = '';
      $('reviewRelated').innerHTML = '';
      $('reviewResult').classList.add('visible');
    }
  } catch {}
}

// ===== 工具函数 =====
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ===== 弹窗关闭 =====
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.classList.remove('visible');
  });
});

// 键盘快捷关闭
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.visible').forEach(m => m.classList.remove('visible'));
    searchInput.focus();
  }
});

// ===== 初始化 =====
function init() {
  renderShortcuts();
  renderAIs();
  loadDocuments();
  loadReviewHistory();
}

init();