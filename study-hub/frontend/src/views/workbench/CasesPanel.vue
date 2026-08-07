<template>
  <section class="case-panel min-w-0" aria-labelledby="cases-panel-title">
    <header class="flex min-w-0 flex-wrap items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-[11px] font-medium uppercase tracking-[0.14em] text-text-secondary">Butler</p>
        <h2 id="cases-panel-title" class="mt-1 text-xl font-semibold">案件</h2>
        <p class="mt-1 text-sm text-text-secondary">只读查看案件事实、审查与验证记录。</p>
      </div>
      <button
        type="button"
        class="shrink-0 rounded-[8px] border border-border px-3 py-2 text-sm text-text-secondary transition-colors hover:border-accent hover:text-text disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="isLoading"
        @click="loadCases()"
      >
        刷新
      </button>
    </header>

    <div class="mt-5 grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(11rem,0.7fr)]">
      <label class="min-w-0 text-xs font-medium text-text-secondary" for="case-keyword">
        关键词
        <input
          id="case-keyword"
          v-model.trim="filters.q"
          type="search"
          placeholder="搜索 ID、标题或描述"
          class="mt-1.5 block w-full min-w-0 rounded-[8px] border border-border bg-bg px-3 py-2.5 text-sm text-text outline-none placeholder:text-text-secondary/70 focus:border-accent"
        >
      </label>
      <label class="min-w-0 text-xs font-medium text-text-secondary" for="case-status">
        状态
        <select id="case-status" v-model="filters.status" class="mt-1.5 block w-full min-w-0 rounded-[8px] border border-border bg-bg px-3 py-2.5 text-sm text-text outline-none focus:border-accent">
          <option value="">全部状态</option>
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </label>
      <div class="grid min-w-0 grid-cols-2 gap-3 sm:col-span-2 xl:col-span-1">
        <label class="min-w-0 text-xs font-medium text-text-secondary" for="case-type">
          类型
          <select id="case-type" v-model="filters.task_type" class="mt-1.5 block w-full min-w-0 rounded-[8px] border border-border bg-bg px-3 py-2.5 text-sm text-text outline-none focus:border-accent">
            <option value="">全部类型</option>
            <option v-for="option in typeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <label class="min-w-0 text-xs font-medium text-text-secondary" for="case-sort">
          更新时间
          <select id="case-sort" v-model="filters.sort_order" class="mt-1.5 block w-full min-w-0 rounded-[8px] border border-border bg-bg px-3 py-2.5 text-sm text-text outline-none focus:border-accent">
            <option value="desc">最新优先</option>
            <option value="asc">最早优先</option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="errorMessage" class="mt-5 rounded-[8px] border border-danger/40 bg-danger/10 p-4" role="alert">
      <p class="text-sm font-medium text-text">案件加载失败</p>
      <p class="mt-1 break-words text-sm text-text-secondary">{{ errorMessage }}</p>
      <button type="button" class="mt-3 rounded-[8px] border border-danger/50 px-3 py-2 text-sm text-text transition-colors hover:bg-danger/10" @click="loadCases()">
        重试
      </button>
    </div>

    <div v-else-if="isLoading && !hasLoaded" class="mt-5 space-y-3" aria-label="正在加载案件" aria-busy="true">
      <div v-for="item in 4" :key="item" class="h-28 animate-pulse rounded-[8px] border border-border bg-surface/60" />
    </div>

    <div v-else-if="hasLoaded && cases.length === 0" class="mt-5 rounded-[8px] border border-dashed border-border bg-bg p-8 text-center">
      <p class="text-sm font-medium text-text">没有匹配的案件</p>
      <p class="mt-1 text-sm text-text-secondary">调整筛选条件后再试。</p>
    </div>

    <div v-else class="mt-5 min-w-0">
      <div class="mb-3 flex min-w-0 items-center justify-between gap-3 text-xs text-text-secondary">
        <span>{{ pagination.total }} 个案件</span>
        <span v-if="isLoading" aria-live="polite">正在更新…</span>
      </div>
      <div class="min-w-0 space-y-3">
        <button
          v-for="item in cases"
          :key="item.id"
          type="button"
          class="block w-full min-w-0 overflow-hidden rounded-[8px] border border-border bg-surface p-4 text-left transition-colors hover:border-accent/60 hover:bg-surface-hover focus:border-accent focus:outline-none"
          @click="openCase(item)"
        >
          <div class="flex min-w-0 flex-wrap items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="flex min-w-0 flex-wrap items-center gap-2">
                <span class="max-w-full truncate font-medium text-text">{{ item.title || '未命名案件' }}</span>
                <span class="case-status shrink-0" :class="statusTone(item.status)">{{ item.status_label || '未知状态' }}</span>
              </div>
              <p class="mt-1 break-all text-xs text-text-secondary">{{ item.id }}</p>
            </div>
            <span class="shrink-0 text-xs text-text-secondary">{{ formatDate(item.updated_at) }}</span>
          </div>
          <div class="mt-3 flex min-w-0 flex-wrap gap-x-4 gap-y-1 text-xs text-text-secondary">
            <span>{{ item.task_type_label || item.task_type || '未知类型' }}</span>
            <span class="case-meta-chip">{{ item.mode_label || modeLabel(item.mode) }}</span>
            <span v-if="item.feature_code" class="break-all">{{ item.feature_code }}</span>
            <span>尝试 {{ item.attempt_count ?? 0 }} 次</span>
            <span v-if="item.current_role">角色：{{ item.current_role }}</span>
          </div>
        </button>
      </div>

      <nav v-if="pagination.total > pagination.page_size" class="mt-5 flex min-w-0 items-center justify-between gap-3" aria-label="案件分页">
        <button type="button" class="rounded-[8px] border border-border px-3 py-2 text-sm text-text-secondary hover:border-accent hover:text-text disabled:cursor-not-allowed disabled:opacity-40" :disabled="!pagination.has_previous || isLoading" @click="changePage(pagination.page - 1)">上一页</button>
        <span class="min-w-0 truncate text-xs text-text-secondary">第 {{ pagination.page }} 页 / 共 {{ totalPages }} 页</span>
        <button type="button" class="rounded-[8px] border border-border px-3 py-2 text-sm text-text-secondary hover:border-accent hover:text-text disabled:cursor-not-allowed disabled:opacity-40" :disabled="!pagination.has_next || isLoading" @click="changePage(pagination.page + 1)">下一页</button>
      </nav>
    </div>

    <Teleport to="body">
      <div v-if="selectedCase" class="fixed inset-0 z-50" role="presentation">
        <button type="button" class="absolute inset-0 h-full w-full cursor-default bg-black/60" aria-label="关闭案件详情" @click="closeCase" />
        <aside class="absolute inset-y-0 right-0 flex w-full max-w-xl min-w-0 flex-col overflow-hidden border-l border-border bg-surface shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="case-detail-title">
          <header class="flex min-w-0 items-start justify-between gap-3 border-b border-border p-5">
            <div class="min-w-0">
              <p class="text-[11px] font-medium uppercase tracking-[0.14em] text-text-secondary">案件详情</p>
              <h2 id="case-detail-title" class="mt-1 break-words text-lg font-semibold text-text">{{ selectedCase.title || '未命名案件' }}</h2>
              <p class="mt-1 break-all text-xs text-text-secondary">{{ selectedCase.id }}</p>
            </div>
            <button type="button" class="shrink-0 rounded-[8px] border border-border px-3 py-2 text-sm text-text-secondary hover:border-accent hover:text-text" aria-label="关闭详情" @click="closeCase">关闭</button>
          </header>

          <div class="min-w-0 flex-1 overflow-y-auto p-5">
            <div v-if="detailLoading" class="space-y-3" aria-busy="true">
              <div v-for="item in 5" :key="item" class="h-16 animate-pulse rounded-[8px] bg-bg" />
            </div>
            <div v-else-if="detailError" class="rounded-[8px] border border-danger/40 bg-danger/10 p-4" role="alert">
              <p class="text-sm font-medium text-text">详情加载失败</p>
              <p class="mt-1 break-words text-sm text-text-secondary">{{ detailError }}</p>
              <button type="button" class="mt-3 rounded-[8px] border border-danger/50 px-3 py-2 text-sm text-text hover:bg-danger/10" @click="retryDetail">重试</button>
            </div>
            <template v-else>
              <section class="min-w-0 border-b border-border pb-5">
                <div class="flex min-w-0 flex-wrap items-center gap-2">
                  <span class="case-status" :class="statusTone(selectedCase.status)">{{ selectedCase.status_label || '未知状态' }}</span>
                  <span class="case-meta-chip">{{ selectedCase.task_type_label || selectedCase.task_type || '未知类型' }}</span>
                  <span class="case-meta-chip">{{ selectedCase.mode_label || modeLabel(selectedCase.mode) }}</span>
                  <span class="case-meta-chip">{{ selectedCase.risk_level_label || selectedCase.risk_level || '未知风险级别' }}</span>
                </div>
                <p class="mt-4 whitespace-pre-wrap break-words text-sm leading-6 text-text-secondary">{{ selectedCase.description || '未提供描述。' }}</p>
                <dl class="mt-4 grid min-w-0 grid-cols-1 gap-3 text-xs sm:grid-cols-2">
                  <div><dt class="text-text-secondary">创建时间</dt><dd class="mt-1 break-words text-text">{{ formatDate(selectedCase.created_at) }}</dd></div>
                  <div><dt class="text-text-secondary">更新时间</dt><dd class="mt-1 break-words text-text">{{ formatDate(selectedCase.updated_at) }}</dd></div>
                  <div><dt class="text-text-secondary">当前角色</dt><dd class="mt-1 break-words text-text">{{ selectedCase.current_role || '未分配' }}</dd></div>
                  <div><dt class="text-text-secondary">尝试次数</dt><dd class="mt-1 text-text">{{ selectedCase.attempt_count ?? 0 }}</dd></div>
                </dl>
              </section>

              <section v-if="contextEntries.length" class="case-detail-section">
                <h3 class="case-detail-heading">上下文来源</h3>
                <dl class="space-y-3">
                  <div v-for="entry in contextEntries" :key="entry.key" class="min-w-0">
                    <dt class="text-xs text-text-secondary">{{ entry.label }}</dt>
                    <dd class="mt-1 whitespace-pre-wrap break-words text-sm text-text">{{ formatValue(entry.value) }}</dd>
                  </div>
                </dl>
              </section>

              <section class="case-detail-section">
                <h3 class="case-detail-heading">下一步</h3>
                <div v-if="selectedCase.next_action" class="rounded-[8px] border border-border bg-bg p-3">
                  <p class="mb-2 text-xs text-text-secondary">处理模式：{{ selectedCase.next_action.mode_label || modeLabel(selectedCase.next_action.mode || selectedCase.mode) }}</p>
                  <p class="break-words text-sm text-text">{{ selectedCase.next_action.summary || selectedCase.next_action.kind || '未提供建议' }}</p>
                  <p v-if="selectedCase.next_action.required?.length" class="mt-2 break-words text-xs text-text-secondary">需要：{{ selectedCase.next_action.required.join('、') }}</p>
                </div>
                <p v-else class="text-sm text-text-secondary">暂无下一步记录。</p>
              </section>

              <section class="case-detail-section">
                <h3 class="case-detail-heading">事实时间线</h3>
                <div v-if="selectedCase.events?.length" class="space-y-3">
                  <article v-for="event in selectedCase.events" :key="`${event.id}-${event.created_at}`" class="case-timeline-item">
                    <div class="flex min-w-0 flex-wrap items-start justify-between gap-2">
                      <p class="break-words text-sm font-medium text-text">{{ event.summary || event.type }}</p>
                      <time class="shrink-0 text-xs text-text-secondary">{{ formatDate(event.created_at) }}</time>
                    </div>
                    <p class="mt-1 break-all text-xs text-text-secondary">{{ event.type }} · {{ event.actor || '未知执行者' }}</p>
                    <pre v-if="hasValue(event.payload)" class="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-[6px] bg-surface p-2 text-[11px] leading-5 text-text-secondary">{{ formatValue(event.payload) }}</pre>
                  </article>
                </div>
                <p v-else class="text-sm text-text-secondary">暂无事件记录。</p>
              </section>

              <section class="case-detail-section">
                <h3 class="case-detail-heading">文件</h3>
                <ul v-if="selectedCase.files?.length" class="space-y-2">
                  <li v-for="file in selectedCase.files" :key="file" class="break-all rounded-[6px] bg-bg px-3 py-2 font-mono text-xs text-text">{{ file }}</li>
                </ul>
                <p v-else class="text-sm text-text-secondary">暂无文件记录。</p>
              </section>

              <section v-for="section in factSections" :key="section.key" class="case-detail-section">
                <h3 class="case-detail-heading">{{ section.label }}</h3>
                <div v-if="selectedCase[section.key]?.length" class="space-y-3">
                  <article v-for="(record, index) in selectedCase[section.key]" :key="record.id || `${section.key}-${index}`" class="rounded-[8px] border border-border bg-bg p-3">
                    <div class="flex min-w-0 flex-wrap items-start justify-between gap-2">
                      <p class="break-words text-sm font-medium text-text">{{ record.summary || record.evidence || record.action || record.verdict || record.evidence_type || section.label }}</p>
                      <time v-if="record.created_at" class="shrink-0 text-xs text-text-secondary">{{ formatDate(record.created_at) }}</time>
                    </div>
                    <p v-if="record.result || record.learned || record.location || record.response" class="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-text-secondary">{{ record.result || record.learned || record.location || record.response }}</p>
                    <p v-if="record.files?.length" class="mt-2 whitespace-pre-wrap break-words font-mono text-xs text-text-secondary">{{ record.files.join('\n') }}</p>
                    <pre class="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-text-secondary">{{ formatRecord(record, section.key) }}</pre>
                  </article>
                </div>
                <p v-else class="text-sm text-text-secondary">暂无{{ section.label }}。</p>
              </section>
            </template>
          </div>
        </aside>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { getCase, getCases, WorkbenchApiError } from '../../services/workbench.js'

const statusOptions = [
  ['received', '已接收'], ['located', '已定位'], ['investigating', '调查中'], ['awaiting_approval', '待审批'],
  ['implementing', '执行中'], ['auditing', '待审查'], ['verifying', '验证中'], ['completed', '已完成'],
  ['blocked', '已阻塞'], ['cancelled', '已取消'], ['archived', '已归档'],
].map(([value, label]) => ({ value, label }))

const typeOptions = [
  ['bug', '故障排查'], ['change', '变更'], ['research', '调研'], ['health_check', '健康检查'],
  ['deploy', '部署'], ['memory_update', '记忆更新'],
].map(([value, label]) => ({ value, label }))

const filters = reactive({ status: '', task_type: '', q: '', sort_order: 'desc' })
const cases = ref([])
const selectedCase = ref(null)
const pagination = ref({ page: 1, page_size: 20, total: 0, has_next: false, has_previous: false })
const isLoading = ref(false)
const hasLoaded = ref(false)
const errorMessage = ref('')
const detailLoading = ref(false)
const detailError = ref('')
const currentPage = ref(1)
let listController = null
let detailController = null
let filterTimer = null
let listRequestToken = 0

const totalPages = computed(() => Math.max(1, Math.ceil(pagination.value.total / pagination.value.page_size)))
const contextLabels = {
  project_index_hits: '项目索引命中', owner_files: '负责文件', memory_summary: '记忆摘要', memory_sources: '记忆来源',
  memory_freshness: '记忆新鲜度', location_notes: '定位记录', task_card: '任务卡', task_card_handoff: '任务卡交接',
  report: '执行报告', change: '变更记录', audit: '审查记录', validation: '验证记录',
}
const contextEntries = computed(() => {
  const context = selectedCase.value?.context || {}
  return Object.keys(contextLabels)
    .filter((key) => context[key] !== undefined && context[key] !== null)
    .map((key) => ({ key, label: contextLabels[key], value: context[key] }))
})
const factSections = [
  { key: 'attempts', label: '尝试记录' },
  { key: 'changes', label: '变更记录' },
  { key: 'audits', label: '审查证据' },
  { key: 'validations', label: '验证证据' },
  { key: 'evidence', label: '文件证据' },
  { key: 'approvals', label: '审批记录' },
  { key: 'memory_drafts', label: '记忆草稿' },
]

function statusTone(status) {
  return {
    received: 'case-status--neutral', located: 'case-status--neutral', investigating: 'case-status--accent',
    awaiting_approval: 'case-status--warn', implementing: 'case-status--accent', auditing: 'case-status--warn',
    verifying: 'case-status--accent', completed: 'case-status--success', blocked: 'case-status--danger',
    cancelled: 'case-status--danger', archived: 'case-status--neutral',
  }[status] || 'case-status--unknown'
}

function modeLabel(mode) {
  return mode === 'simple' ? '简单逻辑' : mode === 'complex' ? '复杂逻辑' : '未知模式'
}

function formatDate(value) {
  if (!value) return '未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function hasValue(value) {
  return value !== undefined && value !== null && value !== '' && !(Array.isArray(value) && value.length === 0)
}

function formatValue(value) {
  if (typeof value === 'string') return value
  try { return JSON.stringify(value, null, 2) } catch { return String(value) }
}

function formatRecord(record, sectionKey) {
  const omitted = new Set(['id', 'case_id', 'created_at', 'summary', 'evidence', 'action', 'verdict', 'evidence_type', 'result', 'learned', 'location', 'response', 'files'])
  if (sectionKey === 'audits' && record.checklist) return `审查清单：\n${formatValue(record.checklist)}`
  if (sectionKey === 'validations' && hasValue(record.passed)) return `通过：${record.passed ? '是' : '否'}\n证据：${record.evidence || '未提供'}`
  const details = Object.fromEntries(Object.entries(record).filter(([key, value]) => !omitted.has(key) && hasValue(value)))
  return Object.keys(details).length ? formatValue(details) : ''
}

function userError(error) {
  if (error instanceof WorkbenchApiError) return error.message
  return error?.message || '工作台服务暂时不可用，请稍后重试。'
}

async function loadCases({ resetPage = false } = {}) {
  if (resetPage) currentPage.value = 1
  listController?.abort()
  listController = new AbortController()
  const token = ++listRequestToken
  isLoading.value = true
  errorMessage.value = ''
  try {
    const data = await getCases({ ...filters, page: currentPage.value, page_size: 20, sort_by: 'updated_at' }, listController.signal)
    if (token !== listRequestToken) return
    cases.value = Array.isArray(data?.items) ? data.items : []
    pagination.value = { ...pagination.value, ...(data?.pagination || {}), page: data?.pagination?.page || currentPage.value }
    currentPage.value = pagination.value.page
    hasLoaded.value = true
  } catch (error) {
    if (error?.name === 'AbortError') return
    if (token !== listRequestToken) return
    cases.value = []
    errorMessage.value = userError(error)
    hasLoaded.value = true
  } finally {
    if (token === listRequestToken) isLoading.value = false
  }
}

function scheduleFilterLoad() {
  clearTimeout(filterTimer)
  filterTimer = setTimeout(() => loadCases({ resetPage: true }), filters.q ? 300 : 0)
}

function changePage(page) {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  currentPage.value = page
  loadCases()
}

async function openCase(item) {
  detailController?.abort()
  detailController = new AbortController()
  selectedCase.value = item
  detailLoading.value = true
  detailError.value = ''
  try {
    selectedCase.value = await getCase(item.id, detailController.signal)
  } catch (error) {
    if (error?.name === 'AbortError') return
    detailError.value = userError(error)
  } finally {
    if (selectedCase.value?.id === item.id) detailLoading.value = false
  }
}

function retryDetail() {
  if (selectedCase.value) openCase(selectedCase.value)
}

function closeCase() {
  detailController?.abort()
  selectedCase.value = null
  detailError.value = ''
  detailLoading.value = false
}

watch(() => [filters.status, filters.task_type, filters.q, filters.sort_order], scheduleFilterLoad)
onMounted(() => loadCases())
onBeforeUnmount(() => {
  clearTimeout(filterTimer)
  listController?.abort()
  detailController?.abort()
})
</script>

<style scoped>
.case-status,
.case-meta-chip {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  overflow-wrap: anywhere;
  border-radius: 999px;
  border: 1px solid transparent;
  padding: 0.18rem 0.5rem;
  font-size: 0.6875rem;
  line-height: 1.25;
}

.case-meta-chip {
  border-color: #2a2a3a;
  color: #8888a0;
}

.case-status--neutral { border-color: #2a2a3a; background: #22222f; color: #a0a0b0; }
.case-status--accent { border-color: rgba(124, 138, 255, 0.35); background: rgba(124, 138, 255, 0.1); color: #a5b0ff; }
.case-status--warn { border-color: rgba(245, 158, 11, 0.4); background: rgba(245, 158, 11, 0.1); color: #fbbf24; }
.case-status--success { border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.1); color: #34d399; }
.case-status--danger { border-color: rgba(255, 92, 122, 0.4); background: rgba(255, 92, 122, 0.1); color: #ff8097; }
.case-status--unknown { border-color: rgba(255, 255, 255, 0.2); background: rgba(255, 255, 255, 0.05); color: #c4c4d0; }

.case-detail-section { min-width: 0; border-bottom: 1px solid #2a2a3a; padding: 1.25rem 0; }
.case-detail-section:last-child { border-bottom: 0; }
.case-detail-heading { margin-bottom: 0.75rem; color: #e0e0e8; font-size: 0.875rem; font-weight: 600; }
.case-timeline-item { min-width: 0; border-left: 2px solid rgba(124, 138, 255, 0.5); padding-left: 0.75rem; }
</style>
