<template>
  <UiWidgetFrame data-figma-node="349:405" title="今日任务" :meta="`${tasks.length} 项`" :loading="loading" :error="error" :empty="!tasks.length && !loading && !error" empty-title="今天还没有任务" empty-description="把下一步行动放进时间线，保持学习节奏。">
    <div class="task-list">
      <div v-for="task in tasks" :key="task.id" class="task-row" :data-task-id="task.id" role="button" tabindex="0" @click="selectTask(task.id)" @keydown.enter="selectTask(task.id)" @keydown.space.prevent="selectTask(task.id)">
        <span class="task-row__rail" :data-status="task.status" aria-hidden="true" />
        <div class="task-row__main">
          <div class="task-row__heading"><strong>{{ task.title }}</strong><UiBadge :status="badgeStatus(task.status)" :label="statusLabel(task.status)" /></div>
          <div class="task-row__meta">{{ task.time || '待安排' }}</div>
          <UiProgress v-if="typeof task.progress === 'number'" :value="task.progress" :show-value="false" />
        </div>
      </div>
    </div>
  </UiWidgetFrame>
</template>

<script setup>
import UiBadge from '../components/data-display/UiBadge.vue'
import UiProgress from '../components/data-display/UiProgress.vue'
import UiWidgetFrame from '../patterns/UiWidgetFrame.vue'

defineProps({ tasks: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['select'])
const statusLabels = { pending: '未开始', running: '进行中', done: '已完成', error: '失败' }
const statusTone = { pending: 'neutral', running: 'info', done: 'success', error: 'danger' }
const statusLabel = (status) => statusLabels[status] || statusLabels.pending
const badgeStatus = (status) => statusTone[status] || 'neutral'
const selectTask = (id) => emit('select', id)
</script>

<style scoped>
.task-list { display: grid; gap: var(--ui-space-2); }
.task-row { display: grid; grid-template-columns: 4px minmax(0, 1fr); gap: var(--ui-space-3); cursor: pointer; border-radius: var(--ui-radius-md); padding: var(--ui-space-3); transition: background var(--ui-duration-fast) var(--ui-ease-standard); }
.task-row:hover, .task-row:focus-visible { outline: none; background: var(--ui-color-surface-raised); }
.task-row__rail { border-radius: 99px; background: var(--ui-color-text-muted); }
.task-row__rail[data-status='running'] { background: var(--ui-color-action); }
.task-row__rail[data-status='done'] { background: var(--ui-color-success); }
.task-row__rail[data-status='error'] { background: var(--ui-color-danger); }
.task-row__main { display: grid; min-width: 0; gap: var(--ui-space-1); }
.task-row__heading { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: var(--ui-space-3); }
.task-row__heading strong { min-width: 0; overflow: hidden; color: var(--ui-color-text-strong); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.task-row__meta { color: var(--ui-color-text-muted); font-size: 11px; }
</style>
