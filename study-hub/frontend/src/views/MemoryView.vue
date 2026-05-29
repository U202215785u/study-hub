<template>
  <div class="flex h-[calc(100vh-64px)] overflow-hidden">
    <!-- 左侧边栏 -->
    <aside class="w-[220px] min-w-[220px] bg-surface border-r border-border flex flex-col p-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-bold">记忆系统</h2>
        <router-link to="/" class="text-[13px] text-text-secondary hover:text-accent transition-colors no-underline">
          ← 仪表盘
        </router-link>
      </div>

      <!-- 五层记忆导航 -->
      <div class="flex flex-col gap-1 mb-4">
        <div class="text-xs text-text-secondary mb-1 px-1">记忆层级</div>
        <div
          class="flex items-center gap-2 px-3 py-2 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentLayer === '' ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setLayer('')"
        >
          <span class="text-lg">🧠</span>
          <span class="flex-1">全部记忆</span>
          <span class="text-text-secondary text-xs">{{ totalCount }}</span>
        </div>
        <div
          class="flex items-center gap-2 px-3 py-2 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentLayer === 'role' ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setLayer('role')"
        >
          <span class="text-lg">👤</span>
          <span class="flex-1">角色记忆</span>
          <span class="text-text-secondary text-xs">{{ layerCounts.role }}</span>
        </div>
        <div
          class="flex items-center gap-2 px-3 py-2 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentLayer === 'project' ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setLayer('project')"
        >
          <span class="text-lg">📁</span>
          <span class="flex-1">项目记忆</span>
          <span class="text-text-secondary text-xs">{{ layerCounts.project }}</span>
        </div>
        <div
          class="flex items-center gap-2 px-3 py-2 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentLayer === 'workflow' ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setLayer('workflow')"
        >
          <span class="text-lg">⚙️</span>
          <span class="flex-1">工作流记忆</span>
          <span class="text-text-secondary text-xs">{{ layerCounts.workflow }}</span>
        </div>
        <div
          class="flex items-center gap-2 px-3 py-2 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentLayer === 'session' ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setLayer('session')"
        >
          <span class="text-lg">💬</span>
          <span class="flex-1">会话记忆</span>
          <span class="text-text-secondary text-xs">{{ layerCounts.session }}</span>
        </div>
        <div
          class="flex items-center gap-2 px-3 py-2 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentLayer === 'world' ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setLayer('world')"
        >
          <span class="text-lg">🌍</span>
          <span class="flex-1">世界记忆</span>
          <span class="text-text-secondary text-xs">{{ layerCounts.world }}</span>
        </div>
      </div>

      <!-- 状态过滤 -->
      <div class="flex flex-col gap-0.5 mb-4">
        <div class="text-xs text-text-secondary mb-1 px-1">状态</div>
        <div
          v-for="s in statusFilters"
          :key="s.value"
          class="flex items-center gap-2 px-3 py-1.5 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentStatus === s.value ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setStatus(s.value)"
        >
          <span>{{ s.icon }}</span>
          <span class="flex-1">{{ s.label }}</span>
        </div>
      </div>

      <!-- 项目列表 -->
      <div v-if="projects.length > 0" class="flex flex-col gap-0.5 mb-4">
        <div class="text-xs text-text-secondary mb-1 px-1">项目</div>
        <div
          v-for="p in projects"
          :key="p.name"
          class="flex items-center gap-2 px-3 py-1.5 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentProject === p.name ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="setProject(p.name)"
        >
          <span>{{ {active:'🟢',paused:'🟡',completed:'✅',archived:'📦'}[p.status] || '⚪' }}</span>
          <span class="flex-1 truncate">{{ p.name }}</span>
        </div>
      </div>

      <div
        class="flex items-center gap-1.5 px-3 py-2.5 rounded-[8px] cursor-pointer text-[13px] text-text-secondary border border-dashed border-border mt-auto transition-colors hover:bg-surface-hover hover:text-accent hover:border-accent"
        @click="openAddModal"
      >
        + 新建记忆
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 标题栏 -->
      <div class="flex items-center gap-3 px-6 py-4 bg-surface border-b border-border flex-wrap">
        <h3 class="text-[15px] font-semibold mr-auto">{{ pageTitle }}</h3>
        <span class="text-text-secondary text-[13px]">{{ filteredMemories.length }} 条</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="语义搜索记忆…"
          class="px-3.5 py-2 bg-bg border border-border rounded-[8px] text-text text-[13px] outline-none w-[240px] focus:border-accent"
          @keydown.enter="doSearch"
        >
        <button
          class="px-3.5 py-[7px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90"
          @click="doSearch"
        >
          搜索
        </button>
        <button
          class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
          @click="openExtractModal"
        >
          提取文本
        </button>
      </div>

      <!-- 记忆列表 -->
      <div class="flex-1 overflow-y-auto px-6 py-4">
        <div v-if="loading" class="text-center py-[60px] text-text-secondary">
          <div class="text-2xl mb-3">⏳</div>
          <p>加载中…</p>
        </div>

        <div v-else-if="!filteredMemories.length" class="text-center py-[60px] text-text-secondary">
          <div class="text-5xl mb-3">🧠</div>
          <p>暂无记忆。点击"新建记忆"或"提取文本"开始。</p>
        </div>

        <div v-else class="flex flex-col gap-2">
          <div
            v-for="mem in filteredMemories"
            :key="mem.id"
            class="flex items-start gap-3 px-4 py-3 bg-surface border border-border rounded-[8px] hover:border-accent transition-colors"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <span
                  class="inline-flex items-center gap-1 px-2 py-[2px] rounded-[10px] text-[11px] border"
                  :class="statusClass(mem.status)"
                >
                  {{ statusIcon(mem.status) }} {{ mem.status }}
                </span>
                <span
                  v-if="mem.memory_layer"
                  class="inline-flex items-center gap-1 px-2 py-[2px] rounded-[10px] text-[11px] border"
                  :class="layerClass(mem.memory_layer)"
                >
                  {{ layerIcon(mem.memory_layer) }} {{ layerLabel(mem.memory_layer) }}
                </span>
                <span
                  v-if="mem.project_name"
                  class="inline-flex items-center gap-1 px-2 py-[2px] rounded-[10px] text-[11px] bg-surface border border-border text-text-secondary"
                >
                  📁 {{ mem.project_name }}
                </span>
                <span
                  v-if="mem.workflow_name"
                  class="inline-flex items-center gap-1 px-2 py-[2px] rounded-[10px] text-[11px] bg-surface border border-border text-text-secondary"
                >
                  ⚙️ {{ mem.workflow_name }}
                </span>
                <span class="text-text-secondary text-[11px]">ID {{ mem.id }}</span>
                <span class="text-text-secondary text-[11px] ml-auto">{{ formatDate(mem.created_at) }}</span>
              </div>
              <p class="text-sm text-text leading-relaxed">{{ mem.content }}</p>
              <div v-if="mem.tags?.length" class="flex gap-1 mt-1.5 flex-wrap">
                <span
                  v-for="tag in mem.tags"
                  :key="tag"
                  class="inline-block px-2 py-0.5 rounded-[10px] text-[11px] bg-accent-glow text-accent"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
            <div class="flex gap-1 shrink-0">
              <button
                class="px-2 py-1 text-[11px] rounded-[6px] border border-border bg-surface text-text cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
                title="编辑"
                @click="openEditModal(mem)"
              >
                编
              </button>
              <button
                v-if="mem.status === 'active'"
                class="px-2 py-1 text-[11px] rounded-[6px] border border-border bg-surface text-text-secondary cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
                title="标记过时"
                @click="markStatus(mem.id, 'outdated')"
              >
                🕐
              </button>
              <button
                v-if="mem.status === 'active'"
                class="px-2 py-1 text-[11px] rounded-[6px] border border-border bg-surface text-danger cursor-pointer transition-colors hover:bg-danger hover:text-white"
                title="标记错误"
                @click="markStatus(mem.id, 'wrong')"
              >
                ❌
              </button>
              <button
                class="px-2 py-1 text-[11px] rounded-[6px] border border-border bg-surface text-danger cursor-pointer transition-colors hover:bg-danger hover:text-white"
                title="删除"
                @click="deleteMemory(mem.id)"
              >
                删
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 新建/编辑记忆弹窗 -->
    <div
      v-if="editModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="editModalVisible = false"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[520px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">{{ editingId ? '编辑记忆' : '新建记忆' }}</h3>
        <textarea
          v-model="editForm.content"
          placeholder="记忆内容，如：用户喜欢吃辣的食物"
          class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent resize-y min-h-[80px] font-[inherit]"
        />
        <div class="flex gap-3">
          <select
            v-model="editForm.memory_layer"
            class="flex-1 px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          >
            <option value="role">👤 角色记忆</option>
            <option value="project">📁 项目记忆</option>
            <option value="workflow">⚙️ 工作流记忆</option>
            <option value="session">💬 会话记忆</option>
            <option value="world">🌍 世界记忆</option>
          </select>
          <select
            v-model="editForm.memory_type"
            class="flex-1 px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          >
            <option value="fact">事实</option>
            <option value="decision">决策</option>
            <option value="preference">偏好</option>
            <option value="habit">习惯</option>
            <option value="action_item">待办</option>
            <option value="lesson">教训</option>
            <option value="snippet">片段</option>
          </select>
        </div>
        <div class="flex gap-3">
          <input
            v-model="editForm.category"
            type="text"
            placeholder="分类"
            class="flex-1 px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          >
          <input
            v-model="tagInput"
            type="text"
            placeholder="标签，逗号分隔"
            class="flex-1 px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          >
        </div>
        <div class="flex gap-3">
          <input
            v-model="editForm.project_name"
            type="text"
            placeholder="项目名称（可选）"
            class="flex-1 px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          >
          <input
            v-model="editForm.workflow_name"
            type="text"
            placeholder="工作流名称（可选）"
            class="flex-1 px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          >
        </div>
        <div class="flex gap-3">
          <label class="flex items-center gap-2 text-sm text-text-secondary">
            重要性
            <input v-model.number="editForm.importance" type="number" min="1" max="5" class="w-16 px-2 py-1 bg-bg border border-border rounded-[6px] text-sm outline-none focus:border-accent">
          </label>
          <label class="flex items-center gap-2 text-sm text-text-secondary">
            置信度
            <input v-model.number="editForm.confidence" type="number" min="0" max="1" step="0.1" class="w-16 px-2 py-1 bg-bg border border-border rounded-[6px] text-sm outline-none focus:border-accent">
          </label>
        </div>
        <div class="flex gap-2.5 justify-end">
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="editModalVisible = false"
          >
            取消
          </button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90"
            @click="saveMemory"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- 提取文本弹窗 -->
    <div
      v-if="extractModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="extractModalVisible = false"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[600px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">从文本提取分层记忆</h3>
        <textarea
          v-model="extractText"
          placeholder="粘贴对话或文本内容，AI 会自动提取五层记忆…"
          class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent resize-y min-h-[200px] font-[inherit]"
        />
        <div class="flex gap-2.5 justify-end">
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="extractModalVisible = false"
          >
            取消
          </button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90"
            :disabled="extracting"
            @click="doExtract"
          >
            {{ extracting ? '提取中…' : '提取并保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div
      v-if="toastVisible"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 px-5 py-2.5 rounded-[8px] text-sm border z-[200] transition-opacity duration-300"
      :class="toastIsError ? 'border-danger text-danger' : 'border-border text-text bg-surface'"
    >
      {{ toastMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'

const settings = useSettingsStore()

// ===== 状态 =====
const memories = ref([])
const projects = ref([])
const layerCounts = ref({ role: 0, project: 0, workflow: 0, session: 0, world: 0 })
const currentLayer = ref('')
const currentStatus = ref('')
const currentProject = ref('')
const searchQuery = ref('')
const searchResults = ref(null)
const loading = ref(false)

const statusFilters = [
  { value: '', label: '全部状态', icon: '🧠' },
  { value: 'active', label: '有效', icon: '✅' },
  { value: 'outdated', label: '已过时', icon: '🕐' },
  { value: 'wrong', label: '错误', icon: '❌' },
]

// 弹窗
const editModalVisible = ref(false)
const editingId = ref(null)
const editForm = ref({
  content: '',
  category: '',
  tags: [],
  importance: 3,
  confidence: 1.0,
  memory_layer: 'session',
  project_name: '',
  workflow_name: '',
  memory_type: 'fact',
})
const tagInput = ref('')

const extractModalVisible = ref(false)
const extractText = ref('')
const extracting = ref(false)

// Toast
const toastVisible = ref(false)
const toastMsg = ref('')
const toastIsError = ref(false)
let toastTimer = null

// ===== 计算属性 =====
const pageTitle = computed(() => {
  if (searchResults.value !== null) return `搜索结果："${searchQuery.value}"`
  if (currentProject.value) return `项目：${currentProject.value}`
  const layerTitles = {
    '': '全部记忆',
    role: '👤 角色记忆',
    project: '📁 项目记忆',
    workflow: '⚙️ 工作流记忆',
    session: '💬 会话记忆',
    world: '🌍 世界记忆',
  }
  return layerTitles[currentLayer.value] || '全部记忆'
})

const totalCount = computed(() => memories.value.length)

const filteredMemories = computed(() => {
  if (searchResults.value !== null) return searchResults.value
  let list = memories.value
  if (currentStatus.value) {
    list = list.filter(m => m.status === currentStatus.value)
  }
  if (currentLayer.value) {
    list = list.filter(m => m.memory_layer === currentLayer.value)
  }
  if (currentProject.value) {
    list = list.filter(m => m.project_name === currentProject.value)
  }
  return list
})

// ===== 帮助函数 =====
function toast(msg, isError = false) {
  toastMsg.value = msg
  toastIsError.value = isError
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2500)
}

function statusIcon(status) {
  return { active: '✅', outdated: '🕐', wrong: '❌' }[status] || '•'
}

function statusClass(status) {
  const map = {
    active: 'bg-green-500/10 border-green-500/30 text-green-400',
    outdated: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
    wrong: 'bg-red-500/10 border-red-500/30 text-red-400',
  }
  return map[status] || 'bg-surface border-border text-text-secondary'
}

function layerIcon(layer) {
  return { role: '👤', project: '📁', workflow: '⚙️', session: '💬', world: '🌍' }[layer] || '•'
}

function layerLabel(layer) {
  return { role: '角色', project: '项目', workflow: '工作流', session: '会话', world: '世界' }[layer] || layer
}

function layerClass(layer) {
  const map = {
    role: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
    project: 'bg-green-500/10 border-green-500/30 text-green-400',
    workflow: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
    session: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
    world: 'bg-gray-500/10 border-gray-500/30 text-gray-400',
  }
  return map[layer] || 'bg-surface border-border text-text-secondary'
}

function formatDate(dateStr) {
  return (dateStr || '').slice(0, 10)
}

// ===== 数据加载 =====
async function loadMemories() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('limit', '200')
    if (currentLayer.value) params.append('layer', currentLayer.value)
    if (currentStatus.value) params.append('status', currentStatus.value)
    if (currentProject.value) params.append('project', currentProject.value)

    const data = await settings.apiGet(`/memory/list?${params.toString()}`)
    memories.value = data.items || []

    // 加载各层统计
    await loadLayerCounts()
  } catch (e) {
    toast('加载记忆失败', true)
  } finally {
    loading.value = false
  }
}

async function loadLayerCounts() {
  const layers = ['role', 'project', 'workflow', 'session', 'world']
  for (const layer of layers) {
    try {
      const data = await settings.apiGet(`/memory/list?layer=${layer}&limit=1`)
      layerCounts.value[layer] = data.total || 0
    } catch {
      layerCounts.value[layer] = 0
    }
  }
}

async function loadProjects() {
  try {
    const data = await settings.apiGet('/projects')
    projects.value = data || []
  } catch {
    projects.value = []
  }
}

// ===== 筛选 =====
function setLayer(layer) {
  currentLayer.value = layer
  currentProject.value = ''
  searchResults.value = null
  loadMemories()
}

function setStatus(status) {
  currentStatus.value = status
  searchResults.value = null
  loadMemories()
}

function setProject(projectName) {
  if (currentProject.value === projectName) {
    currentProject.value = ''
  } else {
    currentProject.value = projectName
  }
  searchResults.value = null
  loadMemories()
}

// ===== 搜索 =====
async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) {
    searchResults.value = null
    return
  }
  loading.value = true
  try {
    const data = await settings.apiGet(`/memory/recall?q=${encodeURIComponent(q)}&top_k=20`)
    searchResults.value = data.results || []
    if (!searchResults.value.length) toast('未找到相关记忆')
  } catch {
    toast('搜索失败', true)
  } finally {
    loading.value = false
  }
}

// ===== 新增/编辑 =====
function openAddModal() {
  editingId.value = null
  editForm.value = {
    content: '',
    category: '',
    tags: [],
    importance: 3,
    confidence: 1.0,
    memory_layer: currentLayer.value || 'session',
    project_name: currentProject.value || '',
    workflow_name: '',
    memory_type: 'fact',
  }
  tagInput.value = ''
  editModalVisible.value = true
}

function openEditModal(mem) {
  editingId.value = mem.id
  editForm.value = {
    content: mem.content,
    category: mem.category || '',
    tags: [...(mem.tags || [])],
    importance: mem.importance,
    confidence: mem.confidence,
    memory_layer: mem.memory_layer || 'session',
    project_name: mem.project_name || '',
    workflow_name: mem.workflow_name || '',
    memory_type: mem.memory_type || 'fact',
  }
  tagInput.value = (mem.tags || []).join(', ')
  editModalVisible.value = true
}

async function saveMemory() {
  const content = editForm.value.content.trim()
  if (!content) { toast('请填写记忆内容', true); return }

  const tags = tagInput.value.split(',').map(t => t.trim()).filter(Boolean)
  const body = {
    content,
    category: editForm.value.category || 'other',
    tags,
    importance: editForm.value.importance,
    confidence: editForm.value.confidence,
    memory_layer: editForm.value.memory_layer,
    project_name: editForm.value.project_name,
    workflow_name: editForm.value.workflow_name,
    memory_type: editForm.value.memory_type,
  }

  try {
    if (editingId.value) {
      await settings.apiPut(`/memory/${editingId.value}`, body)
      toast('记忆已更新')
    } else {
      await settings.apiPost('/memory/remember', body)
      toast('记忆已保存')
    }
    editModalVisible.value = false
    await loadMemories()
  } catch {
    toast('保存失败', true)
  }
}

// ===== 状态标记 =====
async function markStatus(id, status) {
  try {
    await settings.apiPut(`/memory/${id}`, { status })
    toast(`已标记为 ${status}`)
    await loadMemories()
  } catch {
    toast('操作失败', true)
  }
}

// ===== 删除 =====
async function deleteMemory(id) {
  if (!confirm('确认删除这条记忆？')) return
  try {
    await settings.apiDelete(`/memory/${id}`)
    toast('已删除')
    await loadMemories()
  } catch {
    toast('删除失败', true)
  }
}

// ===== 提取文本 =====
function openExtractModal() {
  extractText.value = ''
  extractModalVisible.value = true
}

async function doExtract() {
  const text = extractText.value.trim()
  if (!text) { toast('请输入文本', true); return }
  extracting.value = true
  try {
    const data = await settings.apiPost('/memory/summarize_and_extract', {
      conversation: text,
      source_tool: 'web',
    })
    extracting.value = false
    extractModalVisible.value = false
    const layers = data.added_by_layer || {}
    toast(`提取完成：角色${layers.role || 0} 项目${layers.project || 0} 工作流${layers.workflow || 0} 会话${layers.session || 0}`)
    await loadMemories()
  } catch {
    extracting.value = false
    toast('提取失败', true)
  }
}

// ===== 初始化 =====
onMounted(() => {
  loadMemories()
  loadProjects()
})
</script>
