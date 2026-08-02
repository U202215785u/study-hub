<template>
  <section class="ui-empty" :aria-label="title">
    <div v-if="$slots.icon" class="ui-empty__icon" aria-hidden="true"><slot name="icon" /></div>
    <div v-else class="ui-empty__icon ui-empty__icon--default" aria-hidden="true">∅</div>
    <h3 class="ui-empty__title">{{ title }}</h3>
    <p v-if="description" class="ui-empty__description">{{ description }}</p>
    <div v-if="$slots.action" class="ui-empty__action"><slot name="action" /></div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无内容' },
  description: { type: String, default: '' },
})
</script>

<style scoped>
.ui-empty { display: grid; justify-items: center; gap: var(--ui-space-2); padding: var(--ui-space-8) var(--ui-space-4); text-align: center; color: var(--ui-color-text-muted); }
.ui-empty__icon { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 50%; background: var(--ui-color-surface-raised); color: var(--ui-color-text-muted); font-size: 26px; }
.ui-empty__title { margin: 0; color: var(--ui-color-text-strong); font-size: 15px; line-height: 1.4; }
.ui-empty__description { max-width: 32rem; margin: 0; font-size: 13px; line-height: 1.5; }
.ui-empty__action { margin-top: var(--ui-space-2); }
</style>
