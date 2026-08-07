<template>
  <section class="heatmap-style-picker" aria-labelledby="heatmap-style-title">
    <div class="heatmap-style-picker__heading">
      <h2 id="heatmap-style-title">热力图样式</h2>
      <span>预留样式会在设计完成后接入</span>
    </div>
    <div class="heatmap-style-picker__items" role="listbox" aria-label="热力图样式">
      <button
        v-for="style in styles"
        :key="style.id"
        type="button"
        role="option"
        :aria-selected="style.id === modelValue"
        :disabled="style.status !== 'available'"
        :data-style-id="style.id"
        :data-status="style.status"
        @click="$emit('update:modelValue', style.id)"
      >
        <strong>{{ style.name }}</strong>
        <span>{{ style.status === 'available' ? '可用' : '即将支持' }}</span>
      </button>
    </div>
  </section>
</template>

<script setup>
defineProps({ styles: { type: Array, default: () => [] }, modelValue: { type: String, default: 'grid' } })
defineEmits(['update:modelValue'])
</script>

<style scoped>
.heatmap-style-picker { display: grid; gap: 12px; }
.heatmap-style-picker__heading { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.heatmap-style-picker h2 { margin: 0; font-size: 16px; }
.heatmap-style-picker__heading span { color: var(--ui-color-text-muted); font-size: 11px; }
.heatmap-style-picker__items { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.heatmap-style-picker button { display: grid; min-width: 0; gap: 5px; border: 1px solid var(--ui-color-border); border-radius: 8px; padding: 11px; background: var(--ui-color-surface); color: var(--ui-color-text); text-align: left; cursor: pointer; }
.heatmap-style-picker button[aria-selected='true'] { border-color: var(--ui-color-action); background: color-mix(in srgb, var(--ui-color-action) 12%, transparent); }
.heatmap-style-picker button:disabled { opacity: .55; cursor: not-allowed; }
.heatmap-style-picker button span { color: var(--ui-color-text-muted); font-size: 11px; }
@media (max-width: 640px) { .heatmap-style-picker__items { grid-template-columns: repeat(2, minmax(0, 1fr)); } .heatmap-style-picker__heading { align-items: flex-start; flex-direction: column; } }
</style>
