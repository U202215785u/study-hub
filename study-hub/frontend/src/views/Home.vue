<template>
  <section class="home-dashboard" aria-labelledby="home-title">
    <header class="home-dashboard__header">
      <div>
        <p class="home-dashboard__eyebrow">STUDY HUB / WORKSPACE</p>
        <h1 id="home-title">学习中枢</h1>
        <p class="home-dashboard__subtitle">把今天要理解、整理和输出的内容放在一个安静的工作台里。</p>
      </div>
      <nav class="home-dashboard__quick-nav" aria-label="首页快捷入口">
        <RouterLink to="/kb">知识库</RouterLink>
        <RouterLink to="/learning">学习路线</RouterLink>
        <RouterLink to="/creator">创作中心</RouterLink>
        <UiButton variant="secondary" size="sm" @click="reviewOpen = true">每日复盘</UiButton>
      </nav>
    </header>

    <form class="home-search" role="search" @submit.prevent="doSearch">
      <UiSelect v-model="searchMode" class="home-search__mode" label="搜索模式" :options="searchModeOptions" />
      <UiInput v-model="searchInput" data-home-search-input label="搜索内容" placeholder="搜索知识、任务或命令" />
      <UiSelect v-model="searchCategory" label="分类" :options="categoryOptions" />
      <UiButton data-home-search-primary="true" type="button" size="lg" @click="doSearch">搜索</UiButton>
    </form>

    <UiWidgetFrame v-if="searchResult" class="home-search-result" title="搜索结果" :loading="searchLoading" :error="searchError" :empty="false" :description="searchSources ? `来源：${searchSources}` : ''">
      <MarkdownRenderer v-if="searchAnswer" :content="searchAnswer" />
      <p v-else-if="!searchError" class="home-dashboard__muted">没有找到可展示的结果。</p>
    </UiWidgetFrame>

    <UiDashboardGrid aria-label="首页工作台">
      <UiDashboardItem span="2x3"><TaskWidget :tasks="taskItems" @select="openAutomation" /></UiDashboardItem>
      <UiDashboardItem span="2x2"><CalendarWidget :days="calendarDays" :month-label="calendarMonth" @select="selectedDate = $event" /></UiDashboardItem>
      <UiDashboardItem span="2x2"><AutomationQueueWidget :items="queueItems" @open="queuePanelOpen = true" @retry="retryTask" /></UiDashboardItem>
      <UiDashboardItem span="2x1"><KnowledgeWidget :items="knowledgeItems" @open="viewDocument" /></UiDashboardItem>
      <UiDashboardItem span="2x2"><CreationWidget :items="creationItems" @open="launchCreation" /></UiDashboardItem>
      <UiDashboardItem span="2x1"><WorkflowWidget :steps="workflowSteps" @run="runWorkflow" /></UiDashboardItem>
    </UiDashboardGrid>

    <UiWidgetFrame v-if="reviewOpen" class="home-review" title="每日复盘" description="记录今天真正理解了什么，AI 会帮你整理成可回看的内容。">
      <textarea v-model="reviewInput" aria-label="今日学习记录" placeholder="写写今天学了什么…" />
      <div class="home-review__actions">
        <UiButton :loading="reviewLoading" @click="polishReview">AI 润色</UiButton>
        <UiButton variant="secondary" :loading="reviewLoading" @click="weeklyReport">生成本周周报</UiButton>
        <UiButton variant="text" @click="reviewOpen = false">收起</UiButton>
        <span class="home-dashboard__muted">{{ reviewStatus }}</span>
      </div>
      <MarkdownRenderer v-if="reviewResult" :content="reviewResult" />
      <div v-if="reviewHistory.length" class="home-review__history">
        <button v-for="item in reviewHistory.slice(0, 5)" :key="item.id" type="button" @click="viewReview(item)">{{ item.date }} · {{ (item.raw_text || '').slice(0, 42) }}</button>
      </div>
    </UiWidgetFrame>

    <div v-if="docModal" class="home-modal" role="presentation" @click.self="docModal = false">
      <section class="home-modal__panel" role="dialog" aria-modal="true" aria-labelledby="document-title">
        <header><h2 id="document-title">{{ docTitle }}</h2><UiIconButton label="关闭" variant="text" @click="docModal = false">×</UiIconButton></header>
        <MarkdownRenderer :content="docContent" />
        <footer><UiButton variant="secondary" @click="copyDocument(activeDocument)">复制全文</UiButton><UiButton @click="docModal = false">关闭</UiButton></footer>
      </section>
    </div>

    <div v-if="automationDialog && selectedAutomation" class="home-modal" role="presentation" @click.self="automationDialog = false">
      <section class="home-modal__panel" role="dialog" aria-modal="true" aria-labelledby="automation-title">
        <header><h2 id="automation-title">{{ selectedAutomation.name }}</h2><UiIconButton label="关闭" variant="text" @click="automationDialog = false">×</UiIconButton></header>
        <p class="home-dashboard__muted">{{ selectedAutomation.desc }}</p>
        <UiInput v-model="selectedAutomation.input" label="分享链接" :placeholder="selectedAutomation.placeholder" />
        <footer><UiButton :loading="selectedAutomation.loading" @click="runAutomation(selectedAutomation)">开始解析</UiButton><UiButton variant="secondary" @click="automationDialog = false">取消</UiButton></footer>
      </section>
    </div>

    <aside v-if="queuePanelOpen" class="home-drawer" aria-label="解析队列" @keydown.esc="queuePanelOpen = false">
      <header><h2>解析队列</h2><UiIconButton label="关闭队列" variant="text" @click="queuePanelOpen = false">×</UiIconButton></header>
      <div class="home-drawer__stats"><UiBadge status="neutral" :label="`待处理 ${queueStats.pending || 0}`" /><UiBadge status="info" :label="`进行中 ${queueStats.running || 0}`" /><UiBadge status="success" :label="`已完成 ${queueStats.done || 0}`" /><UiBadge status="danger" :label="`失败 ${queueStats.error || 0}`" /></div>
      <div class="home-drawer__list"><div v-for="item in queueItems" :key="item.id" class="home-drawer__item"><span>{{ item.title }}</span><UiButton v-if="item.status === 'error'" size="sm" variant="text" @click="retryTask(item.id)">重试</UiButton></div></div>
      <footer><UiButton variant="secondary" @click="clearQueue">清除已完成</UiButton><UiButton @click="refreshQueue">刷新</UiButton></footer>
    </aside>

    <div v-if="toast.visible" class="home-toast" :data-error="toast.error ? 'true' : undefined" role="status">{{ toast.message }}</div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '../stores/settings.js'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import {
  AutomationQueueWidget,
  CalendarWidget,
  CreationWidget,
  KnowledgeWidget,
  TaskWidget,
  UiBadge,
  UiButton,
  UiDashboardGrid,
  UiDashboardItem,
  UiIconButton,
  UiInput,
  UiSelect,
  UiWidgetFrame,
  WorkflowWidget,
} from '@study-ui'
import { useHomeSearch } from '../composables/home/useHomeSearch.js'
import { useAutomationQueue } from '../composables/home/useAutomationQueue.js'
import { useKnowledgeDocuments } from '../composables/home/useKnowledgeDocuments.js'
import { useDailyReview } from '../composables/home/useDailyReview.js'

const router = useRouter()
const settings = useSettingsStore()
const isElectron = Boolean(window.electronAPI)
const toast = ref({ visible: false, message: '', error: false })
let toastTimer
function showToast(message, error = false) {
  toast.value = { visible: true, message, error }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.visible = false }, 2500)
}
function openExternal(url) {
  if (isElectron) window.electronAPI.openExternal(url)
  else window.open(url, '_blank', 'noopener,noreferrer')
}

const categories = ref([])
const search = useHomeSearch({ apiPost: settings.apiPost, openExternal, loadCommands: () => settings.loadFromStorage('commands', {}), notify: showToast })
const { mode: searchMode, query: searchInput, category: searchCategory, loading: searchLoading, hasResult: searchResult, answer: searchAnswer, sources: searchSources, error: searchError, submit: doSearch } = search
const searchModeOptions = [{ value: 'ai', label: 'AI 推荐' }, { value: 'kb', label: '知识库' }, { value: 'web', label: '全网' }, { value: 'cmd', label: '命令' }]
const categoryOptions = computed(() => [{ value: '', label: '全部分类' }, ...categories.value.map((item) => ({ value: String(item.id), label: `${item.icon || ''} ${item.name}`.trim() }))])

let queueApi
const knowledgeApi = useKnowledgeDocuments({
  apiGet: settings.apiGet,
  apiPost: settings.apiPost,
  apiDelete: settings.apiDelete,
  apiUpload: settings.apiUpload,
  category: searchCategory,
  notify: showToast,
  confirmAction: (message) => window.confirm(message),
  onReparseQueued: () => queueApi?.start(),
})
queueApi = useAutomationQueue({ apiGet: settings.apiGet, apiPost: settings.apiPost, apiDelete: settings.apiDelete, onCompleted: knowledgeApi.reload, notify: showToast, onApiKeyInvalid: (message) => window.alert(message) })
const { documents, activeDocument, reload: loadDocuments, open: viewDocument, copy: copyDocument } = knowledgeApi
const { items: queueTasks, stats: queueStats, start: startQueuePoll, stop: stopQueuePoll, clear: clearQueue, retry: retryTask, refresh: fetchQueue } = queueApi
const queuePanelOpen = ref(false)
const refreshQueue = () => { fetchQueue(); showToast('已刷新') }
const queueItems = computed(() => queueTasks.value.map((item) => ({
  id: item.id || item.task_id,
  title: item.title || item.module_id || '自动化任务',
  status: item.status,
  progress: typeof (item.progressValue ?? item.percent ?? item.progress) === 'number' ? (item.progressValue ?? item.percent ?? item.progress) : 0,
})))
const knowledgeItems = computed(() => documents.value.slice(0, 8).map((item) => ({ id: item.id, title: item.title, meta: item.created_at?.slice(0, 10) || '最近', status: 'ready' })))

const automationModules = ref([
  { id: 'douyin-summary', name: '抖音摘要', desc: '提取文本、识别资源并生成文档', placeholder: '粘贴抖音分享链接…', input: '', loading: false },
  { id: 'bilibili-summary', name: 'B 站解析', desc: '解析视频信息并提取语音文本', placeholder: '粘贴 B 站分享链接…', input: '', loading: false },
  { id: 'xiaohongshu-summary', name: '小红书解析', desc: '提取笔记内容并归档', placeholder: '粘贴小红书分享链接…', input: '', loading: false },
])
const taskItems = computed(() => automationModules.value.map((item) => ({ id: item.id, title: item.name, time: item.desc, status: item.loading ? 'running' : 'pending', progress: item.loading ? 42 : 0 })))
const automationDialog = ref(false)
const selectedAutomationId = ref('')
const selectedAutomation = computed(() => automationModules.value.find((item) => item.id === selectedAutomationId.value))
function openAutomation(id) { selectedAutomationId.value = id; automationDialog.value = true }
async function runAutomation(module) {
  if (!module.input.trim()) return showToast('请粘贴分享链接', true)
  module.loading = true
  try {
    const data = await settings.apiPost('/automation/queue', { module_id: module.id, input: module.input.trim() })
    if (data.error) showToast(data.error, true)
    else { showToast('任务已提交'); automationDialog.value = false; startQueuePoll() }
  } catch {
    showToast('请求失败', true)
  } finally {
    module.loading = false
  }
}

const creationItems = computed(() => settings.launcherItems.map((item, index) => ({ id: `launcher-${index}`, title: item.name, thumbnail: '', kind: 'template', url: item.url })))
function launchCreation(id) {
  const index = Number(id.split('-')[1])
  const item = settings.launcherItems[index]
  if (item) openExternal(item.url)
}
const workflowSteps = [
  { id: 'collect', label: '收集', status: 'done' },
  { id: 'understand', label: '理解', status: 'done' },
  { id: 'organize', label: '整理', status: 'running' },
  { id: 'publish', label: '输出', status: 'pending' },
]
function runWorkflow(id) {
  const routes = { collect: '/kb', understand: '/learning', organize: '/workflow', publish: '/creator' }
  if (routes[id]) router.push(routes[id])
}

const today = new Date()
const calendarMonth = `${today.getFullYear()} 年 ${today.getMonth() + 1} 月`
const selectedDate = ref(today.toISOString().slice(0, 10))
const calendarDays = computed(() => Array.from({ length: new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate() }, (_, index) => {
  const date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(index + 1).padStart(2, '0')}`
  return { date, label: String(index + 1), selected: date === selectedDate.value, eventTones: date === selectedDate.value ? ['lime'] : [] }
}))

const reviewOpen = ref(false)
const review = useDailyReview({ apiPost: settings.apiPost, apiGet: settings.apiGet, notify: showToast })
const { input: reviewInput, loading: reviewLoading, status: reviewStatus, result: reviewResult, history: reviewHistory, polish: polishReview, weeklyReport, loadHistory: loadReviewHistory, view: viewReview } = review

const docModal = computed({ get: () => Boolean(activeDocument.value), set: (value) => { if (!value) activeDocument.value = null } })
const docTitle = computed(() => activeDocument.value?.title || '')
const docContent = computed(() => activeDocument.value?.content || '')

onMounted(async () => {
  await Promise.all([loadDocuments(), loadReviewHistory()])
  try { categories.value = await settings.apiGet('/categories') } catch { categories.value = [] }
  startQueuePoll()
})
onUnmounted(() => stopQueuePoll())
</script>

<style scoped>
.home-dashboard { display: grid; gap: var(--ui-space-6); max-width: 1480px; margin: 0 auto; }
.home-dashboard__header { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--ui-space-6); }
.home-dashboard__eyebrow { margin: 0 0 var(--ui-space-2); color: var(--ui-color-action); font: 700 11px/1 var(--ui-font-mono); letter-spacing: 0; }
.home-dashboard__header h1 { margin: 0; color: var(--ui-color-text-strong); font-size: 40px; line-height: 1.1; }
.home-dashboard__subtitle { max-width: 38rem; margin: var(--ui-space-3) 0 0; color: var(--ui-color-text-muted); font-size: 14px; }
.home-dashboard__quick-nav { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: var(--ui-space-2); }
.home-dashboard__quick-nav a { color: var(--ui-color-text-muted); font-size: 12px; text-decoration: none; }
.home-dashboard__quick-nav a:hover { color: var(--ui-color-action); }
.home-search { display: grid; grid-template-columns: 150px minmax(0, 1fr) 170px auto; align-items: end; gap: var(--ui-space-3); padding: var(--ui-space-4); border: 1px solid var(--ui-color-border); border-radius: var(--ui-radius-lg); background: var(--ui-color-surface); }
.home-search :deep(.ui-field) { min-width: 0; }
.home-search__mode :deep(.ui-field__label) { color: var(--ui-color-text-muted); }
.home-dashboard__muted { margin: 0; color: var(--ui-color-text-muted); font-size: 13px; }
.home-review { gap: var(--ui-space-4); }
.home-review textarea { width: 100%; min-height: 140px; box-sizing: border-box; resize: vertical; border: 1px solid var(--ui-color-border-strong); border-radius: var(--ui-radius-md); padding: var(--ui-space-3); background: var(--ui-color-canvas); color: var(--ui-color-text); font: 400 14px/1.5 var(--ui-font-sans); }
.home-review textarea:focus { outline: none; border-color: var(--ui-color-action); box-shadow: var(--ui-focus-ring); }
.home-review__actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--ui-space-2); }
.home-review__history { display: grid; gap: var(--ui-space-1); }
.home-review__history button { border: 0; border-bottom: 1px solid var(--ui-color-border); padding: var(--ui-space-2) 0; background: none; color: var(--ui-color-text-muted); text-align: left; cursor: pointer; }
.home-review__history button:hover { color: var(--ui-color-text-strong); }
.home-modal { position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; padding: var(--ui-space-4); background: rgb(0 0 0 / 64%); }
.home-modal__panel { display: grid; width: min(680px, 100%); max-height: min(760px, 90vh); gap: var(--ui-space-4); overflow: auto; border: 1px solid var(--ui-color-border-strong); border-radius: var(--ui-radius-lg); padding: var(--ui-space-5); background: var(--ui-color-surface); box-shadow: var(--ui-shadow-overlay); }
.home-modal__panel header, .home-modal__panel footer, .home-drawer header, .home-drawer footer { display: flex; align-items: center; justify-content: space-between; gap: var(--ui-space-3); }
.home-modal__panel h2, .home-drawer h2 { margin: 0; color: var(--ui-color-text-strong); font-size: 18px; }
.home-drawer { position: fixed; z-index: 70; top: 0; right: 0; bottom: 0; display: grid; width: min(420px, 94vw); grid-template-rows: auto auto 1fr auto; gap: var(--ui-space-4); border-left: 1px solid var(--ui-color-border-strong); padding: var(--ui-space-5); background: var(--ui-color-surface); box-shadow: var(--ui-shadow-overlay); }
.home-drawer__stats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ui-space-2); }
.home-drawer__list { display: grid; align-content: start; gap: var(--ui-space-1); overflow: auto; }
.home-drawer__item { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: var(--ui-space-3); border-bottom: 1px solid var(--ui-color-border); padding: var(--ui-space-3) 0; color: var(--ui-color-text); font-size: 13px; }
.home-drawer__item span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.home-toast { position: fixed; z-index: 100; right: var(--ui-space-5); bottom: var(--ui-space-5); max-width: min(380px, calc(100vw - 40px)); border: 1px solid var(--ui-color-border-strong); border-radius: var(--ui-radius-md); padding: var(--ui-space-3) var(--ui-space-4); background: var(--ui-color-surface-raised); color: var(--ui-color-text-strong); box-shadow: var(--ui-shadow-overlay); font-size: 13px; }
.home-toast[data-error='true'] { border-color: var(--ui-color-danger); color: var(--ui-color-danger); }
@media (max-width: 1023px) { .home-dashboard__header { align-items: flex-start; flex-direction: column; } .home-dashboard__quick-nav { justify-content: flex-start; } .home-search { grid-template-columns: repeat(2, minmax(0, 1fr)); } .home-search__mode, .home-search :deep(.ui-field:nth-child(2)) { grid-column: span 1; } .home-search :deep(.ui-button) { width: 100%; } }
@media (max-width: 767px) { .home-dashboard { gap: var(--ui-space-4); } .home-search { grid-template-columns: 1fr; padding: var(--ui-space-3); } .home-search > * { grid-column: auto !important; } .home-dashboard__header h1 { font-size: 30px; } .home-dashboard__subtitle { font-size: 13px; } .home-modal__panel { padding: var(--ui-space-4); } }
</style>
