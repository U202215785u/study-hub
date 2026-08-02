<template>
  <span class="ui-tag" :data-tone="tone"><slot /></span>
</template>

<script setup>
defineProps({
  tone: { type: String, default: 'neutral', validator: (value) => ['neutral', 'lime', 'purple', 'orange', 'peach', 'cream'].includes(value) },
})
</script>

<style scoped>
.ui-tag { display: inline-flex; align-items: center; min-height: 24px; max-width: 100%; box-sizing: border-box; padding: 0 var(--ui-space-2); border-radius: 999px; background: var(--ui-color-surface-raised); color: var(--ui-color-text); font: 700 11px/1 var(--ui-font-sans); white-space: nowrap; }
.ui-tag[data-tone='lime'] { background: color-mix(in srgb, var(--ui-color-action) 18%, transparent); color: var(--ui-color-action); }
.ui-tag[data-tone='purple'] { background: color-mix(in srgb, var(--ui-color-content-purple) 20%, transparent); color: var(--ui-color-content-purple); }
.ui-tag[data-tone='orange'] { background: color-mix(in srgb, var(--ui-color-content-orange) 20%, transparent); color: var(--ui-color-content-orange); }
.ui-tag[data-tone='peach'] { background: color-mix(in srgb, var(--ui-color-content-peach) 18%, transparent); color: var(--ui-color-content-peach); }
.ui-tag[data-tone='cream'] { background: color-mix(in srgb, var(--ui-color-content-cream) 18%, transparent); color: var(--ui-color-content-cream); }
</style>
