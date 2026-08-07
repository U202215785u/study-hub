<template>
  <div
    class="ui-inset-surface"
    :data-border="border"
    :data-tone="tone"
    :data-interactive="interactive ? 'true' : undefined"
  >
    <div class="ui-inset-surface__content"><slot /></div>
    <div v-if="$slots.actions" class="ui-inset-surface__actions"><slot name="actions" /></div>
  </div>
</template>

<script setup>
defineProps({
  border: { type: String, default: 'dashed', validator: (value) => ['dashed', 'solid'].includes(value) },
  tone: { type: String, default: 'default', validator: (value) => ['default', 'muted'].includes(value) },
  interactive: Boolean,
})
</script>

<style scoped>
.ui-inset-surface { display: flex; min-width: 0; min-height: 0; box-sizing: border-box; align-items: center; gap: var(--ui-space-2); border: 1px dashed var(--ui-color-border-strong); border-radius: var(--ui-radius-md); padding: 0 var(--ui-space-3); overflow: hidden; background: var(--ui-color-shell); color: var(--ui-color-text); }
.ui-inset-surface[data-border='solid'] { border-style: solid; }
.ui-inset-surface[data-tone='muted'] { background: color-mix(in srgb, var(--ui-color-surface-muted) 36%, var(--ui-color-shell)); }
.ui-inset-surface[data-interactive='true']:hover,
.ui-inset-surface[data-interactive='true']:focus-within { border-color: var(--ui-color-action); }
.ui-inset-surface__content { min-width: 0; flex: 1; overflow: hidden; }
.ui-inset-surface__actions { display: flex; flex: 0 0 auto; align-items: center; gap: var(--ui-space-1); }
</style>
