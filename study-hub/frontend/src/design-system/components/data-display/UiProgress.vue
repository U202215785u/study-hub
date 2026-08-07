<template>
  <div class="ui-progress" :data-type="type" :data-size="size" :data-status="status">
    <div v-if="label || showValue" class="ui-progress__row">
      <span v-if="label" class="ui-progress__label">{{ label }}</span>
      <span v-if="showValue" class="ui-progress__value">{{ percent }}%</span>
    </div>
    <div class="ui-progress__track" role="progressbar" :aria-label="ariaLabel || label || '进度'" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="percent">
      <template v-if="type === 'segmented'">
        <span v-for="segment in 10" :key="segment" class="ui-progress__segment" :class="{ 'ui-progress__segment--filled': segment * 10 <= percent }" />
      </template>
      <span v-else class="ui-progress__fill" :style="{ width: `${percent}%` }" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  type: { type: String, default: 'linear', validator: (value) => ['linear', 'segmented'].includes(value) },
  size: { type: String, default: 'default', validator: (value) => ['default', 'compact'].includes(value) },
  status: { type: String, default: 'active', validator: (value) => ['active', 'success', 'warning', 'danger'].includes(value) },
  label: { type: String, default: '' },
  ariaLabel: { type: String, default: '' },
  showValue: Boolean,
})
const percent = computed(() => Math.min(100, Math.max(0, Number.isFinite(props.value) ? props.value : 0)))
</script>

<style scoped>
.ui-progress { display: grid; gap: var(--ui-space-2); min-width: 0; }
.ui-progress__row { display: flex; justify-content: space-between; gap: var(--ui-space-3); color: var(--ui-color-text-muted); font-size: 12px; line-height: 1.3; }
.ui-progress__value { color: var(--ui-color-text-strong); font-variant-numeric: tabular-nums; }
.ui-progress__track { display: flex; align-items: center; gap: 3px; width: 100%; min-height: 8px; overflow: hidden; border-radius: 999px; background: var(--ui-color-surface-muted); }
.ui-progress__fill { display: block; height: 8px; border-radius: inherit; background: var(--ui-color-action); transition: width var(--ui-duration-normal) var(--ui-ease-standard); }
.ui-progress__segment { display: block; height: 8px; flex: 1 1 0; background: var(--ui-color-surface-muted); }
.ui-progress__segment--filled { background: var(--ui-color-action); }
.ui-progress[data-size='compact'] { gap: var(--ui-space-1); }
.ui-progress[data-size='compact'] .ui-progress__track { min-height: 5px; }
.ui-progress[data-size='compact'] .ui-progress__fill,
.ui-progress[data-size='compact'] .ui-progress__segment { height: 5px; }
.ui-progress[data-status='success'] .ui-progress__fill,
.ui-progress[data-status='success'] .ui-progress__segment--filled { background: var(--ui-color-success); }
.ui-progress[data-status='warning'] .ui-progress__fill,
.ui-progress[data-status='warning'] .ui-progress__segment--filled { background: var(--ui-color-warning); }
.ui-progress[data-status='danger'] .ui-progress__fill,
.ui-progress[data-status='danger'] .ui-progress__segment--filled { background: var(--ui-color-danger); }
</style>
