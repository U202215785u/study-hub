<template><div class="ui-dashboard-item" :data-span="span"><slot /></div></template>

<script setup>
defineProps({
  span: { type: String, default: '1x1', validator: (value) => ['1x1', '2x1', '2x2', '2x3'].includes(value) },
})
</script>

<style scoped>
.ui-dashboard-item { min-width: 0; }
@media (min-width: 768px) {
  .ui-dashboard-item[data-span^='2x'] { grid-column: span 2; }
  .ui-dashboard-item[data-span='2x2'] { grid-row: span 2; }
  .ui-dashboard-item[data-span='2x3'] { grid-row: span 3; }
}
</style>
