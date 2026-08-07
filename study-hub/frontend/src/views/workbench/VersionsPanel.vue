<template>
  <section class="min-w-0" aria-labelledby="versions-panel-title">
    <header class="flex min-w-0 flex-wrap items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-xs font-medium text-accent">版本管理</p>
        <h2 id="versions-panel-title" class="mt-1 text-xl font-semibold text-text">版本历史</h2>
        <p class="mt-1 max-w-2xl text-sm leading-6 text-text-secondary">
          查看正式版本、测试版本、构建状态、测试结果与关联工单。
        </p>
      </div>
      <button
        type="button"
        class="shrink-0 rounded-[8px] border border-border px-3 py-2 text-sm text-text-secondary transition-colors hover:border-accent hover:text-text disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="loading || refreshing"
        @click="loadVersions()"
      >
        {{ loading || refreshing ? '刷新中...' : '刷新' }}
      </button>
    </header>

    <div v-if="error" class="mt-5 flex min-w-0 flex-wrap items-center justify-between gap-3 rounded-[8px] border border-danger/40 bg-danger/10 px-4 py-3" role="alert">
      <span class="min-w-0 break-words text-sm text-text">{{ error }}</span>
      <button
        type="button"
        class="shrink-0 rounded-[6px] border border-danger/50 px-3 py-1.5 text-xs text-text transition-colors hover:bg-danger/10 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="loading || refreshing"
        @click="loadVersions()"
      >
        重试
      </button>
    </div>

    <p v-if="notice" class="mt-5 rounded-[8px] border border-success/40 bg-success/10 px-4 py-3 text-sm text-text" role="status">
      {{ notice }}
    </p>

    <div v-if="loading && !hasLoaded" class="mt-6 space-y-6" aria-busy="true" aria-label="正在加载版本">
      <div v-for="section in 2" :key="section" class="space-y-3">
        <div class="h-5 w-32 animate-pulse rounded bg-surface-hover" />
        <div v-for="item in 2" :key="item" class="h-44 animate-pulse rounded-[8px] border border-border bg-surface/60" />
      </div>
    </div>

    <div v-else class="mt-6 min-w-0 space-y-8" :aria-busy="refreshing">
      <VersionSection
        title="正式版本"
        description="已记录的正式版本历史"
        empty-label="暂无正式版本记录"
        :versions="formalVersions"
        :loading="refreshing"
        @open="openDetail"
        @submit="openSubmitConfirmation"
      />

      <VersionSection
        title="测试版本"
        description="候选版本的测试记录与结果"
        empty-label="暂无测试版本记录"
        :versions="testVersions"
        :loading="refreshing"
        :is-test="true"
        @open="openDetail"
        @submit="openSubmitConfirmation"
      />
    </div>

    <Teleport to="body">
      <div v-if="selectedVersion" class="fixed inset-0 z-40 flex min-h-full items-center justify-center overflow-y-auto bg-black/50 p-4" role="presentation" @click.self="closeDetail">
        <article
          class="my-auto max-h-[calc(100vh-2rem)] w-full max-w-3xl min-w-0 overflow-y-auto rounded-[8px] border border-border bg-surface p-4 shadow-xl sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="version-detail-title"
          @keydown.esc="closeDetail"
        >
          <header class="flex min-w-0 items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs font-medium text-accent">版本详情</p>
              <h3 id="version-detail-title" class="mt-1 break-words text-lg font-semibold text-text">
                {{ selectedVersion.version || '未命名版本' }}
              </h3>
            </div>
            <button type="button" class="shrink-0 rounded-[6px] px-2 py-1 text-sm text-text-secondary hover:bg-bg hover:text-text" aria-label="关闭版本详情" @click="closeDetail">
              关闭
            </button>
          </header>

          <div v-if="detailLoading" class="mt-5 rounded-[8px] border border-dashed border-border px-4 py-8 text-center text-sm text-text-secondary" role="status">
            正在加载版本详情...
          </div>
          <div v-else class="mt-5 min-w-0">
            <div v-if="detailError" class="mb-4 rounded-[8px] border border-danger/40 bg-danger/10 px-3 py-3 text-sm text-text" role="alert">
              {{ detailError }}
            </div>

            <div class="flex min-w-0 flex-wrap items-center gap-2">
              <span class="rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 text-xs font-medium text-accent">
                {{ versionTypeLabel(selectedVersion.version_type) }}
              </span>
              <span class="rounded-full border px-2.5 py-1 text-xs font-medium" :class="statusTone(selectedVersion.status)">
                {{ statusLabel(selectedVersion.status) }}
              </span>
              <span v-if="selectedVersion.is_current" class="rounded-full border border-success/30 bg-success/10 px-2.5 py-1 text-xs font-medium text-success">
                当前版本
              </span>
            </div>

            <p v-if="selectedVersion.title" class="mt-4 break-words text-sm font-medium text-text">{{ selectedVersion.title }}</p>
            <p v-if="versionDescription(selectedVersion)" class="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-text-secondary">
              {{ versionDescription(selectedVersion) }}
            </p>

            <dl class="mt-5 grid min-w-0 gap-x-5 gap-y-4 sm:grid-cols-2">
              <Field label="版本 ID" :value="selectedVersion.id" />
              <Field label="工作台" :value="selectedVersion.workbench_id" />
              <Field label="构建状态" :value="buildStatus(selectedVersion)" />
              <Field label="测试结果" :value="testStatus(selectedVersion)" />
              <Field label="目标环境" :value="targetEnvironment(selectedVersion)" />
              <Field label="提交标识" :value="selectedVersion.commit_sha || selectedVersion.commit" />
              <Field label="内容哈希" :value="selectedVersion.content_hash" />
              <Field label="正式基线 ID" :value="selectedVersion.base_formal_version_id" />
              <Field label="创建时间" :value="formatDate(selectedVersion.created_at)" />
              <Field label="更新时间" :value="formatDate(selectedVersion.updated_at)" />
            </dl>

            <section class="mt-6 border-t border-border pt-5" aria-labelledby="detail-tickets-title">
              <h4 id="detail-tickets-title" class="text-sm font-semibold text-text">关联工单</h4>
              <TicketList class="mt-3" :tickets="ticketsFor(selectedVersion)" />
            </section>

            <section v-if="failedChecksFor(selectedVersion).length" class="mt-6 border-t border-border pt-5" aria-labelledby="detail-failed-checks-title">
              <h4 id="detail-failed-checks-title" class="text-sm font-semibold text-text">未通过检查</h4>
              <ul class="mt-3 space-y-2">
                <li v-for="check in failedChecksFor(selectedVersion)" :key="`${check.name}-${check.message}`" class="rounded-[6px] border border-danger/30 bg-danger/10 px-3 py-2 text-sm">
                  <p class="font-medium text-text">{{ check.name || '检查项' }}</p>
                  <p class="mt-1 break-words text-text-secondary">{{ check.message || '未提供说明' }}</p>
                </li>
              </ul>
            </section>

            <div v-if="canRequestApproval(selectedVersion) || hasApprovalState(selectedVersion) || isSubmitted(selectedVersion)" class="mt-6 flex min-w-0 flex-wrap items-center justify-end gap-3 border-t border-border pt-5">
              <span v-if="hasApprovalState(selectedVersion) || isSubmitted(selectedVersion)" class="text-sm text-text-secondary">
                {{ approvalStateLabel(selectedVersion) }}
              </span>
              <button
                v-if="canShowSubmit(selectedVersion)"
                type="button"
                class="rounded-[8px] border border-accent bg-accent px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="isSubmitting(selectedVersion)"
                @click="openSubmitConfirmation(selectedVersion)"
              >
                {{ isSubmitting(selectedVersion) ? '提交中...' : '提交发布审批' }}
              </button>
            </div>
          </div>
        </article>
      </div>

      <div v-if="confirmVersion" class="fixed inset-0 z-50 flex min-h-full items-center justify-center overflow-y-auto bg-black/50 p-4" role="presentation" @click.self="closeSubmitConfirmation">
        <article
          class="my-auto w-full max-w-lg min-w-0 rounded-[8px] border border-border bg-surface p-4 shadow-xl sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="submit-approval-title"
          @keydown.esc="closeSubmitConfirmation"
        >
          <header class="flex min-w-0 items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs font-medium text-accent">发布审批</p>
              <h3 id="submit-approval-title" class="mt-1 text-lg font-semibold text-text">确认提交审批？</h3>
            </div>
            <button type="button" class="shrink-0 rounded-[6px] px-2 py-1 text-sm text-text-secondary hover:bg-bg hover:text-text" :disabled="isSubmitting(confirmVersion)" aria-label="关闭提交审批确认" @click="closeSubmitConfirmation">
              关闭
            </button>
          </header>

          <div class="mt-5 rounded-[8px] border border-border bg-bg p-4">
            <p class="break-words text-sm font-medium text-text">{{ confirmVersion.version }}<span v-if="confirmVersion.title"> · {{ confirmVersion.title }}</span></p>
            <dl class="mt-3 grid gap-3 sm:grid-cols-2">
              <Field label="测试结果" :value="testStatus(confirmVersion)" />
              <Field label="目标环境" :value="targetEnvironment(confirmVersion)" />
            </dl>
          </div>
          <p class="mt-4 text-sm leading-6 text-text-secondary">
            此操作只会创建待处理的发布审批记录，不会改变版本状态。
          </p>
          <p v-if="submitDialogError" class="mt-4 rounded-[8px] border border-danger/40 bg-danger/10 px-3 py-3 text-sm text-text" role="alert">
            {{ submitDialogError }}
          </p>

          <div class="mt-6 flex min-w-0 flex-wrap justify-end gap-2">
            <button type="button" class="rounded-[8px] border border-border px-3 py-2 text-sm text-text-secondary hover:border-accent hover:text-text disabled:cursor-not-allowed disabled:opacity-50" :disabled="isSubmitting(confirmVersion)" @click="closeSubmitConfirmation">
              取消
            </button>
            <button type="button" class="rounded-[8px] border border-accent bg-accent px-3 py-2 text-sm font-medium text-white hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50" :disabled="isSubmitting(confirmVersion)" @click="submitApproval">
              {{ isSubmitting(confirmVersion) ? '提交中...' : '确认提交' }}
            </button>
          </div>
        </article>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useSettingsStore } from '../../stores/settings'
import {
  createIdempotencyKey,
  getVersion,
  listFormalVersions,
  listTestVersions,
  submitReleaseApproval,
  WorkbenchVersionsApiError,
} from '../../services/workbenchVersions.js'

const settings = useSettingsStore()
const formalVersions = ref([])
const testVersions = ref([])
const loading = ref(true)
const refreshing = ref(false)
const hasLoaded = ref(false)
const error = ref('')
const notice = ref('')
const selectedVersion = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const confirmVersion = ref(null)
const submitDialogError = ref('')
const submitKey = ref('')
const submittingIds = ref(new Set())
const submittedIds = ref(new Set())

let listController
let detailController
let loadToken = 0

const formalCount = computed(() => formalVersions.value.length)
const testCount = computed(() => testVersions.value.length)

const statusLabels = {
  recorded: '已记录',
  draft: '草稿',
  ready_for_test: '待测试',
  testing: '测试中',
  passed: '测试通过',
  failed: '测试失败',
  approved: '已批准',
  released: '已发布',
  rolled_back: '已回退',
  queued: '排队中',
  running: '测试中',
  expired: '已过期',
}

function versionTypeLabel(type) {
  return type === 'test' ? '测试版本' : '正式版本'
}

function statusLabel(status) {
  return statusLabels[status] || status || '未提供'
}

function statusTone(status) {
  if (['passed', 'approved', 'released'].includes(status)) return 'border-success/30 bg-success/10 text-success'
  if (['failed', 'rolled_back'].includes(status)) return 'border-danger/40 bg-danger/10 text-danger'
  if (['testing', 'running', 'queued', 'ready_for_test'].includes(status)) return 'border-warn/40 bg-warn/10 text-warn'
  return 'border-border bg-bg text-text-secondary'
}

function metadataOf(version) {
  return version?.metadata && typeof version.metadata === 'object' ? version.metadata : {}
}

function firstValue(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== '') ?? ''
}

function buildStatus(version) {
  const metadata = metadataOf(version)
  return firstValue(version?.build_status, version?.buildStatus, metadata.build_status, metadata.buildStatus, metadata.build?.status)
    || '未提供'
}

function testStatus(version) {
  const metadata = metadataOf(version)
  return firstValue(version?.test_status, version?.testStatus, metadata.test_status, metadata.testStatus, version?.version_type === 'test' ? version?.status : '')
    || '未提供'
}

function targetEnvironment(version) {
  const metadata = metadataOf(version)
  return firstValue(version?.target_environment, version?.environment, metadata.target_environment, metadata.environment) || '未提供'
}

function versionDescription(version) {
  return firstValue(version?.changelog, version?.description)
}

function ticketsFor(version) {
  if (Array.isArray(version?.tickets)) return version.tickets
  if (Array.isArray(version?.ticket_ids)) return version.ticket_ids.map((ticketId) => ({ ticket_id: ticketId }))
  return []
}

function failedChecksFor(version) {
  const metadata = metadataOf(version)
  const checks = firstValue(version?.failed_checks, metadata.failed_checks, metadata.test?.failed_checks)
  return Array.isArray(checks) ? checks : []
}

function allowedActionsFor(version) {
  const metadata = metadataOf(version)
  const actions = firstValue(version?.allowed_actions, metadata.allowed_actions)
  return Array.isArray(actions) ? actions : []
}

function approvalState(version) {
  const metadata = metadataOf(version)
  return firstValue(version?.approval_status, metadata.approval_status, version?.approval?.status)
}

function hasApprovalState(version) {
  return ['pending', 'approved'].includes(approvalState(version))
}

function isSubmitted(version) {
  return submittedIds.value.has(String(version?.id))
}

function isSubmitting(version) {
  return submittingIds.value.has(String(version?.id))
}

function canRequestApproval(version) {
  return Boolean(
    version?.version_type === 'test'
    && testStatus(version) === 'passed'
    && allowedActionsFor(version).includes('submit_approval')
    && !hasApprovalState(version),
  )
}

function canShowSubmit(version) {
  return canRequestApproval(version) && !isSubmitted(version)
}

function approvalStateLabel(version) {
  if (isSubmitted(version) || approvalState(version) === 'pending') return '审批处理中'
  if (approvalState(version) === 'approved') return '审批已通过'
  return ''
}

function formatDate(value) {
  if (!value) return '未提供'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function errorMessage(cause) {
  if (cause instanceof WorkbenchVersionsApiError) {
    if (cause.code === 'WB_APPROVAL_PENDING' || cause.status === 409) return '该测试版本已有审批记录，请刷新列表确认最新状态。'
    if (cause.code === 'WB_TEST_NOT_PASSED') return '只有测试通过的版本可以提交发布审批。'
    return cause.message
  }
  return cause?.message || '版本请求失败，请重试。'
}

async function loadVersions() {
  listController?.abort()
  listController = new AbortController()
  const token = ++loadToken
  const hasItems = formalVersions.value.length > 0 || testVersions.value.length > 0
  loading.value = !hasItems
  refreshing.value = hasItems
  error.value = ''

  try {
    const [formalResult, testResult] = await Promise.all([
      listFormalVersions({ apiBase: settings.apiBase, signal: listController.signal }),
      listTestVersions({ apiBase: settings.apiBase, signal: listController.signal }),
    ])
    if (token !== loadToken) return false
    formalVersions.value = formalResult.items
    testVersions.value = testResult.items
    hasLoaded.value = true
    return true
  } catch (cause) {
    if (cause?.name === 'AbortError' || token !== loadToken) return false
    error.value = errorMessage(cause)
    hasLoaded.value = true
    return false
  } finally {
    if (token === loadToken) {
      loading.value = false
      refreshing.value = false
    }
  }
}

async function openDetail(version) {
  detailController?.abort()
  detailController = new AbortController()
  selectedVersion.value = version
  detailLoading.value = true
  detailError.value = ''
  try {
    selectedVersion.value = await getVersion(version.id, { apiBase: settings.apiBase, signal: detailController.signal })
  } catch (cause) {
    if (cause?.name === 'AbortError') return
    detailError.value = errorMessage(cause)
  } finally {
    if (selectedVersion.value?.id === version.id) detailLoading.value = false
  }
}

function closeDetail() {
  detailController?.abort()
  selectedVersion.value = null
  detailError.value = ''
  detailLoading.value = false
}

function openSubmitConfirmation(version) {
  if (!canShowSubmit(version) || isSubmitting(version)) return
  confirmVersion.value = version
  submitKey.value = createIdempotencyKey(version.id)
  submitDialogError.value = ''
}

function closeSubmitConfirmation(force = false) {
  if (!force && confirmVersion.value && isSubmitting(confirmVersion.value)) return
  confirmVersion.value = null
  submitKey.value = ''
  submitDialogError.value = ''
}

async function submitApproval() {
  const version = confirmVersion.value
  if (!version || !canShowSubmit(version) || isSubmitting(version)) return

  const versionId = String(version.id)
  const nextSubmitting = new Set(submittingIds.value)
  nextSubmitting.add(versionId)
  submittingIds.value = nextSubmitting
  submitDialogError.value = ''
  error.value = ''

  try {
    await submitReleaseApproval(version.id, {
      apiBase: settings.apiBase,
      idempotencyKey: submitKey.value,
    })
    const nextSubmitted = new Set(submittedIds.value)
    nextSubmitted.add(versionId)
    submittedIds.value = nextSubmitted
    closeSubmitConfirmation(true)
    notice.value = `版本 ${version.version} 已提交发布审批。`
    await loadVersions()
  } catch (cause) {
    submitDialogError.value = errorMessage(cause)
    if (cause instanceof WorkbenchVersionsApiError && (cause.code === 'WB_APPROVAL_PENDING' || cause.status === 409)) {
      notice.value = '该测试版本的审批状态已发生变化，请刷新列表确认。'
    }
  } finally {
    const nextSubmitting = new Set(submittingIds.value)
    nextSubmitting.delete(versionId)
    submittingIds.value = nextSubmitting
  }
}

watch(() => settings.apiBase, () => {
  loadVersions()
})

onMounted(() => loadVersions())

onBeforeUnmount(() => {
  listController?.abort()
  detailController?.abort()
})
</script>

<script>
import { defineComponent, h } from 'vue'

const Field = defineComponent({
  name: 'VersionField',
  props: { label: String, value: [String, Number] },
  setup(props) {
    return () => h('div', { class: 'min-w-0' }, [
      h('dt', { class: 'text-xs text-text-secondary' }, props.label),
      h('dd', { class: 'mt-1 break-words text-sm text-text' }, props.value === undefined || props.value === null || props.value === '' ? '未提供' : String(props.value)),
    ])
  },
})

const TicketList = defineComponent({
  name: 'VersionTicketList',
  props: { tickets: { type: Array, default: () => [] } },
  setup(props) {
    return () => props.tickets.length
      ? h('ul', { class: 'grid min-w-0 gap-2 sm:grid-cols-2' }, props.tickets.map((ticket) => {
        const item = typeof ticket === 'string' ? { ticket_id: ticket } : ticket || {}
        return h('li', { key: `${item.ticket_id || item.id || 'ticket'}-${item.title || ''}`, class: 'min-w-0 rounded-[6px] border border-border bg-bg px-3 py-2' }, [
          h('p', { class: 'break-all text-sm font-medium text-text' }, item.ticket_id || item.id || '未提供'),
          item.title ? h('p', { class: 'mt-1 break-words text-xs text-text-secondary' }, item.title) : null,
          item.status ? h('p', { class: 'mt-1 text-xs text-text-secondary' }, `状态：${item.status}`) : null,
        ])
      }))
      : h('p', { class: 'text-sm text-text-secondary' }, '暂无关联工单')
  },
})

const VersionSection = defineComponent({
  name: 'VersionSection',
  components: { Field, TicketList },
  props: {
    title: String,
    description: String,
    emptyLabel: String,
    versions: { type: Array, default: () => [] },
    loading: Boolean,
    isTest: Boolean,
  },
  emits: ['open', 'submit'],
  setup(props, { emit }) {
    const statusLabels = {
      recorded: '已记录', draft: '草稿', ready_for_test: '待测试', testing: '测试中',
      passed: '测试通过', failed: '测试失败', approved: '已批准', released: '已发布',
      rolled_back: '已回退', queued: '排队中', running: '测试中', expired: '已过期',
    }
    const label = (status) => statusLabels[status] || status || '未提供'
    const tone = (status) => {
      if (['passed', 'approved', 'released'].includes(status)) return 'border-success/30 bg-success/10 text-success'
      if (['failed', 'rolled_back'].includes(status)) return 'border-danger/40 bg-danger/10 text-danger'
      if (['testing', 'running', 'queued', 'ready_for_test'].includes(status)) return 'border-warn/40 bg-warn/10 text-warn'
      return 'border-border bg-bg text-text-secondary'
    }
    const metadata = (version) => version?.metadata && typeof version.metadata === 'object' ? version.metadata : {}
    const value = (...values) => values.find((item) => item !== undefined && item !== null && item !== '') ?? ''
    const build = (version) => value(version?.build_status, version?.buildStatus, metadata(version).build_status, metadata(version).buildStatus, metadata(version).build?.status) || '未提供'
    const test = (version) => value(version?.test_status, version?.testStatus, metadata(version).test_status, metadata(version).testStatus, version?.version_type === 'test' ? version?.status : '') || '未提供'
    const environment = (version) => value(version?.target_environment, version?.environment, metadata(version).target_environment, metadata(version).environment) || '未提供'
    const tickets = (version) => Array.isArray(version?.tickets) ? version.tickets : (version?.ticket_ids || []).map((ticketId) => ({ ticket_id: ticketId }))
    const actions = (version) => Array.isArray(version?.allowed_actions) ? version.allowed_actions : (Array.isArray(metadata(version).allowed_actions) ? metadata(version).allowed_actions : [])
    const approval = (version) => value(version?.approval_status, metadata(version).approval_status, version?.approval?.status)
    const canRequest = (version) => props.isTest && test(version) === 'passed' && actions(version).includes('submit_approval') && !['pending', 'approved'].includes(approval(version))
    return () => h('section', { class: 'min-w-0', 'aria-labelledby': `${props.title.replace(/\s+/g, '-').toLowerCase()}-title` }, [
      h('header', { class: 'flex min-w-0 flex-wrap items-end justify-between gap-3 border-b border-border pb-3' }, [
        h('div', { class: 'min-w-0' }, [
          h('h3', { id: `${props.title.replace(/\s+/g, '-').toLowerCase()}-title`, class: 'text-lg font-semibold text-text' }, props.title),
          h('p', { class: 'mt-1 text-sm text-text-secondary' }, props.description),
        ]),
        h('span', { class: 'shrink-0 text-xs text-text-secondary' }, `${props.versions.length} 条`),
      ]),
      props.loading && props.versions.length
        ? h('p', { class: 'mt-3 text-xs text-text-secondary', role: 'status' }, '正在更新...')
        : null,
      !props.versions.length
        ? h('div', { class: 'mt-4 rounded-[8px] border border-dashed border-border bg-bg px-4 py-8 text-center text-sm text-text-secondary' }, props.emptyLabel)
        : h('div', { class: 'mt-4 grid min-w-0 gap-3' }, props.versions.map((version) => h('article', { key: version.id, class: 'min-w-0 rounded-[8px] border border-border bg-surface p-4 sm:p-5' }, [
            h('div', { class: 'flex min-w-0 flex-wrap items-start justify-between gap-3' }, [
              h('div', { class: 'min-w-0 flex-1' }, [
                h('div', { class: 'flex min-w-0 flex-wrap items-center gap-2' }, [
                  h('h4', { class: 'break-words text-base font-semibold text-text' }, version.version || '未命名版本'),
                  h('span', { class: ['rounded-full border px-2.5 py-1 text-xs font-medium', tone(version.status)] }, label(version.status)),
                  version.is_current ? h('span', { class: 'rounded-full border border-success/30 bg-success/10 px-2.5 py-1 text-xs font-medium text-success' }, '当前') : null,
                ]),
                version.title ? h('p', { class: 'mt-1 break-words text-sm text-text-secondary' }, version.title) : null,
                h('p', { class: 'mt-1 break-all text-xs text-text-secondary' }, `ID：${version.id}`),
              ]),
              h('time', { class: 'shrink-0 text-xs text-text-secondary', datetime: version.created_at }, version.created_at || '未提供'),
            ]),
            h('dl', { class: 'mt-4 grid min-w-0 gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-4' }, [
              h(Field, { label: '构建状态', value: build(version) }),
              h(Field, { label: '测试结果', value: test(version) }),
              h(Field, { label: '目标环境', value: environment(version) }),
              h(Field, { label: '提交标识', value: version.commit_sha || version.commit || '未提供' }),
            ]),
            h('div', { class: 'mt-4 border-t border-border pt-3' }, [
              h('p', { class: 'text-xs font-medium text-text-secondary' }, '关联工单'),
              h(TicketList, { class: 'mt-2', tickets: tickets(version) }),
            ]),
            h('div', { class: 'mt-4 flex min-w-0 flex-wrap items-center justify-end gap-2' }, [
              canRequest(version) ? h('button', { type: 'button', class: 'rounded-[8px] border border-accent bg-accent px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-accent/90', onClick: (event) => { event.stopPropagation(); emit('submit', version) } }, '提交发布审批') : null,
              !canRequest(version) && ['pending', 'approved'].includes(approval(version)) ? h('span', { class: 'text-xs text-text-secondary' }, approval(version) === 'approved' ? '审批已通过' : '审批处理中') : null,
              h('button', { type: 'button', class: 'rounded-[8px] border border-border px-3 py-2 text-sm text-text-secondary transition-colors hover:border-accent hover:text-text', onClick: () => emit('open', version) }, '查看详情'),
            ]),
          ]))),
    ])
  },
})

export default { components: { Field, TicketList, VersionSection } }
</script>
