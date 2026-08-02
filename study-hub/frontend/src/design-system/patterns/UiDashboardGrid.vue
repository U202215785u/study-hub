<template><div class="ui-dashboard-grid"><slot /></div></template>

<style scoped>
.ui-dashboard-grid { display: grid; width: 100%; min-width: 0; grid-template-columns: minmax(0, 1fr); grid-auto-rows: minmax(160px, auto); gap: var(--ui-space-4); }
@media (min-width: 768px) { .ui-dashboard-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ui-space-5); } }
@media (min-width: 1024px) { .ui-dashboard-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (min-width: 1280px) { .ui-dashboard-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--ui-space-6); } }
</style>
