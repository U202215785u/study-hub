<template>
  <button
    class="ui-button"
    :class="{ 'ui-button--block': block }"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading ? 'true' : undefined"
    :data-variant="variant"
    :data-size="size"
    :data-block="block ? 'true' : undefined"
    @click="onClick"
  >
    <span v-if="loading" class="ui-button__spinner" aria-hidden="true" />
    <span v-else-if="$slots.prefix" class="ui-button__icon" aria-hidden="true">
      <slot name="prefix" />
    </span>
    <span class="ui-button__label"><slot /></span>
    <span v-if="$slots.suffix" class="ui-button__icon" aria-hidden="true">
      <slot name="suffix" />
    </span>
  </button>
</template>

<script setup>
const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'quiet', 'text', 'danger'].includes(value),
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value),
  },
  type: {
    type: String,
    default: 'button',
    validator: (value) => ['button', 'submit', 'reset'].includes(value),
  },
  loading: Boolean,
  disabled: Boolean,
  block: Boolean,
})

const emit = defineEmits(['click'])

function onClick(event) {
  if (props.loading || props.disabled) return
  emit('click', event)
}
</script>

<style scoped>
.ui-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ui-space-2);
  max-width: 100%;
  border: 1px solid transparent;
  border-radius: var(--ui-radius-md);
  font: 700 14px/1 var(--ui-font-sans);
  letter-spacing: 0;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color var(--ui-duration-fast) var(--ui-ease-standard),
    border-color var(--ui-duration-fast) var(--ui-ease-standard),
    color var(--ui-duration-fast) var(--ui-ease-standard),
    transform var(--ui-duration-fast) var(--ui-ease-standard);
}

.ui-button[data-size='sm'] {
  min-height: 32px;
  padding: 0 var(--ui-space-3);
  font-size: 12px;
}

.ui-button[data-size='md'] {
  min-height: 40px;
  padding: 0 var(--ui-space-4);
}

.ui-button[data-size='lg'] {
  min-height: 48px;
  padding: 0 var(--ui-space-5);
  font-size: 15px;
}

.ui-button[data-variant='primary'] {
  background: var(--ui-color-action);
  color: var(--ui-color-action-text);
}

.ui-button[data-variant='primary']:hover:not(:disabled) {
  background: var(--ui-color-action-hover);
}

.ui-button[data-variant='primary']:active:not(:disabled) {
  background: var(--ui-color-action-pressed);
}

.ui-button[data-variant='secondary'] {
  background: var(--ui-color-surface);
  border-color: var(--ui-color-border-strong);
  color: var(--ui-color-text-strong);
}

.ui-button[data-variant='secondary']:hover:not(:disabled),
.ui-button[data-variant='quiet']:hover:not(:disabled) {
  background: var(--ui-color-surface-raised);
  border-color: var(--ui-color-border-strong);
}

.ui-button[data-variant='quiet'] {
  background: var(--ui-color-surface-raised);
  color: var(--ui-color-text);
}

.ui-button[data-variant='text'] {
  background: transparent;
  color: var(--ui-color-text-muted);
}

.ui-button[data-variant='text']:hover:not(:disabled) {
  color: var(--ui-color-text-strong);
}

.ui-button[data-variant='danger'] {
  background: color-mix(in srgb, var(--ui-color-danger) 16%, transparent);
  border-color: color-mix(in srgb, var(--ui-color-danger) 44%, transparent);
  color: var(--ui-color-danger);
}

.ui-button[data-variant='danger']:hover:not(:disabled) {
  background: var(--ui-color-danger);
  color: var(--ui-color-canvas);
}

.ui-button:active:not(:disabled) {
  transform: translateY(1px);
}

.ui-button:focus-visible {
  outline: none;
  box-shadow: var(--ui-focus-ring);
}

.ui-button:disabled {
  color: var(--ui-color-text-disabled);
  cursor: not-allowed;
  opacity: 0.58;
  transform: none;
}

.ui-button--block {
  width: 100%;
}

.ui-button__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ui-button__icon,
.ui-button__spinner {
  display: inline-flex;
  flex: 0 0 auto;
  width: 1em;
  height: 1em;
  align-items: center;
  justify-content: center;
}

.ui-button__spinner {
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: ui-button-spin 700ms linear infinite;
}

@keyframes ui-button-spin {
  to { transform: rotate(360deg); }
}
</style>
