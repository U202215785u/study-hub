<template>
  <span class="ui-spinner" :data-size="size" role="status">
    <span class="ui-spinner__ring" aria-hidden="true" />
    <span class="ui-sr-only">{{ label }}</span>
  </span>
</template>

<script setup>
defineProps({
  size: { type: String, default: 'md', validator: (value) => ['sm', 'md', 'lg'].includes(value) },
  label: { type: String, default: '加载中' },
})
</script>

<style scoped>
.ui-spinner { display: inline-flex; align-items: center; justify-content: center; color: var(--ui-color-action); }
.ui-spinner__ring { display: block; width: 1em; height: 1em; border: 2px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: ui-spinner-rotate 700ms linear infinite; }
.ui-spinner[data-size='sm'] { font-size: 14px; }
.ui-spinner[data-size='md'] { font-size: 20px; }
.ui-spinner[data-size='lg'] { font-size: 28px; }
.ui-sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
@keyframes ui-spinner-rotate { to { transform: rotate(360deg); } }
</style>
