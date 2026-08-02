<template>
  <header class="ui-panel-header">
    <div class="ui-panel-header__copy">
      <div class="ui-panel-header__title-row">
        <h2 class="ui-panel-header__title">{{ title }}</h2>
        <span v-if="meta" class="ui-panel-header__meta">{{ meta }}</span>
      </div>
      <p v-if="description" class="ui-panel-header__description">{{ description }}</p>
    </div>
    <div class="ui-panel-header__actions"><slot name="actions" /></div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  meta: { type: [String, Number], default: '' },
  description: { type: String, default: '' },
})
</script>

<style scoped>
.ui-panel-header { display: flex; min-height: 40px; align-items: flex-start; justify-content: space-between; gap: var(--ui-space-4); }
.ui-panel-header__copy { display: grid; min-width: 0; gap: var(--ui-space-1); }
.ui-panel-header__title-row { display: flex; min-width: 0; align-items: center; gap: var(--ui-space-2); }
.ui-panel-header__title { min-width: 0; margin: 0; overflow: hidden; color: var(--ui-color-text-strong); font: 700 15px/1.35 var(--ui-font-sans); text-overflow: ellipsis; white-space: nowrap; }
.ui-panel-header__meta { flex: 0 0 auto; color: var(--ui-color-text-muted); font: 600 12px/1.3 var(--ui-font-sans); }
.ui-panel-header__description { margin: 0; color: var(--ui-color-text-muted); font-size: 12px; line-height: 1.4; }
.ui-panel-header__actions { display: flex; min-width: 40px; min-height: 40px; flex: 0 0 auto; align-items: flex-start; justify-content: flex-end; gap: var(--ui-space-2); }
</style>
