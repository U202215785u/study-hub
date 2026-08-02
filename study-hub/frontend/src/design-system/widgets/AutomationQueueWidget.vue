<template>
  <UiWidgetFrame data-figma-node="349:369" title="自动化队列" :meta="`${items.length} 项`" :loading="loading" :error="error" :empty="!items.length && !loading && !error" empty-title="队列为空" empty-description="提交一个解析任务后，它会出现在这里。">
    <div class="queue-list">
      <div v-for="item in items" :key="item.id" class="queue-row" :data-queue-id="item.id" role="button" tabindex="0" @click="emit('open', item.id)" @keydown.enter="emit('open', item.id)" @keydown.space.prevent="emit('open', item.id)">
        <div class="queue-row__copy"><strong>{{ item.title }}</strong><UiBadge :status="badgeStatus(item.status)" :label="statusLabel(item.status)" /></div>
        <UiProgress :value="item.progress" :show-value="true" />
        <UiButton v-if="item.status === 'error'" size="sm" variant="text" :data-retry-id="item.id" @click.stop="emit('retry', item.id)">重试</UiButton>
      </div>
    </div>
  </UiWidgetFrame>
</template>

<script setup>
import UiBadge from '../components/data-display/UiBadge.vue'
import UiProgress from '../components/data-display/UiProgress.vue'
import UiButton from '../components/general/UiButton.vue'
import UiWidgetFrame from '../patterns/UiWidgetFrame.vue'

defineProps({ items: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['open', 'retry'])
const statusLabels = { pending: '排队中', running: '处理中', done: '已完成', error: '失败' }
const statusTone = { pending: 'neutral', running: 'info', done: 'success', error: 'danger' }
const statusLabel = (status) => statusLabels[status] || statusLabels.pending
const badgeStatus = (status) => statusTone[status] || 'neutral'
</script>

<style scoped>
.queue-list { display: grid; gap: var(--ui-space-2); }
.queue-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: var(--ui-space-2) var(--ui-space-3); border-radius: var(--ui-radius-md); padding: var(--ui-space-3); cursor: pointer; }
.queue-row:hover, .queue-row:focus-visible { outline: none; background: var(--ui-color-surface-raised); }
.queue-row__copy { display: flex; min-width: 0; align-items: center; gap: var(--ui-space-3); }
.queue-row__copy strong { min-width: 0; overflow: hidden; color: var(--ui-color-text-strong); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.queue-row > .ui-progress { grid-column: 1 / -1; }
.queue-row > .ui-button { justify-self: end; }
</style>
