<template>
  <header class="ui-compact-header" :data-size="size">
    <RouterLink v-if="to" class="ui-compact-header__link" :to="to" :target="target" :rel="target === '_blank' ? 'noopener noreferrer' : undefined">
      <component :is="`h${level}`" class="ui-compact-header__title">{{ title }}</component>
    </RouterLink>
    <component v-else :is="`h${level}`" class="ui-compact-header__title">{{ title }}</component>
    <slot />
    <span v-if="meta" class="ui-compact-header__meta">{{ meta }}</span>
    <span v-if="$slots.action" class="ui-compact-header__action"><slot name="action" /></span>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  to: { type: [String, Object], default: '' },
  target: { type: String, default: '_blank' },
  meta: { type: String, default: '' },
  level: { type: Number, default: 2, validator: (value) => value >= 2 && value <= 6 },
  size: { type: String, default: 'sm', validator: (value) => ['sm', 'md', 'lg'].includes(value) },
})
</script>

<style scoped>
.ui-compact-header { display: flex; min-width: 0; align-items: center; gap: var(--ui-space-2); }
.ui-compact-header__link { min-width: 0; flex: 1; overflow: hidden; color: inherit; text-decoration: none; }
.ui-compact-header__title { min-width: 0; overflow: hidden; margin: 0; color: var(--ui-color-text-strong); text-overflow: ellipsis; white-space: nowrap; }
.ui-compact-header__link:hover .ui-compact-header__title, .ui-compact-header__link:focus-visible .ui-compact-header__title { color: var(--ui-color-action); text-decoration: underline; text-underline-offset: 3px; }
.ui-compact-header[data-size='sm'] .ui-compact-header__title { font-size: 16px; line-height: 22px; }
.ui-compact-header[data-size='md'] .ui-compact-header__title { font-size: 18px; line-height: 23px; }
.ui-compact-header[data-size='lg'] .ui-compact-header__title { font-size: 20px; line-height: 24px; }
.ui-compact-header__meta { flex: 0 0 auto; color: var(--ui-color-text-muted); font-size: 10px; white-space: nowrap; }
.ui-compact-header__action { display: inline-flex; flex: 0 0 auto; }
</style>
