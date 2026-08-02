<template>
  <section class="ui-widget-frame" :aria-label="ariaLabel || title" :data-state="activeState">
    <UiPanelHeader :title="title" :meta="meta" :description="description">
      <template #actions><slot name="actions" /></template>
    </UiPanelHeader>

    <div class="ui-widget-frame__body">
      <template v-if="activeState === 'loading'">
        <slot name="loading"><div class="ui-widget-frame__fallback"><UiSpinner /><span>加载中</span></div></slot>
      </template>
      <template v-else-if="activeState === 'error'">
        <slot name="error"><div class="ui-widget-frame__fallback ui-widget-frame__fallback--error">{{ error }}</div></slot>
      </template>
      <template v-else-if="activeState === 'empty'">
        <slot name="empty"><UiEmpty :title="emptyTitle" :description="emptyDescription" /></slot>
      </template>
      <slot v-else />
    </div>

    <footer v-if="$slots.footer" class="ui-widget-frame__footer"><slot name="footer" /></footer>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import UiEmpty from '../components/feedback/UiEmpty.vue'
import UiSpinner from '../components/feedback/UiSpinner.vue'
import UiPanelHeader from './UiPanelHeader.vue'

const props = defineProps({
  title: { type: String, required: true },
  meta: { type: [String, Number], default: '' },
  description: { type: String, default: '' },
  loading: Boolean,
  error: { type: [String, Boolean], default: '' },
  empty: Boolean,
  emptyTitle: { type: String, default: '暂无内容' },
  emptyDescription: { type: String, default: '' },
  ariaLabel: { type: String, default: '' },
})

const activeState = computed(() => {
  if (props.loading) return 'loading'
  if (props.error) return 'error'
  if (props.empty) return 'empty'
  return 'content'
})
</script>

<style scoped>
.ui-widget-frame { display: flex; min-width: 0; min-height: 100%; box-sizing: border-box; flex-direction: column; gap: var(--ui-space-4); overflow: hidden; border: 1px solid var(--ui-color-border); border-radius: var(--ui-radius-widget); padding: var(--ui-space-5); background: var(--ui-color-surface); box-shadow: var(--ui-shadow-widget); }
.ui-widget-frame__body { min-width: 0; flex: 1 1 auto; }
.ui-widget-frame__fallback { display: flex; min-height: 120px; align-items: center; justify-content: center; gap: var(--ui-space-3); color: var(--ui-color-text-muted); font-size: 13px; text-align: center; }
.ui-widget-frame__fallback--error { color: var(--ui-color-danger); }
.ui-widget-frame__footer { padding-top: var(--ui-space-3); border-top: 1px solid var(--ui-color-border); }
@media (max-width: 767px) { .ui-widget-frame { border-radius: var(--ui-radius-lg); padding: var(--ui-space-4); } }
</style>
