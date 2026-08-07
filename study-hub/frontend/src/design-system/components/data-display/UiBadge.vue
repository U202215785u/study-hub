<template>
  <span class="ui-badge" :data-status="status" :data-size="size">
    <span class="ui-badge__dot" aria-hidden="true" />
    <span>{{ label }}</span>
  </span>
</template>

<script setup>
defineProps({
  status: { type: String, default: 'neutral', validator: (value) => ['neutral', 'info', 'success', 'warning', 'danger'].includes(value) },
  size: { type: String, default: 'default', validator: (value) => ['default', 'compact'].includes(value) },
  label: { type: String, required: true },
})
</script>

<style scoped>
.ui-badge { display: inline-flex; align-items: center; gap: var(--ui-space-2); min-height: 24px; color: var(--ui-color-text); font: 700 12px/1.2 var(--ui-font-sans); }
.ui-badge__dot { width: 7px; height: 7px; flex: 0 0 auto; border-radius: 50%; background: var(--ui-color-text-muted); }
.ui-badge[data-status='info'] .ui-badge__dot { background: var(--ui-color-info); }
.ui-badge[data-status='success'] .ui-badge__dot { background: var(--ui-color-success); }
.ui-badge[data-status='warning'] .ui-badge__dot { background: var(--ui-color-warning); }
.ui-badge[data-status='danger'] .ui-badge__dot { background: var(--ui-color-danger); }
.ui-badge[data-size='compact'] { min-height: 18px; gap: var(--ui-space-1); font-size: 10px; }
.ui-badge[data-size='compact'] .ui-badge__dot { width: 5px; height: 5px; }
</style>
