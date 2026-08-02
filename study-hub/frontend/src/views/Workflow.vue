<template>
  <div class="flex flex-col gap-6">
    <!-- 标题 -->
    <div class="text-center">
      <h1 class="text-[22px] font-bold tracking-tight">工作流</h1>
      <p class="text-xs text-text-secondary mt-1">用大白话描述流程 → AI 自动生成 → 一键执行</p>
    </div>

    <!-- ====== 白话文创建 ====== -->
    <div class="bg-surface border border-border rounded-[12px] p-5">
      <div class="text-sm font-semibold mb-3">✨ 创建一个新工作流</div>
      <div class="flex gap-2">
        <input
          v-model="createText"
          @keydown.enter="createFromText"
          type="text"
          placeholder="用大白话描述你想做什么，比如：打开百度搜猫的图片，截图，AI分析是什么品种"
          class="flex-1 px-4 py-3 bg-surface border border-border rounded-[10px] text-text text-sm outline-none focus:border-accent"
          :disabled="creating"
        />
        <button
          @click="createFromText"
          :disabled="creating || !createText.trim()"
          class="px-5 py-3 bg-accent text-white rounded-[10px] font-semibold text-sm border-none cursor-pointer transition-all whitespace-nowrap"
          :class="creating || !createText.trim() ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-[0_4px_16px_rgba(124,138,255,0.3)]'"
        >
          {{ creating ? '生成中…' : '生成工作流' }}
        </button>
      </div>
      <div v-if="createError" class="text-xs text-danger mt-2">{{ createError }}</div>
      <div v-if="createSuccess" class="text-xs text-success mt-2">{{ createSuccess }}</div>
    </div>

    <!-- ====== 模板列表 ====== -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <span class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px]">
          可用模板 ({{ templates.length }})
        </span>
        <button
          @click="loadTemplates"
          class="text-[11px] text-text-secondary hover:text-accent bg-transparent border-none cursor-pointer"
        >刷新</button>
      </div>

      <div v-if="loading" class="text-text-secondary text-sm">加载中…</div>

      <div v-else-if="templates.length === 0" class="bg-surface border border-dashed border-border rounded-[12px] p-8 text-center text-text-secondary text-sm">
        <p class="mb-2 text-2xl">📭</p>
        <p>还没有工作流模板</p>
        <p class="text-xs mt-1">在上方用大白话描述你想做的事，AI 会帮你生成第一个</p>
      </div>

      <div v-else class="grid gap-3">
        <div
          v-for="t in templates" :key="t.file"
          class="bg-surface border rounded-[12px] p-4 transition-all"
          :class="selected?.file === t.file ? 'border-accent shadow-[0_0_16px_rgba(124,138,255,0.2)]' : 'border-border'"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 cursor-pointer" @click="selectTemplate(t)">
              <div class="flex items-center gap-2">
                <span class="font-semibold text-sm">{{ t.name }}</span>
                <span class="text-[10px] text-text-secondary bg-white/[0.06] px-2 py-0.5 rounded-full">{{ t.steps_count }} 步</span>
              </div>
              <div v-if="t.desc" class="text-xs text-text-secondary mt-1">{{ t.desc }}</div>
              <div class="flex gap-1.5 mt-2 flex-wrap">
                <span v-for="s in t.steps" :key="s.id" class="text-[10px] text-text-secondary bg-white/[0.04] px-1.5 py-0.5 rounded">
                  {{ s.label }}
                </span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex gap-1 ml-3 flex-shrink-0">
              <button
                @click.stop="copyTemplate(t)"
                class="text-[11px] text-text-secondary hover:text-accent bg-white/[0.04] px-2 py-1 rounded border-none cursor-pointer"
                title="复制"
              >📋</button>
              <button
                @click.stop="startEdit(t)"
                class="text-[11px] text-text-secondary hover:text-accent bg-white/[0.04] px-2 py-1 rounded border-none cursor-pointer"
                title="编辑"
              >✏️</button>
              <button
                @click.stop="confirmDelete(t)"
                class="text-[11px] text-text-secondary hover:text-danger bg-white/[0.04] px-2 py-1 rounded border-none cursor-pointer"
                title="删除"
              >🗑</button>
            </div>
          </div>

          <!-- 执行按钮 -->
          <div v-if="selected?.file === t.file" class="mt-3 pt-3 border-t border-border">
            <div v-if="t.params.length > 0" class="flex flex-col gap-2 mb-3">
              <div v-for="p in t.params" :key="p.name" class="flex flex-col gap-1">
                <label class="text-xs text-text-secondary">{{ p.ask || p.name }}</label>
                <input
                  v-model="params[p.name]"
                  type="text"
                  :placeholder="p.ask || p.name"
                  class="px-3 py-2 bg-surface border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
                  @keydown.enter="startWorkflow"
                />
              </div>
            </div>
            <button
              @click="startWorkflow"
              :disabled="running"
              class="w-full py-2.5 rounded-[10px] font-semibold text-sm border-none cursor-pointer transition-all"
              :class="running ? 'bg-white/[0.06] text-text-secondary cursor-not-allowed' : 'bg-accent text-white hover:shadow-[0_4px_16px_rgba(124,138,255,0.3)]'"
            >
              {{ running ? '执行中…' : '▶ 开始执行' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ====== YAML 编辑弹窗 ====== -->
    <div v-if="editing" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(0,0,0,0.6)">
      <div class="bg-surface border border-border rounded-[16px] p-6 w-full max-w-2xl mx-4 max-h-[85vh] flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <span class="font-semibold text-sm">编辑模板：{{ editing.file }}</span>
          <button @click="editing = null" class="text-text-secondary hover:text-text bg-transparent border-none cursor-pointer text-lg">×</button>
        </div>
        <textarea
          v-model="editContent"
          class="flex-1 min-h-[300px] px-4 py-3 bg-surface border border-border rounded-[10px] text-text text-sm font-mono outline-none focus:border-accent resize-y"
          placeholder="YAML 内容…"
        ></textarea>
        <div class="flex gap-2 justify-end">
          <button @click="editing = null" class="px-4 py-2 bg-white/[0.06] text-text-secondary rounded-[8px] text-sm border-none cursor-pointer">取消</button>
          <button @click="saveEdit" :disabled="saving" class="px-4 py-2 bg-accent text-white rounded-[8px] text-sm font-semibold border-none cursor-pointer">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
        <div v-if="editError" class="text-xs text-danger">{{ editError }}</div>
      </div>
    </div>

    <!-- ====== 删除确认弹窗 ====== -->
    <div v-if="deleting" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(0,0,0,0.6)">
      <div class="bg-surface border border-border rounded-[16px] p-6 w-full max-w-sm mx-4 flex flex-col gap-4">
        <span class="font-semibold text-sm">确认删除</span>
        <p class="text-sm text-text-secondary">确定要删除模板「{{ deleting.name }}」吗？此操作不可恢复。</p>
        <div class="flex gap-2 justify-end">
          <button @click="deleting = null" class="px-4 py-2 bg-white/[0.06] text-text-secondary rounded-[8px] text-sm border-none cursor-pointer">取消</button>
          <button @click="doDelete" :disabled="saving" class="px-4 py-2 bg-danger text-white rounded-[8px] text-sm font-semibold border-none cursor-pointer">
            {{ saving ? '删除中…' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ====== 任务列表 ====== -->
    <div v-if="tasks.length > 0">
      <div class="flex items-center justify-between mb-3">
        <span class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px]">
          执行记录 ({{ tasks.length }})
        </span>
        <button
          v-if="archivedCount > 0"
          @click="showArchived = !showArchived"
          class="text-[11px] text-text-secondary hover:text-accent bg-transparent border-none cursor-pointer"
        >
          {{ showArchived ? '收起归档' : `📦 归档 (${archivedCount})` }}
        </button>
      </div>

      <div class="grid gap-2">
        <div
          v-for="t in tasks" :key="t.task_id"
          class="bg-surface border border-border rounded-[10px] overflow-hidden transition-all"
        >
          <!-- 标题栏（点击展开/折叠） -->
          <div
            @click="toggleExpand(t.task_id)"
            class="flex items-center justify-between p-3 cursor-pointer hover:bg-white/[0.02]"
          >
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-[10px] text-text-secondary">{{ expanded.has(t.task_id) ? '▼' : '▶' }}</span>
              <span class="text-sm font-semibold truncate">{{ t.template_name }}</span>
              <StatusBadge :status="t.status" />
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span class="text-[10px] text-text-secondary hidden sm:inline">{{ t.created_at?.slice(11, 16) || '' }}</span>
              <button
                v-if="t.status === 'done' || t.status === 'error'"
                @click.stop="doArchive(t.task_id)"
                class="text-[11px] text-text-secondary hover:text-accent bg-transparent border-none cursor-pointer px-1"
                title="归档"
              >📦</button>
            </div>
          </div>

          <!-- 展开内容 -->
          <div v-if="expanded.has(t.task_id)" class="px-3 pb-3 border-t border-border">
            <!-- 步骤条 -->
            <div class="flex gap-1.5 flex-wrap mt-3 mb-2">
              <span
                v-for="s in t.steps" :key="s.key"
                class="text-[10px] px-1.5 py-0.5 rounded-full"
                :class="stepClass(s.status)"
              >{{ s.label }}</span>
            </div>

            <div class="text-[11px] text-text-secondary">{{ t.progress }}</div>
            <div v-if="t.error" class="text-[11px] text-danger mt-1">{{ t.error }}</div>

            <!-- 完成结果展示 -->
            <div v-if="t.status === 'done' && t.outputs && t.outputs.length > 0" class="mt-3 pt-3 border-t border-border">
              <div class="text-xs font-semibold text-text mb-2">📋 产出</div>
              <div v-for="(o, i) in t.outputs" :key="i" class="mb-2 last:mb-0">
                <div v-if="o.type === 'text'" class="bg-white/[0.04] rounded-[6px] p-2">
                  <div class="text-[10px] text-text-secondary mb-1">{{ o.label }}</div>
                  <div class="text-xs text-text max-h-32 overflow-y-auto whitespace-pre-wrap break-all">{{ o.text?.slice(0, 2000) }}</div>
                </div>
                <div v-else-if="o.type === 'file'" class="bg-white/[0.04] rounded-[6px] p-2 flex items-center justify-between">
                  <div>
                    <div class="text-xs font-semibold text-text">{{ o.label }}</div>
                    <div class="text-[10px] text-text-secondary">{{ o.filename }}</div>
                  </div>
                  <a :href="`${API}/workflow/output/${t.task_id}/${encodeURIComponent(o.filename)}`"
                     :download="o.filename"
                     class="px-3 py-1.5 bg-accent text-white rounded-[6px] text-xs font-semibold no-underline hover:shadow-[0_2px_8px_rgba(124,138,255,0.3)] transition-all">
                    ⬇ 下载
                  </a>
                </div>
                <div v-else class="text-[10px] text-text-secondary">{{ o.label }} — 完成</div>
              </div>
            </div>

            <!-- 暂停交互 -->
            <div v-if="t.status === 'paused'" class="mt-3 pt-3 border-t border-border">
              <div v-if="t._pause_reason?.type === 'ask'" class="flex flex-col gap-2">
                <p class="text-xs text-text-secondary">{{ t._pause_reason.prompt }}</p>
                <div class="flex gap-2">
                  <input
                    v-model="askReplies[t.task_id]"
                    type="text"
                    placeholder="输入回复…"
                    class="flex-1 px-3 py-1.5 bg-surface border border-border rounded-[6px] text-text text-sm outline-none focus:border-accent"
                    @keydown.enter="doResume(t.task_id)"
                  />
                  <button @click="doResume(t.task_id)" class="px-4 py-1.5 bg-accent text-white rounded-[6px] text-xs font-semibold border-none cursor-pointer">继续</button>
                </div>
              </div>
              <div v-else class="flex items-center justify-between">
                <span class="text-xs text-text-secondary">{{ t._pause_reason?.prompt || '等待操作' }}</span>
                <button @click="doResume(t.task_id)" class="px-4 py-1.5 bg-accent text-white rounded-[6px] text-xs font-semibold border-none cursor-pointer">继续</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import StatusBadge from '../components/TaskStatusBadge.vue'

const API = (() => {
  const raw = localStorage.getItem('settings-storage')
  if (raw) {
    try {
      const data = JSON.parse(raw)
      const base = data?.apiBase || ''
      if (base) return base.replace(/\/+$/, '')
    } catch {}
  }
  return typeof window !== 'undefined' ? window.location.origin : ''
})()

// 创建
const createText = ref('')
const creating = ref(false)
const createError = ref('')
const createSuccess = ref('')

// 模板
const templates = ref([])
const selected = ref(null)
const params = ref({})
const loading = ref(false)

// 编辑
const editing = ref(null)
const editContent = ref('')
const editError = ref('')
const saving = ref(false)

// 删除
const deleting = ref(null)

// 任务
const tasks = ref([])
const archivedTasks = ref([])
const archivedCount = ref(0)
const expanded = ref(new Set())
const showArchived = ref(false)
const askReplies = ref({})
const running = ref(false)
let pollTimer = null

onMounted(() => {
  loadTemplates()
  pollTasks()
  pollTimer = setInterval(pollTasks, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

// ====== 模板加载 ======
async function loadTemplates() {
  loading.value = true
  try {
    const res = await fetch(`${API}/workflow/templates`)
    const data = await res.json()
    templates.value = data.templates || []
  } catch { /* 后端未启动 */ }
  finally { loading.value = false }
}

// ====== 白话文创建 ======
async function createFromText() {
  const text = createText.value.trim()
  if (!text || creating.value) return

  creating.value = true
  createError.value = ''
  createSuccess.value = ''

  try {
    const res = await fetch(`${API}/workflow/create-from-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: text }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '生成失败')

    createSuccess.value = `✅ 已创建「${data.name}」（${data.steps_count} 步）`
    createText.value = ''
    await loadTemplates()
    // 自动选中新模板
    selected.value = templates.value.find(t => t.file === data.file) || null
    if (selected.value) {
      params.value = {}
      selected.value.params.forEach(p => { params.value[p.name] = '' })
    }
  } catch (e) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}

// ====== 模板选择与执行 ======
function selectTemplate(t) {
  if (selected.value?.file === t.file) {
    selected.value = null
    params.value = {}
    return
  }
  selected.value = t
  params.value = {}
  t.params.forEach(p => { params.value[p.name] = '' })
}

async function startWorkflow() {
  if (!selected.value || running.value) return
  try {
    const res = await fetch(`${API}/workflow/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        yaml_file: selected.value.file,
        params: params.value,
      }),
    })
    if (!res.ok) {
      const err = await res.json()
      alert(err.detail || '启动失败')
      return
    }
    pollTasks()
  } catch (e) {
    alert('请求失败: ' + e.message)
  }
}

// ====== 模板编辑 ======
async function startEdit(t) {
  try {
    const res = await fetch(`${API}/workflow/templates/${encodeURIComponent(t.file)}`)
    const data = await res.json()
    editing.value = t
    editContent.value = data.content
    editError.value = ''
  } catch (e) {
    alert('获取模板内容失败')
  }
}

async function saveEdit() {
  if (!editing.value || saving.value) return
  saving.value = true
  editError.value = ''
  try {
    const res = await fetch(`${API}/workflow/templates/${encodeURIComponent(editing.value.file)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: editContent.value }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '保存失败')
    }
    editing.value = null
    await loadTemplates()
  } catch (e) {
    editError.value = e.message
  } finally {
    saving.value = false
  }
}

// ====== 模板复制 ======
async function copyTemplate(t) {
  try {
    const res = await fetch(`${API}/workflow/templates/${encodeURIComponent(t.file)}/copy`, { method: 'POST' })
    if (res.ok) await loadTemplates()
  } catch {}
}

// ====== 模板删除 ======
function confirmDelete(t) {
  deleting.value = t
}

async function doDelete() {
  if (!deleting.value || saving.value) return
  saving.value = true
  try {
    const res = await fetch(`${API}/workflow/templates/${encodeURIComponent(deleting.value.file)}`, { method: 'DELETE' })
    if (res.ok) {
      if (selected.value?.file === deleting.value.file) {
        selected.value = null
        params.value = {}
      }
      deleting.value = null
      await loadTemplates()
    }
  } catch {} finally {
    saving.value = false
  }
}

// ====== 展开/折叠 ======
function toggleExpand(taskId) {
  if (expanded.value.has(taskId)) {
    expanded.value.delete(taskId)
  } else {
    expanded.value.add(taskId)
  }
  // 触发响应式更新
  expanded.value = new Set(expanded.value)
}

// ====== 归档 ======
async function doArchive(taskId) {
  try {
    await fetch(`${API}/workflow/archive/${taskId}`, { method: 'POST' })
    pollTasks()
  } catch {}
}

// ====== 任务轮询与交互 ======
async function pollTasks() {
  try {
    const url = `${API}/workflow/queue/status?show_archived=${showArchived.value}`
    const res = await fetch(url)
    const data = await res.json()
    tasks.value = data.tasks || []
    archivedTasks.value = data.archived || []
    archivedCount.value = data.stats?.archived || 0
    running.value = tasks.value.some(t => t.status === 'running' || t.status === 'pending')
    // 运行中的自动展开
    tasks.value.forEach(t => {
      if (t.status === 'running' || t.status === 'paused') {
        expanded.value.add(t.task_id)
      }
    })
    expanded.value = new Set(expanded.value)
  } catch {}
}

async function doResume(taskId) {
  const reply = askReplies.value[taskId] || ''
  try {
    await fetch(`${API}/workflow/resume/${taskId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: reply ? { reply } : {} }),
    })
    askReplies.value[taskId] = ''
    pollTasks()
  } catch {}
}

function stepClass(status) {
  return {
    'pending': 'bg-white/[0.04] text-text-secondary',
    'running': 'bg-accent/20 text-accent',
    'done': 'bg-green-500/20 text-green-400',
    'error': 'bg-red-500/20 text-red-400',
  }[status] || 'bg-white/[0.04] text-text-secondary'
}
</script>
