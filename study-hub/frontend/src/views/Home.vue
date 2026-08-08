<template>
  <WorkbenchFrame ref="motionScope">
    <template #background><BentoBackground :static="isEditing" /></template>
    <template #navigation>
      <div class="home-navigation">
        <CapsuleNavigation
          data-home-motion="navigation"
          :search-text="searchInput"
          @update:search-text="updateSearchInput"
          @search="searchNow"
          @search-focus="openSearch"
          @search-close="closeSearch"
          @notify="showToast('暂无新通知')"
          @edit="beginEdit"
        />
        <WorkstationSearchPanel
          :open="searchExpanded"
          :groups="searchGroups"
          :loading="searchLoading"
          :error="searchError"
          :assistant="searchAssistant"
          @navigate="navigateSearchResult"
          @open-document="viewDocument"
          @retry="retrySearch"
          @close="closeSearch"
        />
      </div>
    </template>
    <template #greeting><GreetingBar data-home-motion="greeting" /></template>

    <div class="home-dashboard-grid" data-visual-anchor="grid">
      <BentoDashboardGrid ref="dashboardGrid" :data-grid-dragging="draggingWidget || undefined">
        <MotionWrapper
          v-for="(widget, index) in visibleWidgets"
          :key="widget.id"
          class="home-dashboard-grid__item"
          data-home-motion="widget"
          :data-module-id="widget.id"
          :data-flip-id="widget.id"
          :style="layoutStyle(widget)"
          :delay="index * 0.06"
          :while-hover="{ y: -2 }"
          :while-press="{ scale: 0.98 }"
        >
          <button
            v-if="isEditing"
            class="home-dashboard-grid__drag-handle"
            type="button"
            :aria-label="`拖拽${registry[widget.id].label}`"
            @pointerdown="startGridDrag($event, widget.id)"
          >⠿</button>
          <component :is="registry[widget.id].component" v-bind="propsFor(widget.id)" v-on="listenersFor(widget.id)" />
        </MotionWrapper>
      </BentoDashboardGrid>
    </div>

    <template #footer>
      <footer class="home-footer"><span>v1.0</span><RouterLink to="/settings">月亮</RouterLink></footer>
    </template>
  </WorkbenchFrame>

  <Transition name="home-editor">
    <DashboardEditor
      v-if="isEditing"
      :widgets="draft.widgets"
      :can-undo="canUndo"
      @hide="hideWithMotion"
      @show="showWithMotion"
      @reorder="reorderWithMotion"
      @undo="undoWithMotion"
      @save="save"
      @cancel="cancelWithMotion"
      @restore="restoreDefaultLayout"
    />
  </Transition>

  <Transition name="home-surface" @after-leave="restoreFocusAfterLeave">
    <div v-if="reviewOpen" class="home-modal" role="presentation" @click.self="closeReview">
    <section ref="reviewPanel" class="home-modal__panel" role="dialog" aria-modal="true" aria-labelledby="review-title">
      <header><h2 id="review-title">每日复盘</h2><UiIconButton label="关闭每日复盘" variant="text" @click="reviewOpen = false">×</UiIconButton></header>
      <textarea v-model="reviewInput" aria-label="今日学习记录" placeholder="写下今天真正理解了什么..." />
      <div class="home-actions"><UiButton :loading="reviewLoading" @click="polishReview">AI 润色</UiButton><UiButton variant="secondary" :loading="reviewLoading" @click="weeklyReport">本周周报</UiButton><span>{{ reviewStatus }}</span></div>
      <MarkdownRenderer v-if="reviewResult" :content="reviewResult" />
    </section>
    </div>
  </Transition>

  <Transition name="home-surface" @after-leave="restoreFocusAfterLeave">
    <div v-if="docModal" class="home-modal" role="presentation" @click.self="closeDocument">
    <section ref="documentPanel" class="home-modal__panel home-document-modal__panel" role="dialog" aria-modal="true" aria-labelledby="document-title">
      <header><h2 id="document-title">{{ docTitle }}</h2><UiIconButton label="关闭文档" variant="text" @click="docModal = false">×</UiIconButton></header>
      <div class="home-document-modal__reader">
        <DocumentReader
          :summary-markdown="docContent"
          :tutorial-markdown="docTutorialContent"
          :tutorial-status="docTutorialStatus"
          :tutorial-reason="docTutorialReason"
          @active-content="docCopyContent = $event"
        />
      </div>
      <footer><UiButton variant="secondary" @click="copyDocContent">复制全文</UiButton><UiButton @click="docModal = false">关闭</UiButton></footer>
    </section>
    </div>
  </Transition>

  <Transition name="home-surface" @after-leave="restoreFocusAfterLeave">
    <div v-if="automationDialog && selectedAutomation" class="home-modal" role="presentation" @click.self="closeAutomation">
    <section ref="automationPanel" class="home-modal__panel" role="dialog" aria-modal="true" aria-labelledby="automation-title">
      <header><h2 id="automation-title">{{ selectedAutomation.name }}</h2><UiIconButton label="关闭自动化" variant="text" @click="automationDialog = false">×</UiIconButton></header>
      <p class="home-muted">{{ selectedAutomation.desc }}</p>
      <UiInput v-model="selectedAutomation.input" label="分享链接" :placeholder="selectedAutomation.placeholder" />
      <label v-if="selectedAutomation.id === 'douyin-summary'" class="home-tutorial-option">
        <input v-model="selectedAutomation.includeTutorial" type="checkbox">
        <span>同时生成图文教程</span>
      </label>
      <footer><UiButton :loading="selectedAutomation.loading" @click="runAutomation(selectedAutomation)">开始解析</UiButton><UiButton variant="secondary" @click="automationDialog = false">取消</UiButton></footer>
    </section>
    </div>
  </Transition>

  <Transition name="home-drawer" @after-leave="restoreFocusAfterLeave">
    <div v-if="queuePanelOpen" class="home-drawer-backdrop" role="presentation" @click.self="closeQueue">
    <aside ref="queuePanel" class="home-drawer" aria-label="解析队列" @keydown.esc="closeQueue">
      <header><h2>解析队列</h2><UiIconButton label="关闭队列" variant="text" @click="closeQueue">×</UiIconButton></header>
      <div class="home-drawer__list"><div v-for="item in queueItems" :key="item.id"><span>{{ item.title }}</span><UiButton v-if="item.status === 'error'" size="sm" variant="text" @click="retryTask(item.id)">重试</UiButton></div></div>
      <footer><UiButton variant="secondary" @click="clearQueue">清除已完成</UiButton><UiButton @click="refreshQueue">刷新</UiButton></footer>
    </aside>
    </div>
  </Transition>

  <Transition name="home-drawer" @after-leave="restoreFocusAfterLeave">
    <div v-if="knowledgePanelOpen" class="home-drawer-backdrop" role="presentation" @click.self="closeKnowledge">
    <aside ref="knowledgePanel" class="home-drawer knowledge-drawer" aria-label="知识库" @keydown.esc="closeKnowledge">
      <header><h2>知识库</h2><UiIconButton label="关闭知识库" variant="text" @click="closeKnowledge">×</UiIconButton></header>
      <div class="home-drawer__list knowledge-drawer__list">
        <div v-if="!documents.length" class="knowledge-drawer__empty">知识库暂无文档</div>
        <div v-for="item in documents" :key="item.id" class="knowledge-drawer__item" :data-knowledge-drawer-id="item.id">
          <button type="button" class="knowledge-drawer__title" @click="openKnowledgeDocument(item.id)">{{ item.title || '未命名文档' }}</button>
          <span class="knowledge-drawer__actions">
            <UiButton size="xs" shape="pill" @click="copyKnowledgeDocument(item.id)">复制</UiButton>
            <UiButton size="xs" shape="pill" variant="danger" @click="removeDocument(item.id)">删除</UiButton>
          </span>
        </div>
      </div>
      <footer><UiButton variant="secondary" @click="loadDocuments">刷新</UiButton><UiButton @click="closeKnowledge">关闭</UiButton></footer>
    </aside>
    </div>
  </Transition>

  <Transition name="home-toast">
    <div v-if="toast.visible" class="home-toast" :data-error="toast.error || undefined" role="status">{{ toast.message }}</div>
  </Transition>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import DocumentReader from '../components/DocumentReader.vue'
import { useSettingsStore } from '../stores/settings.js'
import WorkstationSearchPanel from '../components/home/WorkstationSearchPanel.vue'
import { useHomeSearch } from '../composables/home/useHomeSearch.js'
import { useAutomationQueue } from '../composables/home/useAutomationQueue.js'
import { useKnowledgeDocuments } from '../composables/home/useKnowledgeDocuments.js'
import { useDailyReview } from '../composables/home/useDailyReview.js'
import { createHomeDashboardData, toLocalDateKey } from '../composables/home/useHomeDashboardData.js'
import { useHeatmap } from '../composables/heatmap/useHeatmap.js'
import { useDashboardLayout } from '../composables/home/useDashboardLayout.js'
import { createGridDrag } from '../composables/home/useGridDrag.js'
import { useGsap, readCssTimeSeconds } from '../composables/useGsap.js'
import { playHomeEntrance } from '../composables/home/useHomeEntrance.js'
import { createDashboardFlip } from '../composables/home/useDashboardFlip.js'
import { Flip, gsap } from '../lib/gsap.js'
import { DASHBOARD_REGISTRY } from '../design-system/layout/dashboardRegistry.js'
import { GRID_GAP, GRID_ROW_HEIGHT, layoutStyle } from '../design-system/layout/dashboardLayout.js'
import WorkbenchFrame from '../design-system/patterns/WorkbenchFrame.vue'
import MotionWrapper from '../design-system/patterns/MotionWrapper.vue'
import CapsuleNavigation from '../design-system/patterns/CapsuleNavigation.vue'
import GreetingBar from '../design-system/patterns/GreetingBar.vue'
import BentoDashboardGrid from '../design-system/patterns/BentoDashboardGrid.vue'
import BentoBackground from '../design-system/patterns/BentoBackground.vue'
import DashboardEditor from '../design-system/patterns/DashboardEditor.vue'
import UiButton from '../design-system/components/general/UiButton.vue'
import UiIconButton from '../design-system/components/general/UiIconButton.vue'
import UiInput from '../design-system/components/data-entry/UiInput.vue'

const router = useRouter()
const settings = useSettingsStore()
const registry = DASHBOARD_REGISTRY
const motionScope = ref(null)
const isElectron = Boolean(window.electronAPI)
const toast = ref({ visible: false, message: '', error: false })
let toastTimer
function showToast(message, error = false) {
  if (!error && toast.value.visible && toast.value.error) return
  toast.value = { visible: true, message, error }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.visible = false }, 2500)
}
function openExternal(url) {
  if (isElectron) window.electronAPI.openExternal(url)
  else window.open(url, '_blank', 'noopener,noreferrer')
}

const layoutApi = useDashboardLayout()
const { layout, draft, active, isEditing, canUndo, beginEdit, hide: hideLayout, show: showLayout, move: moveLayout, undo, reorder: reorderLayout, save, cancelEdit: cancelEditLayout, restoreDefault } = layoutApi
const dashboardGrid = ref(null)
const draggingWidget = ref('')
let dashboardFlip = { run: async (mutate) => { mutate(); await nextTick() } }
const runDashboardMutation = (mutate) => dashboardFlip.run(mutate)
const hideWithMotion = (id) => runDashboardMutation(() => hideLayout(id))
const showWithMotion = (id) => runDashboardMutation(() => showLayout(id))
const reorderWithMotion = (id, targetOrder) => runDashboardMutation(() => reorderLayout(id, targetOrder))
const undoWithMotion = () => runDashboardMutation(() => undo())
const cancelWithMotion = () => runDashboardMutation(() => cancelEditLayout())
function restoreDefaultLayout() {
  if (window.confirm('将恢复默认布局并丢弃当前自定义布局，是否继续？')) runDashboardMutation(() => restoreDefault())
}
const visibleWidgets = computed(() => active.value.widgets.filter((widget) => widget.visible).sort((a, b) => a.order - b.order))
const gridDrag = createGridDrag({
  getGridRect: () => dashboardGrid.value?.$el?.getBoundingClientRect(),
  rowHeight: GRID_ROW_HEIGHT,
  gap: GRID_GAP,
  onStart: (id) => { draggingWidget.value = id },
  onEnd: (id, target) => {
    draggingWidget.value = ''
    runDashboardMutation(() => moveLayout(id, target))
  },
})
function startGridDrag(event, id) {
  try { event.currentTarget?.setPointerCapture?.(event.pointerId) } catch { /* Synthetic and unsupported pointers use the window listeners. */ }
  gridDrag.pointerDown(event, id)
}
function continueGridDrag(event) { gridDrag.pointerMove(event) }
function finishGridDrag(event) { gridDrag.pointerUp(event) }
function cancelGridDrag(event) { gridDrag.pointerCancel(event); draggingWidget.value = '' }

function targetsIn(scope) {
  return scope ? [...scope.querySelectorAll('.home-dashboard-grid__item')] : []
}

useGsap({
  scope: () => motionScope.value?.$el,
  setup: ({ gsap: scopedGsap, scope }) => {
    const duration = readCssTimeSeconds('--ui-duration-normal', scope || document.documentElement)
    dashboardFlip = createDashboardFlip({
      Flip,
      gsap: scopedGsap,
      getTargets: () => targetsIn(scope),
      nextTick,
      reducedMotion: false,
      duration,
    })
    return playHomeEntrance({ gsap: scopedGsap, root: scope, duration })
  },
  onReducedMotion: ({ scope }) => {
    dashboardFlip = createDashboardFlip({
      Flip,
      gsap,
      getTargets: () => targetsIn(scope),
      nextTick,
      reducedMotion: true,
      duration: 0,
    })
  },
})

const search = useHomeSearch({ apiGet: settings.apiGet })
const {
  query: searchInput,
  expanded: searchExpanded,
  groups: searchGroups,
  loading: searchLoading,
  error: searchError,
  assistant: searchAssistant,
  open: openSearch,
  close: closeSearch,
  searchNow,
  scheduleSearch,
  retry: retrySearch,
  isSafeNavigation,
} = search
function updateSearchInput(value) { searchInput.value = value; scheduleSearch() }
function navigateSearchResult(navigation) {
  if (!isSafeNavigation(navigation)) return showToast('无法打开不受支持的搜索结果', true)
  closeSearch()
  router.push({ path: navigation.path, query: navigation.query || {} })
}

let queueApi
const knowledgeApi = useKnowledgeDocuments({ apiGet: settings.apiGet, apiPost: settings.apiPost, apiDelete: settings.apiDelete, apiUpload: settings.apiUpload, notify: showToast, confirmAction: (message) => window.confirm(message), onReparseQueued: () => queueApi?.start() })
async function handleAutomationCompleted(task) {
  await knowledgeApi.reload()
  showToast(`${task.title || '自动化任务'}已完成`)
}
queueApi = useAutomationQueue({ apiGet: settings.apiGet, apiPost: settings.apiPost, apiDelete: settings.apiDelete, onCompleted: handleAutomationCompleted, notify: showToast, onApiKeyInvalid: (message) => window.alert(message) })
const { documents, activeDocument, reload: loadDocuments, open: viewDocument, copy: copyDocument, remove: removeDocument } = knowledgeApi

function copyDocContent() {
  return copyDocument({ content: docCopyContent.value || docContent.value })
}

async function copyKnowledgeDocument(id) {
  try {
    const document = await settings.apiGet(`/documents/${id}`)
    if (document?.error) return showToast(document.error, true)
    return copyDocument(document)
  } catch {
    showToast('复制失败', true)
  }
}

const { items: queueTasks, start: startQueuePoll, stop: stopQueuePoll, clear: clearQueue, retry: retryTask, refresh: fetchQueue } = queueApi
const queuePanelOpen = ref(false)
const knowledgePanelOpen = ref(false)
const refreshQueue = () => { fetchQueue(); showToast('已刷新') }
const mapper = createHomeDashboardData()
const queueItems = computed(() => mapper.mapQueue(queueTasks.value))
const knowledgeItems = computed(() => mapper.mapDocuments(documents.value))
const heatmapApi = useHeatmap({ apiGet: settings.apiGet, apiPut: settings.apiPut, fixedRangeDays: 196 })
const homeHeatmapView = ref('heatmap')
const ddlTasks = ref([])
const ddlCategories = ref([])
const ddlLoading = ref(true)
const ddlError = ref('')
const categories = ref([])
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

async function loadDdlCategories() {
  try {
    const data = await settings.apiGet('/ddl/categories')
    ddlCategories.value = Array.isArray(data) ? data : []
  } catch {
    ddlCategories.value = []
  }
}

const automationModules = ref([
  { id: 'douyin-summary', name: '抖音摘要', desc: '提取文本、识别资源并生成文档。', placeholder: '粘贴抖音分享链接...', input: '', includeTutorial: false, loading: false },
  { id: 'bilibili-summary', name: 'B站解析', desc: '解析视频信息并提取语音文本。', placeholder: '粘贴 B 站分享链接...', input: '', loading: false },
  { id: 'xiaohongshu-summary', name: '小红书解析', desc: '提取笔记内容并归档。', placeholder: '粘贴小红书分享链接...', input: '', loading: false },
])
const automationDialog = ref(false)
const selectedAutomationId = ref('')
const selectedAutomation = computed(() => automationModules.value.find((item) => item.id === selectedAutomationId.value))
function openAutomation(id, input = '') {
  selectedAutomationId.value = id || automationModules.value[0].id
  if (typeof input === 'string' && input.trim()) selectedAutomation.value.input = input.trim()
  automationDialog.value = true
}
async function runAutomation(module) {
  if (!module.input.trim()) return showToast('请粘贴分享链接', true)
  module.loading = true
  try {
    const payload = { module_id: module.id, input: module.input.trim() }
    if (module.id === 'douyin-summary' && module.includeTutorial) payload.include_tutorial = true
    const data = await settings.apiPost('/automation/queue', payload)
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
const todayTaskCategories = computed(() => ddlCategories.value.slice(0, 3).map((category) => ({
  ...category,
  tasks: taskItems.value.filter((task) => task.category_id === category.id),
})))
const taskSummary = computed(() => mapper.mapTaskSummary(ddlTasks.value, selectedDate.value))
const heatmapCells = computed(() => heatmapApi.data.value?.cells?.map((cell) => ({ id: cell.date, ...cell })) || [])
const heatmapLoading = computed(() => heatmapApi.loading.value)
const heatmapError = computed(() => heatmapApi.error.value)
const heatmapSettings = computed(() => heatmapApi.settings.value)
const heatmapCaption = computed(() => {
  const payload = heatmapApi.data.value
  const summary = payload?.summary
  return summary ? `近 ${payload?.range?.days || 196} 天：${summary.total} 条记录` : '正在读取统一热力数据'
})

const creationItems = computed(() => mapper.mapLaunchers(settings.launcherItems))
function launchCreation(id) { const item = creationItems.value.find((entry) => entry.id === id); if (item?.url) openExternal(item.url); else router.push('/creator') }
const commandItems = computed(() => {
  const configured = Object.entries(settings.loadFromStorage('commands', {})).map(([id, item]) => ({ id, name: item.name || id, route: item.route || item.url }))
  return mapper.mapCommands(configured.length ? configured : [{ id: 'journal', name: '更新日志', route: '/journal' }, { id: 'wiki', name: '编译Wiki', route: '/wiki' }])
})
function runCommand(id) {
  const command = commandItems.value.find((item) => item.id === id)
  if (!command?.route) return
  if (command.route.startsWith('/')) router.push(command.route)
  else if (/^https?:\/\//i.test(command.route)) openExternal(command.route)
}
const workflowSteps = [{ id: 'collect', label: '网页输入', status: 'running' }, { id: 'execute', label: '执行', status: 'pending' }, { id: 'output', label: '输出', status: 'pending' }]
const workflowUrl = ref('')
function runWorkflow(id, url = workflowUrl.value) {
  const path = id === 'output' ? '/creator' : '/workflow'
  const value = typeof url === 'string' ? url.trim() : ''
  router.push(value ? { path, query: { url: value } } : path)
}

const reviewOpen = ref(false)
const review = useDailyReview({ apiPost: settings.apiPost, apiGet: settings.apiGet, notify: showToast })
const { input: reviewInput, loading: reviewLoading, status: reviewStatus, result: reviewResult, polish: polishReview, weeklyReport, loadHistory: loadReviewHistory } = review
const docModal = computed({ get: () => Boolean(activeDocument.value), set: (value) => { if (!value) activeDocument.value = null } })
const docTitle = computed(() => activeDocument.value?.title || '')
const docContent = computed(() => activeDocument.value?.content || '')
const docTutorialContent = computed(() => activeDocument.value?.tutorial_markdown || '')
const docTutorialStatus = computed(() => activeDocument.value?.tutorial_status || 'not_requested')
const docTutorialReason = computed(() => activeDocument.value?.tutorial_reason || '')
const docCopyContent = ref('')

const reviewPanel = ref(null)
const documentPanel = ref(null)
const automationPanel = ref(null)
const queuePanel = ref(null)
const knowledgePanel = ref(null)
const lastFocusedElement = ref(null)
const activeSurface = computed(() => {
  if (reviewOpen.value) return 'review'
  if (docModal.value) return 'document'
  if (automationDialog.value) return 'automation'
  if (knowledgePanelOpen.value) return 'knowledge'
  if (queuePanelOpen.value) return 'queue'
  return ''
})
const surfacePanels = { review: reviewPanel, document: documentPanel, automation: automationPanel, queue: queuePanel, knowledge: knowledgePanel }

function rememberFocus() {
  const element = document.activeElement
  if (element instanceof HTMLElement && element !== document.body) lastFocusedElement.value = element
}

function focusableElements(panel) {
  return panel ? [...panel.querySelectorAll('button, input, textarea, select, a[href], [tabindex]:not([tabindex="-1"])')].filter((element) => !element.disabled) : []
}

function focusSurface(name) {
  const panel = surfacePanels[name]?.value || document.querySelector(name === 'queue' || name === 'knowledge' ? '.home-drawer' : '.home-modal__panel')
  const elements = focusableElements(panel)
  ;(elements[0] || panel)?.focus?.()
}

function restoreFocus() {
  const element = lastFocusedElement.value
  lastFocusedElement.value = null
  if (element?.isConnected) nextTick(() => element.focus())
}
function restoreFocusAfterLeave() {
  if (!activeSurface.value) restoreFocus()
}

function closeReview() { reviewOpen.value = false }
function closeDocument() { docModal.value = false }
function closeAutomation() { automationDialog.value = false }
function closeQueue() { queuePanelOpen.value = false }
function closeKnowledge() { knowledgePanelOpen.value = false }
async function openKnowledgeDocument(id) {
  closeKnowledge()
  return viewDocument(id)
}

function handleGlobalKeydown(event) {
  const name = activeSurface.value
  if (!name) return
  if (event.key === 'Escape') {
    event.preventDefault()
    ;({ review: closeReview, document: closeDocument, automation: closeAutomation, queue: closeQueue, knowledge: closeKnowledge }[name])()
    return
  }
  if (event.key !== 'Tab') return
  const panel = surfacePanels[name]?.value || document.querySelector(name === 'queue' || name === 'knowledge' ? '.home-drawer' : '.home-modal__panel')
  const elements = focusableElements(panel)
  if (!elements.length) return
  const first = elements[0]
  const last = elements[elements.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(activeSurface, async (name) => {
  if (name) {
    await nextTick()
    focusSurface(name)
  }
})

function propsFor(id) {
  const props = {
    'work-heatmap': { cells: heatmapCells.value, caption: heatmapCaption.value, loading: heatmapLoading.value, error: heatmapError.value, viewMode: homeHeatmapView.value, settings: heatmapSettings.value },
    'calendar-agenda': { days: calendarDays.value, agenda: agendaItems.value, monthLabel: calendarMonth, loading: ddlLoading.value, error: ddlError.value },
    'today-focus': { tasks: taskItems.value, categories: todayTaskCategories.value, dateLabel: `${String(today.getMonth() + 1).padStart(2, '0')}月${String(today.getDate()).padStart(2, '0')}日`, loading: ddlLoading.value, error: ddlError.value },
    'automation-queue': { items: queueItems.value }, knowledge: { items: knowledgeItems.value },
    'daily-memory': { title: '今日手账' }, 'quick-command': { commands: commandItems.value },
    'creation-entry': { items: creationItems.value }, 'quick-workflow': { steps: workflowSteps },
  }
  if (id === 'today-focus') props['today-focus'] = { ...props['today-focus'], totalTaskCount: taskSummary.value.total, completedTaskCount: taskSummary.value.completed }
  if (id === 'quick-workflow') props['quick-workflow'] = { ...props['quick-workflow'], modelValue: workflowUrl.value }
  return props[id] || {}
}
function listenersFor(id) {
  const listeners = {
    'work-heatmap': { 'update:viewMode': (value) => { homeHeatmapView.value = value } },
    'calendar-agenda': { select: (date) => { selectedDate.value = date }, open: () => router.push('/ddl') },
    'today-focus': { select: () => router.push('/ddl'), create: (categoryId) => router.push({ path: '/ddl', query: { create: '1', categoryId: String(categoryId), planDate: selectedDate.value } }) },
    'automation-queue': { open: () => { queuePanelOpen.value = true }, retry: retryTask, create: () => openAutomation() },
    knowledge: { open: viewDocument, 'open-all': () => { rememberFocus(); knowledgePanelOpen.value = true }, copy: copyKnowledgeDocument, remove: removeDocument }, 'daily-memory': { open: () => { reviewOpen.value = true } },
    'quick-command': { run: runCommand }, 'creation-entry': { open: launchCreation }, 'quick-workflow': { run: runWorkflow },
  }[id] || {}
  if (id === 'calendar-agenda') listeners.today = () => { selectedDate.value = toLocalDateKey(new Date()) }
  if (id === 'automation-queue') {
    listeners.open = () => { rememberFocus(); queuePanelOpen.value = true }
    listeners.create = (url) => { rememberFocus(); openAutomation(undefined, url) }
    listeners.submit = (url) => { rememberFocus(); openAutomation(undefined, url) }
  }
  if (id === 'knowledge') {
    listeners.open = (documentId) => { rememberFocus(); return viewDocument(documentId) }
  }
  if (id === 'daily-memory') listeners.open = () => { rememberFocus(); reviewOpen.value = true }
  if (id === 'quick-workflow') listeners['update:modelValue'] = (value) => { workflowUrl.value = value }
  return listeners
}

onMounted(async () => {
  await Promise.all([loadDocuments(), loadReviewHistory(), loadDdlTasks(), loadDdlCategories(), heatmapApi.load()])
  try { categories.value = await settings.apiGet('/categories') } catch { categories.value = [] }
  startQueuePoll()
})
onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('pointermove', continueGridDrag)
  window.addEventListener('pointerup', finishGridDrag)
  window.addEventListener('pointercancel', cancelGridDrag)
})
onUnmounted(() => {
  stopQueuePoll(); clearTimeout(toastTimer)
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('pointermove', continueGridDrag)
  window.removeEventListener('pointerup', finishGridDrag)
  window.removeEventListener('pointercancel', cancelGridDrag)
})
</script>

<style scoped>
.home-navigation { position: relative; }
.home-navigation :deep(.workstation-search-panel) { top: 105px; right: max(24px, calc((100vw - 1320px) / 2)); }
.home-dashboard-grid {
  width: calc(100% + 12px);
  min-height: 656px;
  margin-top: 20px;
  margin-left: -6px;
}
.home-dashboard-grid :deep(.bento-dashboard-grid) { grid-auto-flow: row; }
.home-dashboard-grid__item { position: relative; min-width: 0; min-height: 0; align-self: stretch; }
.home-dashboard-grid__drag-handle { position: absolute; z-index: 3; top: 8px; right: 8px; display: grid; width: 28px; height: 28px; place-items: center; border: 1px solid rgb(245 246 238 / 22%); border-radius: 8px; background: rgb(16 20 15 / 82%); color: #d7ff63; cursor: grab; touch-action: none; }
.home-dashboard-grid__drag-handle:active { cursor: grabbing; }
@media (max-width: 767px) {
  .home-dashboard-grid { width: 100%; min-height: 0; margin-left: 0; }
  .home-dashboard-grid__item { grid-column: 1 !important; grid-row: auto !important; }
  .home-footer { position: relative; right: auto; bottom: auto; left: auto; height: auto; margin-top: 20px; padding-bottom: 0; }
}
.home-footer { position: absolute; right: 46px; bottom: 0; left: 46px; display: flex; width: auto; height: 55px; box-sizing: border-box; align-items: center; justify-content: space-between; margin: 0; padding-bottom: 20px; color: #8b9186; font-size: 12px; pointer-events: none; }
.home-footer a { pointer-events: auto; }
.home-footer a { display: inline-flex; height: 34px; align-items: center; border-radius: 18px; padding: 0 17px; background: #d7ff63; color: #11140f; font-weight: 800; text-decoration: none; }
.home-modal { position: fixed; z-index: 100; inset: 0; display: grid; place-items: center; padding: 24px; background: rgb(0 0 0 / 68%); }
.home-modal__panel { display: grid; width: min(680px, 100%); max-height: 86vh; box-sizing: border-box; gap: 16px; overflow: auto; border: 1px solid rgb(245 246 238 / 20%); border-radius: 18px; padding: 20px; background: #1b1d1a; box-shadow: var(--ui-shadow-overlay); }
.home-document-modal__panel { width: min(1200px, 100%); max-height: 90vh; grid-template-rows: auto minmax(0, 1fr) auto; overflow: hidden; }
.home-document-modal__reader { min-height: 0; overflow-y: auto; padding: 20px; border-radius: 8px; background: var(--ui-color-bg, #10140f); }
.home-modal__panel header, .home-modal__panel footer, .home-drawer header, .home-drawer footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.home-tutorial-option { display: inline-flex; align-items: center; gap: 8px; color: #d9ddcf; font-size: 13px; }
.home-modal__panel h2, .home-drawer h2 { margin: 0; color: #f5f6ee; font-size: 18px; }
.home-modal__panel textarea { min-height: 140px; resize: vertical; border: 1px solid rgb(245 246 238 / 20%); border-radius: 10px; padding: 12px; background: #10140f; color: #f5f6ee; font: 14px/1.5 var(--ui-font-sans); }
.home-actions { display: flex; align-items: center; gap: 8px; }.home-actions span,.home-muted{color:#8b9186;font-size:12px}.home-error{color:#ff6b78}
.home-drawer-backdrop { position: fixed; z-index: 95; inset: 0; }
.home-drawer { position: absolute; top: 0; right: 0; bottom: 0; display: grid; width: min(420px, 94vw); box-sizing: border-box; grid-template-rows: auto 1fr auto; gap: 16px; border-left: 1px solid rgb(245 246 238 / 20%); padding: 20px; background: #1b1d1a; box-shadow: var(--ui-shadow-overlay); }
.home-drawer__list { display: grid; align-content: start; gap: 8px; overflow: auto; }.home-drawer__list>div{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgb(245 246 238 / 12%);padding:12px 0;color:#d9ddcf;font-size:12px}
.knowledge-drawer__item { gap: 12px; }
.knowledge-drawer__title { min-width: 0; flex: 1; overflow: hidden; border: 0; padding: 0; background: transparent; color: inherit; font: inherit; text-align: left; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.knowledge-drawer__actions { display: inline-flex; flex: 0 0 auto; gap: 6px; }
.knowledge-drawer__empty { color: #8b9186; }
.home-toast { position: fixed; z-index: 120; right: 24px; bottom: 24px; border: 1px solid rgb(245 246 238 / 20%); border-radius: 10px; padding: 12px 16px; background: #252824; color: #f5f6ee; box-shadow: var(--ui-shadow-overlay); font-size: 12px; }.home-toast[data-error='true']{color:#ff6b78}
.home-surface-enter-active, .home-surface-leave-active, .home-drawer-enter-active, .home-drawer-leave-active, .home-editor-enter-active, .home-editor-leave-active, .home-toast-enter-active, .home-toast-leave-active { transition: opacity var(--ui-duration-normal) var(--ui-ease-standard), transform var(--ui-duration-normal) var(--ui-ease-standard); }
.home-surface-enter-from, .home-surface-leave-to { opacity: 0; }
.home-surface-enter-from .home-modal__panel, .home-surface-leave-to .home-modal__panel { transform: translateY(8px); }
.home-modal__panel { transition: transform var(--ui-duration-normal) var(--ui-ease-standard); }
.home-drawer-enter-from, .home-drawer-leave-to { opacity: 0; }
.home-drawer-enter-from .home-drawer, .home-drawer-leave-to .home-drawer { transform: translateX(24px); }
.home-drawer { transition: transform var(--ui-duration-normal) var(--ui-ease-standard); }
.home-editor-enter-from, .home-editor-leave-to { opacity: 0; transform: translateX(24px); }
.home-toast-enter-from, .home-toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
