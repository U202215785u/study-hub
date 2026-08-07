<template>
  <UiButton
    size="xs"
    shape="pill"
    :variant="active || tone === 'action' ? 'primary' : 'secondary'"
    :disabled="disabled"
    :aria-pressed="active ? 'true' : 'false'"
    @click="emit('click', $event)"
  >
    <slot />
  </UiButton>
</template>

<script setup>
import UiButton from './UiButton.vue'

defineProps({
  active: Boolean,
  disabled: Boolean,
  tone: {
    type: String,
    default: 'neutral',
    validator: (value) => ['neutral', 'action'].includes(value),
  },
})

const emit = defineEmits(['click'])
</script>
