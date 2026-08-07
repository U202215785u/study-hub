<template>
  <section class="min-w-0" aria-labelledby="approvals-panel-title">
    <div class="flex min-w-0 flex-wrap items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-xs font-medium text-accent">审批</p>
        <h3 id="approvals-panel-title" class="mt-1 text-lg font-semibold text-text">待审批</h3>
        <p class="mt-1 text-sm text-text-secondary">需要你确认后才能继续的工作台操作</p>
      </div>
      <button
        type="button"
        class="shrink-0 rounded-[8px] border border-border px-3 py-2 text-sm text-text transition-colors hover:border-accent disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="loading || refreshing || Boolean(submittingId)"
        @click="loadApprovals"
      >
        {{ loading || refreshing ? '刷新中…' : '刷新' }}
      </button>
    </div>

    <div v-if="error" class="mt-4 flex min-w-0 flex-wrap items-center justify-between gap-3 rounded-[8px] border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700" role="alert">
      <span class="min-w-0 break-words">{{ error }}</span>
      <button
        type="button"
        class="shrink-0 rounded-[6px] border border-red-300 px-2.5 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="loading || refreshing || Boolean(submittingId)"
        @click="loadApprovals"
      >
        重试
      </button>
    </div>

    <p v-if="notice" class="mt-4 rounded-[8px] border border-green-200 bg-green-50 px-3 py-3 text-sm text-green-700" role="status">
      {{ notice }}
    </p>

    <div v-if="loading" class="mt-5 rounded-[8px] border border-dashed border-border bg-bg px-4 py-8 text-center text-sm text-text-secondary" aria-live="polite">
      正在加载待审批事项…
    </div>

    <div v-else-if="!approvals.length" class="mt-5 rounded-[8px] border border-dashed border-border bg-bg px-4 py-8 text-center text-sm text-text-secondary">
      当前没有待审批事项
    </div>

    <div v-else class="mt-5 grid min-w-0 gap-3" :aria-busy="refreshing">
      <article
        v-for="approval in approvals"
        :key="approval.id"
        class="min-w-0 rounded-[8px] border border-border bg-bg p-4 sm:p-5"
      >
        <div class="flex min-w-0 flex-wrap items-center justify-between gap-2">
          <div class="flex min-w-0 flex-wrap items-center gap-2">
            <span class="rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 text-xs font-medium text-accent">
              {{ riskKindLabel(approval.risk_kind) }}
            </span>
            <span class="text-xs text-text-secondary">{{ approval.risk_kind }}</span>
          </div>
          <time v-if="approval.created_at" class="shrink-0 text-xs text-text-secondary" :datetime="approval.created_at">
            {{ formatDate(approval.created_at) }}
          </time>
        </div>

        <p class="mt-4 whitespace-pre-wrap break-words text-sm leading-6 text-text">{{ approval.summary }}</p>

        <div v-if="approval.case_id || approval.task_id" class="mt-3 break-all text-xs text-text-secondary">
          案件：{{ approval.case_id || approval.task_id }}
        </div>

        <div class="mt-4 flex min-w-0 flex-wrap gap-2">
          <button
            type="button"
            class="min-w-[5rem] flex-1 rounded-[8px] border border-accent bg-accent px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
            :disabled="Boolean(submittingId)"
            @click="openDecision(approval, 'approve')"
          >
            批准
          </button>
          <button
            type="button"
            class="min-w-[5rem] flex-1 rounded-[8px] border border-red-300 px-3 py-2.5 text-sm font-medium text-red-700 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
            :disabled="Boolean(submittingId)"
            @click="openDecision(approval, 'reject')"
          >
            拒绝
          </button>
        </div>
      </article>
    </div>

    <div
      v-if="dialogOpen && selectedApproval"
      class="fixed inset-0 z-50 flex min-h-full items-center justify-center overflow-y-auto bg-black/40 p-4"
      role="presentation"
      @click.self="closeDecision"
    >
      <div
        class="my-auto max-h-[calc(100vh-2rem)] w-full max-w-2xl min-w-0 overflow-y-auto rounded-[8px] border border-border bg-surface p-4 shadow-xl sm:p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="approval-dialog-title"
        tabindex="-1"
        @keydown.esc="closeDecision"
      >
        <div class="flex min-w-0 items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs font-medium text-accent">审批确认</p>
            <h4 id="approval-dialog-title" class="mt-1 text-lg font-semibold text-text">
              {{ decision === 'approve' ? '批准审批' : '拒绝审批' }}
            </h4>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-[6px] px-2 py-1 text-sm text-text-secondary hover:bg-bg hover:text-text disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="关闭审批确认框"
            :disabled="isSubmitting"
            @click="closeDecision"
          >
            关闭
          </button>
        </div>

        <div class="mt-5 min-w-0 rounded-[8px] border border-border bg-bg p-3 sm:p-4">
          <div class="flex min-w-0 flex-wrap items-center gap-2 text-xs text-text-secondary">
            <span class="font-medium text-text">风险类型</span>
            <span>{{ riskKindLabel(selectedApproval.risk_kind) }}</span>
            <span aria-hidden="true">·</span>
            <span class="break-all">{{ selectedApproval.risk_kind }}</span>
          </div>
          <p class="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-text">{{ selectedApproval.summary }}</p>
        </div>

        <p v-if="decision === 'approve'" class="mt-4 text-sm leading-6 text-text-secondary">
          批准只表示审批已通过，不表示已经发布。
        </p>
        <label class="mt-4 block text-sm font-medium text-text" for="approval-opinion">审批意见</label>
        <textarea
          id="approval-opinion"
          v-model="opinion"
          class="mt-2 min-h-28 w-full min-w-0 resize-y rounded-[8px] border border-border bg-bg px-3 py-2.5 text-sm leading-6 text-text outline-none placeholder:text-text-secondary focus:border-accent disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isSubmitting"
          placeholder="填写本次审批的理由或补充说明（可选）"
        />

        <p v-if="dialogError" class="mt-3 break-words text-sm text-red-700" role="alert">{{ dialogError }}</p>

        <div class="mt-5 flex min-w-0 flex-wrap-reverse justify-end gap-2">
          <button
            type="button"
            class="min-w-[5rem] rounded-[8px] border border-border px-3 py-2.5 text-sm text-text transition-colors hover:bg-bg disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="isSubmitting"
            @click="closeDecision"
          >
            取消
          </button>
          <button
            type="button"
            class="min-w-[6rem] rounded-[8px] border px-3 py-2.5 text-sm font-medium text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50"
            :class="decision === 'approve' ? 'border-accent bg-accent hover:bg-accent/90' : 'border-red-600 bg-red-600 hover:bg-red-700'"
            :disabled="isSubmitting"
            @click="submitDecision"
          >
            {{ isSubmitting ? '处理中…' : (decision === 'approve' ? '确认批准' : '确认拒绝') }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useSettingsStore } from '../../stores/settings'
import { createIdempotencyKey, getPendingApprovals, resolveApproval, WorkbenchApiError } from '../../services/workbenchApprovals'

const settings = useSettingsStore()
const approvals = ref([])
const loading = ref(false)
const refreshing = ref(false)
const error = ref('')
const notice = ref('')
const dialogError = ref('')
const dialogOpen = ref(false)
const selectedApproval = ref(null)
const decision = ref('approve')
const opinion = ref('')
const decisionKey = ref('')
const submittingId = ref('')

const isSubmitting = computed(() => Boolean(submittingId.value))

const riskLabels = {
  data: '数据',
  deployment: '部署',
  permission: '权限',
  personal_data: '个人数据',
  release: '发布',
}

function riskKindLabel(riskKind) {
  return riskLabels[riskKind] || '受保护操作'
}

function formatDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function errorMessage(value) {
  if (value instanceof WorkbenchApiError) {
    if (value.status === 409 || value.code === 'WB_APPROVAL_ALREADY_DECIDED') {
      return '该审批已被处理，请刷新列表后重试。'
    }
    return value.message
  }
  return value?.message || '审批请求失败，请重试。'
}

async function loadApprovals() {
  if (loading.value || refreshing.value) return false
  const hasItems = approvals.value.length > 0
  loading.value = !hasItems
  refreshing.value = hasItems
  error.value = ''
  try {
    const result = await getPendingApprovals({ apiBase: settings.apiBase })
    approvals.value = result.items
    return true
  } catch (loadError) {
    error.value = errorMessage(loadError)
    return false
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function openDecision(approval, nextDecision) {
  if (isSubmitting.value) return
  selectedApproval.value = approval
  decision.value = nextDecision
  opinion.value = ''
  decisionKey.value = createIdempotencyKey(approval.id)
  dialogError.value = ''
  notice.value = ''
  dialogOpen.value = true
}

function closeDecision(force = false) {
  if (isSubmitting.value && !force) return
  dialogOpen.value = false
  selectedApproval.value = null
  decisionKey.value = ''
  dialogError.value = ''
}

async function submitDecision() {
  if (!selectedApproval.value || isSubmitting.value) return
  const approval = selectedApproval.value
  const approved = decision.value === 'approve'
  submittingId.value = approval.id
  dialogError.value = ''
  error.value = ''
  notice.value = ''

  try {
    await resolveApproval(approval.id, {
      approved,
      response: opinion.value,
      apiBase: settings.apiBase,
      idempotencyKey: decisionKey.value,
    })

    approvals.value = approvals.value.filter((item) => item.id !== approval.id)
    closeDecision(true)
    notice.value = '审批已处理'
    const refreshed = await loadApprovals()
    if (!refreshed) error.value = '审批已处理，但列表刷新失败，请重试。'
  } catch (submitError) {
    if (submitError instanceof WorkbenchApiError && (submitError.status === 409 || submitError.code === 'WB_APPROVAL_ALREADY_DECIDED')) {
      closeDecision(true)
      notice.value = '该审批已被其他处理者处理，请刷新列表确认。'
      const refreshed = await loadApprovals()
      if (!refreshed) error.value = '审批状态可能已变更，列表刷新失败，请重试。'
    } else {
      dialogError.value = errorMessage(submitError)
    }
  } finally {
    submittingId.value = ''
  }
}

watch(() => settings.apiBase, () => {
  loadApprovals()
})

onMounted(() => {
  loadApprovals()
})
</script>
