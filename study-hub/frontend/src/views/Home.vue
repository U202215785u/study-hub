<template>
  <WorkbenchFrame>
    <template #navigation>
      <div class="home-navigation">
        <CapsuleNavigation :search-text="searchInput" @update:search-text="updateSearchInput" @search="searchNow" @search-focus="openSearch" @search-close="closeSearch" @notify="showToast('暂无新通知')" @edit="beginEdit" />
        <WorkstationSearchPanel :open="searchExpanded" :groups="searchGroups" :loading="searchLoading" :error="searchError" :assistant="searchAssistant" @navigate="navigateSearchResult" @open-document="viewDocument" @retry="retrySearch" @close="closeSearch" />
      </div>
    </template>
    <template #greeting><GreetingBar /></template>

    <div class="home-dashboard-grid" data-visual-anchor="grid">
      <BentoDashboardGrid>
        <div v-for="widget in visibleWidgets" :key="widget.id" class="home-dashboard-grid__item" :data-module-id="widget.id" :style="widgetStyle(widget)">
          <component :is="registry[widget.id].component" v-bind="propsFor(widget.id)" v-on="listenersFor(widget.id)" />
        </div>
      </BentoDashboardGrid>
    </div>

    <template #footer>
      <footer class="home-footer"><span>v1.0</span><RouterLink to="/settings">月亮</RouterLink></footer>
    </template>
  </WorkbenchFrame>

  <DashboardEditor
    v-if="isEditing"
    :widgets="draft.widgets"
    @hide="hide"
    @show="show"
    @reorder="reorder"
    @save="save"
    @cancel="cancelEdit"
    @restore="restoreDefault"
  />

  <div v-if="reviewOpen" class="home-modal" role="presentation" @click.self="reviewOpen = false">
    <section class="home-modal__panel" role="dialog" aria-modal="true" aria-labelledby="review-title">
      <header><h2 id="review-title">每日复盘</h2><UiIconButton label="关闭每日复盘" variant="text" @click="reviewOpen = false">×</UiIconButton></header>
      <textarea v-model="reviewInput" aria-label="今日学习记录" placeholder="写下今天真正理解了什么..." />
      <div class="home-actions"><UiButton :loading="reviewLoading" @click="polishReview">AI 润色</UiButton><UiButton variant="secondary" :loading="reviewLoading" @click="weeklyReport">本周周报</UiButton><span>{{ reviewStatus }}</span></div>
      <MarkdownRenderer v-if="reviewResult" :content="reviewResult" />
    </section>
  </div>

  <div v-if="docModal" class="home-modal" role="presentation" @click.self="docModal = false">
    <section class="home-modal__panel" role="dialog" aria-modal="true" aria-labelledby="document-title">
      <header><h2 id="document-title">{{ docTitle }}</h2><UiIconButton label="关闭文档" variant="text" @click="docModal = false">×</UiIconButton></header>
      <MarkdownRenderer :content="docContent" />
      <footer><UiButton variant="secondary" @click="copyDocContent">复制全文</UiButton><UiButton @click="docModal = false">关闭</UiButton></footer>
    </section>
  </div>

  <div v-if="automationDialog && selectedAutomation" class="home-modal" role="presentation" @click.self="automationDialog = false">
    <section class="home-modal__panel" role="dialog" aria-modal="true" aria-labelledby="automation-title">
      <header><h2 id="automation-title">{{ selectedAutomation.name }}</h2><UiIconButton label="关闭自动化" variant="text" @click="automationDialog = false">×</UiIconButton></header>
      <p class="home-muted">{{ selectedAutomation.desc }}</p>
      <UiInput v-model="selectedAutomation.input" label="分享链接" :placeholder="selectedAutomation.placeholder" />
      <footer><UiButton :loading="selectedAutomation.loading" @click="runAutomation(selectedAutomation)">开始解析</UiButton><UiButton variant="secondary" @click="automationDialog = false">取消</UiButton></footer>
    </section>
  </div>

  <aside v-if="queuePanelOpen" class="home-drawer" aria-label="解析队列" @keydown.esc="queuePanelOpen = false">
    <header><h2>解析队列</h2><UiIconButton label="关闭队列" variant="text" @click="queuePanelOpen = false">×</UiIconButton></header>
    <div class="home-drawer__list"><div v-for="item in queueItems" :key="item.id"><span>{{ item.title }}</span><UiButton v-if="item.status === 'error'" size="sm" variant="text" @click="retryTask(item.id)">重试</UiButton></div></div>
    <footer><UiButton variant="secondary" @click="clearQueue">清除已完成</UiButton><UiButton @click="refreshQueue">刷新</UiButton></footer>
  </aside>

  <div v-if="toast.visible" class="home-toast" :data-error="toast.error || undefined" role="status">{{ toast.message }}</div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import WorkstationSearchPanel from '../components/home/WorkstationSearchPanel.vue'
import { useSettingsStore } from '../stores/settings.js'
import { useHomeSearch } from '../composables/home/useHomeSearch.js'
import { useAutomationQueue } from '../composables/home/useAutomationQueue.js'
import { useKnowledgeDocuments } from '../composables/home/useKnowledgeDocuments.js'
import { useDailyReview } from '../composables/home/useDailyReview.js'
import { createHomeDashboardData, toLocalDateKey } from '../composables/home/useHomeDashboardData.js'
import { useDashboardLayout } from '../composables/home/useDashboardLayout.js'
import { DASHBOARD_REGISTRY } from '../design-system/layout/dashboardRegistry.js'
import { getWidgetGeometry } from '../design-system/layout/dashboardLayout.js'
import WorkbenchFrame from '../design-system/patterns/WorkbenchFrame.vue'
import CapsuleNavigation from '../design-system/patterns/CapsuleNavigation.vue'
import GreetingBar from '../design-system/patterns/GreetingBar.vue'
import BentoDashboardGrid from '../design-system/patterns/BentoDashboardGrid.vue'
import DashboardEditor from '../design-system/patterns/DashboardEditor.vue'
import UiButton from '../design-system/components/general/UiButton.vue'
import UiIconButton from '../design-system/components/general/UiIconButton.vue'
import UiInput from '../design-system/components/data-entry/UiInput.vue'

const router = useRouter()
const settings = useSettingsStore()
const registry = DASHBOARD_REGISTRY
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

const layoutApi = useDashboardLayout()
const { layout, draft, active, isEditing, beginEdit, hide, show, reorder, save, cancelEdit, restoreDefault } = layoutApi
const visibleWidgets = computed(() => active.value.widgets.filter((widget) => widget.visible).sort((a, b) => a.order - b.order))
function widgetStyle(widget) {
  const [columns, rows] = widget.size.split('x').map(Number)
  return { '--widget-columns': columns, '--widget-rows': rows, '--widget-height': `${getWidgetGeometry(widget.id, 1440).height}px` }
}

const search = useHomeSearch({ apiGet: settings.apiGet })
const { query: searchInput, expanded: searchExpanded, groups: searchGroups, loading: searchLoading, error: searchError, assistant: searchAssistant, open: openSearch, close: closeSearch, searchNow, scheduleSearch, retry: retrySearch, isSafeNavigation } = search
function updateSearchInput(value) { searchInput.value = value; scheduleSearch() }
function navigateSearchResult(navigation) {
  if (!isSafeNavigation(navigation)) return showToast('无法打开不受支持的搜索结果', true)
  closeSearch()
  router.push({ path: navigation.path, query: navigation.query || {} })
}

let queueApi
const knowledgeApi = useKnowledgeDocuments({ apiGet: settings.apiGet, apiPost: settings.apiPost, apiDelete: settings.apiDelete, apiUpload: settings.apiUpload, category: ref(''), notify: showToast, confirmAction: (message) => window.confirm(message), onReparseQueued: () => queueApi?.start() })
queueApi = useAutomationQueue({ apiGet: settings.apiGet, apiPost: settings.apiPost, apiDelete: settings.apiDelete, onCompleted: knowledgeApi.reload, notify: showToast, onApiKeyInvalid: (message) => window.alert(message) })
const { documents, activeDocument, reload: loadDocuments, open: viewDocument, copy: copyDocument } = knowledgeApi

function copyDocContent() {
  return copyDocument(activeDocument.value)
}

const { items: queueTasks, start: startQueuePoll, stop: stopQueuePoll, clear: clearQueue, retry: retryTask, refresh: fetchQueue } = queueApi
const queuePanelOpen = ref(false)
const refreshQueue = () => { fetchQueue(); showToast('已刷新') }
const mapper = createHomeDashboardData()
const queueItems = computed(() => mapper.mapQueue(queueTasks.value))
const knowledgeItems = computed(() => mapper.mapDocuments(documents.value))
const ddlTasks = ref([])
const ddlLoading = ref(true)
const ddlError = ref('')
async function loadDdlTasks() {
  ddlLoading.value = true
  ddlError.value = ''
  try {
    const data = await settings.apiGet('/ddl/tasks')
    ddlTasks.value = Array.isArray(data) ? data : []
  } catch {
    ddlTasks.value = []
    ddlError.value = '任务数据加载失败'
  } finally {
    ddlLoading.value = false
  }
}

const automationModules = ref([
  { id: 'douyin-summary', name: '抖音摘要', desc: '提取文本、识别资源并生成文档。', placeholder: '粘贴抖音分享链接...', input: '', loading: false },
  { id: 'bilibili-summary', name: 'B站解析', desc: '解析视频信息并提取语音文本。', placeholder: '粘贴 B 站分享链接...', input: '', loading: false },
  { id: 'xiaohongshu-summary', name: '小红书解析', desc: '提取笔记内容并归档。', placeholder: '粘贴小红书分享链接...', input: '', loading: false },
])
const automationDialog = ref(false)
const selectedAutomationId = ref('')
const selectedAutomation = computed(() => automationModules.value.find((item) => item.id === selectedAutomationId.value))
function openAutomation(id) { selectedAutomationId.value = id || automationModules.value[0].id; automationDialog.value = true }
async function runAutomation(module) {
  if (!module.input.trim()) return showToast('请粘贴分享链接', true)
  module.loading = true
  try {
    const data = await settings.apiPost('/automation/queue', { module_id: module.id, input: module.input.trim() })
    if (data.error) showToast(data.error, true)
    else { showToast('任务已提交'); automationDialog.value = false; startQueuePoll() }
  } catch { showToast('请求失败', true) } finally { module.loading = false }
}

const today = new Date()
const selectedDate = ref(toLocalDateKey(today))
const calendarMonth = `${today.getFullYear()}年 ${today.getMonth() + 1}月`
const calendarDays = computed(() => Array.from({ length: 7 }, (_, index) => {
  const date = new Date(today); date.setDate(today.getDate() - today.getDay() + index)
  const id = toLocalDateKey(date)
  return { date: id, label: String(date.getDate()), selected: id === selectedDate.value }
}))
const agendaItems = computed(() => mapper.mapAgenda(ddlTasks.value, selectedDate.value))
const taskItems = computed(() => mapper.mapTodayTasks(ddlTasks.value, selectedDate.value))
const heatmapCells = computed(() => mapper.mapActivityHeatmap({ tasks: ddlTasks.value, documents: documents.value, queue: queueTasks.value }, today))
const heatmapCaption = computed(() => `近 7 天：${heatmapCells.value.slice(-7).reduce((total, cell) => total + cell.count, 0)} 次记录`)

const creationItems = computed(() => mapper.mapLaunchers(settings.launcherItems))
function launchCreation(id) { const item = creationItems.value.find((entry) => entry.id === id); if (item?.url) openExternal(item.url); else router.push('/creator') }
const commandItems = computed(() => {
  const configured = Object.entries(settings.loadFromStorage('commands', {})).map(([id, item]) => ({ id, name: item.name || id, route: item.route || item.url }))
  return mapper.mapCommands(configured.length ? configured : [{ id: 'journal', name: '更新日志', route: '/journal' }, { id: 'wiki', name: '编译Wiki', route: '/wiki' }])
})
function runCommand(id) { const command = commandItems.value.find((item) => item.id === id); if (!command?.route) return; if (command.route.startsWith('/')) router.push(command.route); else openExternal(command.route) }
const workflowSteps = [{ id: 'collect', label: '网页输入', status: 'running' }, { id: 'execute', label: '执行', status: 'pending' }, { id: 'output', label: '输出', status: 'pending' }]
function runWorkflow(id) { router.push(id === 'output' ? '/creator' : '/workflow') }

const reviewOpen = ref(false)
const review = useDailyReview({ apiPost: settings.apiPost, apiGet: settings.apiGet, notify: showToast })
const { input: reviewInput, loading: reviewLoading, status: reviewStatus, result: reviewResult, polish: polishReview, weeklyReport, loadHistory: loadReviewHistory } = review
const docModal = computed({ get: () => Boolean(activeDocument.value), set: (value) => { if (!value) activeDocument.value = null } })
const docTitle = computed(() => activeDocument.value?.title || '')
const docContent = computed(() => activeDocument.value?.content || '')

function propsFor(id) {
  const props = {
    'work-heatmap': { cells: heatmapCells.value, caption: heatmapCaption.value, loading: ddlLoading.value, error: ddlError.value },
    'calendar-agenda': { days: calendarDays.value, agenda: agendaItems.value, monthLabel: calendarMonth, loading: ddlLoading.value, error: ddlError.value },
    'today-focus': { tasks: taskItems.value, dateLabel: `${String(today.getMonth() + 1).padStart(2, '0')}月${String(today.getDate()).padStart(2, '0')}日`, loading: ddlLoading.value, error: ddlError.value },
    'automation-queue': { items: queueItems.value }, knowledge: { items: knowledgeItems.value },
    'daily-memory': { title: '今日手账' }, 'quick-command': { commands: commandItems.value },
    'creation-entry': { items: creationItems.value }, 'quick-workflow': { steps: workflowSteps },
  }
  return props[id] || {}
}
function listenersFor(id) {
  return {
    'calendar-agenda': { select: (date) => { selectedDate.value = date }, open: () => router.push('/ddl') },
    'today-focus': { select: () => router.push('/ddl') },
    'automation-queue': { open: () => { queuePanelOpen.value = true }, retry: retryTask, create: () => openAutomation() },
    knowledge: { open: viewDocument }, 'daily-memory': { open: () => { reviewOpen.value = true } },
    'quick-command': { run: runCommand }, 'creation-entry': { open: launchCreation }, 'quick-workflow': { run: runWorkflow },
  }[id] || {}
}

onMounted(async () => {
  await Promise.all([loadDocuments(), loadReviewHistory(), loadDdlTasks()])
  startQueuePoll()
})
onUnmounted(() => { stopQueuePoll(); clearTimeout(toastTimer) })
</script>

<style scoped>
.home-dashboard-grid { width: calc(100% + 12px); margin-top: 20px; margin-left: -6px; }
.home-navigation { position: relative; }
.home-navigation :deep(.workstation-search-panel) { top: 105px; right: max(24px, calc((100vw - 1320px) / 2)); }
.home-dashboard-grid :deep(.bento-dashboard-grid) { grid-auto-flow: row dense; }
.home-dashboard-grid__item { min-width: 0; height: var(--widget-height); grid-column: span var(--widget-columns); grid-row: span var(--widget-rows); align-self: start; }
.home-footer { display: flex; width: calc(100% - 92px); align-items: center; justify-content: space-between; margin: 25px 46px 0; padding-bottom: 20px; color: #8b9186; font-size: 12px; }
.home-footer a { display: inline-flex; height: 34px; align-items: center; border-radius: 18px; padding: 0 17px; background: #d7ff63; color: #11140f; font-weight: 800; text-decoration: none; }
.home-modal { position: fixed; z-index: 100; inset: 0; display: grid; place-items: center; padding: 24px; background: rgb(0 0 0 / 68%); }
.home-modal__panel { display: grid; width: min(680px, 100%); max-height: 86vh; box-sizing: border-box; gap: 16px; overflow: auto; border: 1px solid rgb(245 246 238 / 20%); border-radius: 18px; padding: 20px; background: #1b1d1a; box-shadow: var(--ui-shadow-overlay); }
.home-modal__panel header, .home-modal__panel footer, .home-drawer header, .home-drawer footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.home-modal__panel h2, .home-drawer h2 { margin: 0; color: #f5f6ee; font-size: 18px; }
.home-modal__panel textarea { min-height: 140px; resize: vertical; border: 1px solid rgb(245 246 238 / 20%); border-radius: 10px; padding: 12px; background: #10140f; color: #f5f6ee; font: 14px/1.5 var(--ui-font-sans); }
.home-actions { display: flex; align-items: center; gap: 8px; }.home-actions span,.home-muted{color:#8b9186;font-size:12px}.home-error{color:#ff6b78}
.home-drawer { position: fixed; z-index: 95; top: 0; right: 0; bottom: 0; display: grid; width: min(420px, 94vw); box-sizing: border-box; grid-template-rows: auto 1fr auto; gap: 16px; border-left: 1px solid rgb(245 246 238 / 20%); padding: 20px; background: #1b1d1a; box-shadow: var(--ui-shadow-overlay); }
.home-drawer__list { display: grid; align-content: start; gap: 8px; overflow: auto; }.home-drawer__list>div{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgb(245 246 238 / 12%);padding:12px 0;color:#d9ddcf;font-size:12px}
.home-toast { position: fixed; z-index: 120; right: 24px; bottom: 24px; border: 1px solid rgb(245 246 238 / 20%); border-radius: 10px; padding: 12px 16px; background: #252824; color: #f5f6ee; box-shadow: var(--ui-shadow-overlay); font-size: 12px; }.home-toast[data-error='true']{color:#ff6b78}
</style>
