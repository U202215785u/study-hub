<template>
  <div class="bento-dashboard-grid" data-columns="8" :aria-label="ariaLabel">
    <slot />
  </div>
</template>

<script setup>
defineProps({ ariaLabel: { type: String, default: '首页模块' } })
</script>

<style scoped>
.bento-dashboard-grid {
  display: grid;
  width: 100%;
  min-width: 0;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  grid-auto-rows: 153.36px;
  gap: 14.31px;
}
@media (max-width: 1100px) {
  .bento-dashboard-grid { grid-template-columns: repeat(8, minmax(0, 1fr)); min-width: 1010px; }
}
@media (max-width: 767px) {
  .bento-dashboard-grid { min-width: 1010px; }
}
</style>
