<template>
  <UiWidgetFrame data-figma-node="349:471" title="最近知识" :meta="`${items.length} 篇`" :loading="loading" :error="error" :empty="!items.length && !loading && !error" empty-title="知识库为空" empty-description="导入文档后，最近内容会出现在这里。">
    <div class="knowledge-list">
      <button v-for="item in items" :key="item.id" class="knowledge-row" :data-knowledge-id="item.id" type="button" @click="emit('open', item.id)">
        <span class="knowledge-row__mark" aria-hidden="true" />
        <span class="knowledge-row__copy"><strong>{{ item.title }}</strong><small>{{ item.meta }}</small></span>
        <UiBadge :status="badgeStatus(item.status)" :label="statusLabel(item.status)" />
      </button>
    </div>
  </UiWidgetFrame>
</template>

<script setup>
import UiBadge from '../components/data-display/UiBadge.vue'
import UiWidgetFrame from '../patterns/UiWidgetFrame.vue'

defineProps({ items: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['open'])
const statusLabels = { ready: '可阅读', indexing: '整理中', error: '需处理' }
const statusTone = { ready: 'success', indexing: 'info', error: 'warning' }
const statusLabel = (status) => statusLabels[status] || statusLabels.ready
const badgeStatus = (status) => statusTone[status] || 'neutral'
</script>

<style scoped>
.knowledge-list { display: grid; gap: var(--ui-space-1); }
.knowledge-row { display: flex; min-width: 0; align-items: center; gap: var(--ui-space-3); border: 0; border-radius: var(--ui-radius-md); padding: var(--ui-space-3); background: transparent; color: inherit; text-align: left; cursor: pointer; }
.knowledge-row:hover, .knowledge-row:focus-visible { outline: none; background: var(--ui-color-surface-raised); }
.knowledge-row__mark { width: 30px; height: 30px; flex: 0 0 auto; border-radius: var(--ui-radius-sm); background: var(--ui-color-content-purple); opacity: .8; }
.knowledge-row__copy { display: grid; min-width: 0; flex: 1 1 auto; gap: 3px; }
.knowledge-row__copy strong { overflow: hidden; color: var(--ui-color-text-strong); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.knowledge-row__copy small { color: var(--ui-color-text-muted); font-size: 11px; }
</style>
