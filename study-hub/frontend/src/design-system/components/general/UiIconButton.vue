<template>
  <UiButton
    class="ui-icon-button"
    :variant="variant"
    :size="size"
    :type="type"
    :loading="loading"
    :disabled="disabled"
    :aria-label="label"
    :title="label"
    @click="emit('click', $event)"
  >
    <slot />
  </UiButton>
</template>

<script setup>
import UiButton from './UiButton.vue'

const props = defineProps({
  label: { type: String, default: '' },
  variant: { type: String, default: 'quiet' },
  size: { type: String, default: 'md' },
  type: { type: String, default: 'button' },
  loading: Boolean,
  disabled: Boolean,
})

if (!props.label.trim()) {
  throw new Error('UiIconButton requires a label')
}

const emit = defineEmits(['click'])
</script>

<style scoped>
.ui-icon-button {
  aspect-ratio: 1;
  padding: 0;
}

.ui-icon-button[data-size='sm'] { width: 32px; }
.ui-icon-button[data-size='md'] { width: 40px; }
.ui-icon-button[data-size='lg'] { width: 48px; }

.ui-icon-button :deep(.ui-button__label) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}
</style>
