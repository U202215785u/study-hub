<template>
  <section class="overview-panel" aria-labelledby="overview-panel-title">
    <header class="panel-header">
      <div class="panel-heading">
        <p class="eyebrow">只读摘要</p>
        <h2 id="overview-panel-title">工作台总览</h2>
        <p class="panel-description">集中查看工单、审批、版本、环境和近期规划的当前摘要。</p>
      </div>
      <div class="panel-actions">
        <span v-if="displayOverview && isRefreshing" class="refresh-status" role="status" aria-live="polite">
          正在刷新
        </span>
        <button
          type="button"
          class="refresh-button"
          :disabled="isLoading || isRefreshing"
          @click="requestRefresh"
        >
          {{ isRefreshing ? '刷新中' : '刷新' }}
        </button>
      </div>
    </header>

    <div v-if="isLoading && !displayOverview" class="state-panel" role="status" aria-live="polite" aria-busy="true">
      <span class="spinner" aria-hidden="true"></span>
      <strong>正在加载总览</strong>
      <span>正在读取工作台摘要。</span>
    </div>

    <div v-else-if="!displayOverview && displayError" class="state-panel state-error" role="alert">
      <strong>总览加载失败</strong>
      <span>{{ displayError }}</span>
      <button type="button" class="retry-button" :disabled="isRefreshing" @click="requestRefresh">
        重试
      </button>
    </div>

    <div v-else-if="!displayOverview" class="state-panel" role="status">
      <strong>暂无总览数据</strong>
      <span>当前没有可展示的工作台摘要。</span>
    </div>

    <template v-else-if="displayOverview">
      <div v-if="displayError" class="error-banner" role="alert">
        <span class="error-copy">{{ displayError }}</span>
        <button type="button" class="retry-button" :disabled="isRefreshing" @click="requestRefresh">
          重试
        </button>
      </div>

      <div class="summary-grid" :aria-busy="isRefreshing">
        <button
          v-for="card in summaryCards"
          :key="card.key"
          type="button"
          class="summary-card"
          :disabled="!card.hasValue"
          :aria-label="card.hasValue ? `查看${card.label}` : `${card.label}暂无数据`"
          @click="navigate(card.module, card.entity, card.id)"
        >
          <span class="card-label">{{ card.label }}</span>
          <strong class="card-value">{{ card.value }}</strong>
          <span class="card-detail">{{ card.detail }}</span>
        </button>
      </div>

      <div v-if="isEmptyOverview" class="empty-panel" role="status">
        <strong>暂无总览数据</strong>
        <span>工单、审批、版本和规划都还没有可展示的摘要。</span>
      </div>

      <div v-else class="overview-grid">
        <section class="overview-section version-section" aria-labelledby="version-summary-title">
          <div class="section-heading">
            <div>
              <p class="eyebrow">版本摘要</p>
              <h3 id="version-summary-title">当前版本与测试版本</h3>
            </div>
            <button type="button" class="text-action" @click="navigate('versions', 'version')">查看版本</button>
          </div>
          <div class="version-grid">
            <button
              type="button"
              class="version-item"
              :disabled="!currentVersion"
              @click="navigate('versions', 'version', currentVersion?.id)"
            >
              <span class="item-label">当前版本</span>
              <strong>{{ currentVersion?.version || '暂无' }}</strong>
              <span>{{ currentVersion ? versionStatus(currentVersion) : '暂无已确认版本' }}</span>
            </button>
            <button
              type="button"
              class="version-item"
              :disabled="!testVersion"
              @click="navigate('versions', 'test-version', testVersion?.id)"
            >
              <span class="item-label">最新测试版本</span>
              <strong>{{ testVersion?.version || '暂无' }}</strong>
              <span>{{ testVersion ? versionStatus(testVersion) : '暂无测试版本' }}</span>
            </button>
          </div>
        </section>

        <section class="overview-section environment-section" aria-labelledby="environment-summary-title">
          <div class="section-heading">
            <div>
              <p class="eyebrow">运行摘要</p>
              <h3 id="environment-summary-title">环境状态</h3>
            </div>
            <button type="button" class="text-action" @click="navigate('environment', 'environment')">查看环境</button>
          </div>
          <div class="environment-summary">
            <span class="status-dot" :class="statusTone(environmentStatus)" aria-hidden="true"></span>
            <div class="environment-copy">
              <strong>{{ statusLabel(environmentStatus) }}</strong>
              <span>{{ environmentDetail }}</span>
            </div>
          </div>
          <dl class="health-list">
            <div>
              <dt>整体健康</dt>
              <dd :class="statusTone(healthStatus)">{{ statusLabel(healthStatus) }}</dd>
            </div>
            <div>
              <dt>运行版本</dt>
              <dd>{{ environment?.runtime?.python_version || '暂无' }}</dd>
            </div>
          </dl>
        </section>

        <section class="overview-section cases-section" aria-labelledby="recent-cases-title">
          <div class="section-heading">
            <div>
              <p class="eyebrow">工单摘要</p>
              <h3 id="recent-cases-title">近期工单</h3>
            </div>
            <button type="button" class="text-action" @click="navigate('tasks', 'case')">查看工单</button>
          </div>
          <div v-if="recentCases.length" class="case-list">
            <button
              v-for="item in recentCases"
              :key="item.id"
              type="button"
              class="case-item"
              @click="navigate('tasks', 'case', item.id)"
            >
              <span class="case-main">
                <strong>{{ item.title || '未命名工单' }}</strong>
                <span>{{ item.status_label || item.status || '未知状态' }}</span>
              </span>
              <span class="case-date">{{ formatDate(item.updated_at) }}</span>
            </button>
          </div>
          <p v-else class="section-empty">暂无近期工单。</p>
        </section>

        <section class="overview-section roadmap-section" aria-labelledby="roadmap-summary-title">
          <div class="section-heading">
            <div>
              <p class="eyebrow">规划摘要</p>
              <h3 id="roadmap-summary-title">近期规划</h3>
            </div>
            <button type="button" class="text-action" @click="navigate('roadmap', 'roadmap')">查看规划</button>
          </div>
          <div class="roadmap-summary">
            <span class="roadmap-status" :class="statusTone(roadmapStatus)">{{ roadmapStatusLabel }}</span>
            <p>{{ roadmapText }}</p>
          </div>
          <dl class="roadmap-meta">
            <div>
              <dt>来源</dt>
              <dd>{{ roadmapSource }}</dd>
            </div>
            <div>
              <dt>更新时间</dt>
              <dd>{{ formatDate(roadmap?.updated_at) }}</dd>
            </div>
          </dl>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getOverview } from '../../services/workbenchOverview.js'

const props = defineProps({
  overview: { type: Object, default: undefined },
  loading: { type: Boolean, default: undefined },
  refreshing: { type: Boolean, default: undefined },
  error: { type: [String, Error, Object], default: undefined },
  refreshToken: { type: [String, Number], default: 0 },
  autoLoad: { type: Boolean, default: true },
  apiBase: { type: String, default: undefined },
})

const emit = defineEmits(['refresh', 'navigate'])
const localOverview = ref(null)
const localLoading = ref(false)
const localRefreshing = ref(false)
const localError = ref(null)

const displayOverview = computed(() => props.overview !== undefined ? props.overview : localOverview.value)
const isLoading = computed(() => props.loading !== undefined ? props.loading : localLoading.value)
const isRefreshing = computed(() => props.refreshing !== undefined ? props.refreshing : localRefreshing.value)
const displayError = computed(() => props.error !== undefined ? errorMessage(props.error) : errorMessage(localError.value))
const currentVersion = computed(() => displayOverview.value?.current_version || null)
const testVersion = computed(() => displayOverview.value?.latest_test_version || null)
const environment = computed(() => displayOverview.value?.environment || null)
const roadmap = computed(() => displayOverview.value?.roadmap_summary || displayOverview.value?.roadmap || null)
const recentCases = computed(() => Array.isArray(displayOverview.value?.recent_cases) ? displayOverview.value.recent_cases : [])
const pendingCases = computed(() => Array.isArray(displayOverview.value?.pending_cases) ? displayOverview.value.pending_cases : [])
const verificationCases = computed(() => Array.isArray(displayOverview.value?.verification_cases) ? displayOverview.value.verification_cases : [])
const pendingApprovals = computed(() => Number(displayOverview.value?.pending_approvals || 0))
const environmentStatus = computed(() => environment.value?.status || displayOverview.value?.health?.status || 'unknown')
const healthStatus = computed(() => displayOverview.value?.health?.status || environment.value?.health?.status || 'unknown')
const roadmapStatus = computed(() => roadmap.value?.status || 'missing')
const roadmapStatusLabel = computed(() => ({ available: '可用', missing: '暂无规划', error: '读取异常' }[roadmapStatus.value] || '未知'))
const roadmapSource = computed(() => roadmap.value?.source || roadmap.value?.relative_path || '暂无')
const roadmapText = computed(() => {
  const content = typeof roadmap.value?.content === 'string' ? roadmap.value.content : ''
  const text = content
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/[#>*_`~-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  if (text) return text.length > 220 ? `${text.slice(0, 220)}...` : text
  if (roadmapStatus.value === 'missing') return '暂无可展示的近期规划。'
  if (roadmapStatus.value === 'error') return '规划内容暂时无法读取，请稍后重试。'
  return '规划已提供，但暂无可展示的摘要。'
})

const summaryCards = computed(() => [
  {
    key: 'cases',
    label: '进行中的工单',
    value: pendingCases.value.length,
    detail: verificationCases.value.length ? `${verificationCases.value.length} 项待验证` : '暂无待验证工单',
    module: 'tasks',
    entity: 'case',
    hasValue: pendingCases.value.length > 0 || verificationCases.value.length > 0,
  },
  {
    key: 'approvals',
    label: '待处理审批',
    value: pendingApprovals.value,
    detail: pendingApprovals.value ? '需要确认的事项' : '暂无待处理审批',
    module: 'approvals',
    entity: 'approval',
    hasValue: pendingApprovals.value > 0,
  },
  {
    key: 'test-version',
    label: '最新测试版本',
    value: testVersion.value?.version || '暂无',
    detail: testVersion.value ? versionStatus(testVersion.value) : '暂无测试版本',
    module: 'versions',
    entity: 'test-version',
    id: testVersion.value?.id,
    hasValue: Boolean(testVersion.value),
  },
  {
    key: 'environment',
    label: '环境状态',
    value: statusLabel(environmentStatus.value),
    detail: environmentDetail.value,
    module: 'environment',
    entity: 'environment',
    hasValue: environmentStatus.value !== 'unknown',
  },
])

const environmentDetail = computed(() => {
  const checks = environment.value?.health?.checks || displayOverview.value?.health?.checks || {}
  const checkCount = Object.keys(checks).length
  return checkCount ? `${checkCount} 项健康检查` : '暂无健康检查摘要'
})

const isEmptyOverview = computed(() => {
  if (!displayOverview.value) return false
  const hasCases = recentCases.value.length || pendingCases.value.length || verificationCases.value.length
  const hasVersion = Boolean(currentVersion.value || testVersion.value)
  const hasEnvironment = environmentStatus.value !== 'unknown' || healthStatus.value !== 'unknown'
  const hasRoadmap = roadmapStatus.value !== 'missing' || Boolean(roadmap.value?.content)
  return !hasCases && !pendingApprovals.value && !hasVersion && !hasEnvironment && !hasRoadmap
})

function errorMessage(value) {
  if (!value) return ''
  if (typeof value === 'string') return value
  return value.message || '总览加载失败，请重试。'
}

function statusLabel(status) {
  return ({
    ok: '正常',
    healthy: '健康',
    degraded: '降级',
    error: '异常',
    unknown: '未知',
    available: '可用',
    missing: '暂无',
    running: '测试中',
    passed: '测试通过',
    failed: '测试失败',
    queued: '排队中',
    expired: '已过期',
  }[status] || status || '未知')
}

function statusTone(status) {
  return `tone-${['ok', 'healthy', 'available', 'passed'].includes(status) ? 'positive' : ['degraded', 'queued', 'missing', 'running'].includes(status) ? 'warning' : ['error', 'failed', 'expired'].includes(status) ? 'negative' : 'neutral'}`
}

function versionStatus(version) {
  return version.status_label || statusLabel(version.status) || version.channel || '状态未知'
}

function formatDate(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function navigate(module, entity, id = null) {
  emit('navigate', { module, entity, id: id || null, source: 'overview' })
}

async function loadOverview() {
  localError.value = null
  const hasExistingData = Boolean(localOverview.value)
  localLoading.value = !hasExistingData
  localRefreshing.value = hasExistingData
  try {
    localOverview.value = await getOverview({ apiBase: props.apiBase })
  } catch (cause) {
    localError.value = cause instanceof Error ? cause : new Error('总览加载失败，请重试。')
  } finally {
    localLoading.value = false
    localRefreshing.value = false
  }
}

function requestRefresh() {
  if (isLoading.value || isRefreshing.value) return
  emit('refresh')
  if (props.overview === undefined && props.loading === undefined && props.refreshing === undefined && props.error === undefined) {
    loadOverview()
  }
}

onMounted(() => {
  if (props.autoLoad && props.overview === undefined && props.loading === undefined && props.refreshing === undefined && props.error === undefined) {
    loadOverview()
  }
})

watch(() => props.refreshToken, (next, previous) => {
  if (next === previous || !props.autoLoad || props.overview !== undefined) return
  if (props.loading === undefined && props.refreshing === undefined && props.error === undefined) loadOverview()
})
</script>

<style scoped>
.overview-panel { min-width: 0; color: #e0e0e8; }
.panel-header, .section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.panel-header { padding-bottom: 18px; border-bottom: 1px solid #2a2a3a; }
.panel-heading, .section-heading > div, .environment-copy, .case-main { min-width: 0; }
.eyebrow { margin: 0 0 5px; color: #8888a0; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; }
h2, h3, p { margin-top: 0; }
h2 { margin-bottom: 6px; font-size: 22px; line-height: 1.25; }
h3 { margin-bottom: 0; font-size: 16px; line-height: 1.4; }
.panel-description { max-width: 40rem; margin-bottom: 0; color: #8888a0; font-size: 13px; line-height: 1.6; }
.panel-actions { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 10px; }
.refresh-status { color: #a0a0b0; font-size: 12px; }
.refresh-button, .retry-button, .text-action { cursor: pointer; border: 1px solid #4b5563; border-radius: 6px; background: #1a1a24; color: #e0e0e8; }
.refresh-button, .retry-button { min-height: 36px; padding: 7px 12px; font-size: 13px; }
.text-action { flex: 0 0 auto; border-color: transparent; background: transparent; color: #a5b0ff; font-size: 12px; }
.refresh-button:hover, .refresh-button:focus-visible, .retry-button:hover, .retry-button:focus-visible, .text-action:hover, .text-action:focus-visible { border-color: #7c8aff; color: #fff; }
.refresh-button:disabled, .retry-button:disabled, .summary-card:disabled, .version-item:disabled { cursor: not-allowed; opacity: .55; }
.state-panel, .empty-panel { display: grid; justify-items: center; gap: 9px; padding: 52px 16px; color: #a0a0b0; text-align: center; }
.state-panel strong, .empty-panel strong { color: #e0e0e8; }
.state-panel span, .empty-panel span { max-width: 34rem; overflow-wrap: anywhere; font-size: 13px; }
.state-error { color: #fb7185; }
.state-error span { color: #a0a0b0; }
.spinner { width: 22px; height: 22px; border: 2px solid #3b3b50; border-top-color: #7c8aff; border-radius: 50%; animation: spin .8s linear infinite; }
.error-banner { display: flex; min-width: 0; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-top: 18px; padding: 12px 14px; border-left: 3px solid #fb7185; background: rgba(251, 113, 133, .08); color: #fda4af; }
.error-copy { min-width: 0; overflow-wrap: anywhere; font-size: 13px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 20px; }
.summary-card, .version-item, .case-item { min-width: 0; border: 1px solid #2a2a3a; background: #1a1a24; color: inherit; text-align: left; }
.summary-card { display: grid; min-height: 128px; align-content: start; gap: 8px; padding: 16px; border-radius: 8px; cursor: pointer; transition: border-color .15s ease, background .15s ease; }
.summary-card:hover:not(:disabled), .summary-card:focus-visible:not(:disabled), .version-item:hover:not(:disabled), .version-item:focus-visible:not(:disabled), .case-item:hover, .case-item:focus-visible { border-color: #7c8aff; background: #20202d; outline: none; }
.card-label, .item-label, dt { color: #8888a0; font-size: 12px; }
.card-value { min-width: 0; overflow-wrap: anywhere; color: #f0f0f8; font-size: 25px; line-height: 1.2; }
.card-detail, .version-item span:last-child, .case-main span, .case-date, .section-empty, .roadmap-summary p, dd { color: #a0a0b0; font-size: 12px; line-height: 1.5; }
.overview-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 14px; }
.overview-section { min-width: 0; padding: 16px; border: 1px solid #2a2a3a; border-radius: 8px; background: #1a1a24; }
.section-heading { padding-bottom: 13px; border-bottom: 1px solid #2a2a3a; }
.version-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.version-item { display: grid; min-height: 100px; align-content: start; gap: 7px; padding: 13px; border-radius: 6px; cursor: pointer; }
.version-item strong { min-width: 0; overflow-wrap: anywhere; color: #f0f0f8; font-size: 18px; }
.environment-summary { display: flex; min-width: 0; align-items: flex-start; gap: 11px; margin-top: 15px; }
.status-dot { flex: 0 0 auto; width: 10px; height: 10px; margin-top: 5px; border-radius: 50%; background: #a0a0b0; }
.environment-copy { display: grid; gap: 4px; }
.environment-copy strong { color: #f0f0f8; font-size: 17px; }
.environment-copy span { color: #a0a0b0; font-size: 12px; }
.health-list, .roadmap-meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 18px 0 0; }
.health-list > div, .roadmap-meta > div { min-width: 0; display: grid; gap: 4px; }
dd { margin: 0; overflow-wrap: anywhere; }
.tone-positive { color: #34d399 !important; }
.tone-warning { color: #fbbf24 !important; }
.tone-negative { color: #fb7185 !important; }
.tone-neutral { color: #a0a0b0 !important; }
.status-dot.tone-positive { background: #34d399; }
.status-dot.tone-warning { background: #fbbf24; }
.status-dot.tone-negative { background: #fb7185; }
.case-list { display: grid; gap: 8px; margin-top: 14px; }
.case-item { display: flex; min-width: 0; align-items: flex-start; justify-content: space-between; gap: 12px; padding: 12px; border-radius: 6px; cursor: pointer; }
.case-main { display: grid; gap: 4px; }
.case-main strong { min-width: 0; overflow-wrap: anywhere; color: #f0f0f8; font-size: 13px; }
.case-date { flex: 0 0 auto; white-space: nowrap; }
.section-empty { margin: 16px 0 0; }
.roadmap-summary { min-width: 0; margin-top: 15px; }
.roadmap-status { display: inline-flex; margin-bottom: 8px; padding: 4px 8px; border: 1px solid currentColor; border-radius: 999px; font-size: 11px; }
.roadmap-summary p { margin: 0; overflow-wrap: anywhere; }
.roadmap-meta { margin-top: 15px; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) { .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 680px) {
  .panel-header, .section-heading { display: grid; }
  .panel-actions { justify-content: flex-start; }
  .summary-grid, .overview-grid, .version-grid, .health-list, .roadmap-meta { grid-template-columns: minmax(0, 1fr); }
  .summary-card { min-height: 112px; }
  .case-item { display: grid; gap: 6px; }
  .case-date { white-space: normal; }
}
</style>
