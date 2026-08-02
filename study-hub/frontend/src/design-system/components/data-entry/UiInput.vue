<template>
  <div class="ui-field">
    <label v-if="label" class="ui-field__label" :for="inputId">
      <span>{{ label }}</span>
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>
    <p v-if="description && !error" :id="descriptionId" class="ui-field__description">{{ description }}</p>
    <input
      :id="inputId"
      class="ui-input"
      :class="{ 'ui-input--error': Boolean(error) }"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="describedBy"
      @input="onInput"
      @focus="$emit('focus', $event)"
      @blur="$emit('blur', $event)"
    >
    <p v-if="error" :id="errorId" class="ui-field__error" role="alert">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

let nextId = 0
const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  error: { type: String, default: '' },
  disabled: Boolean,
  required: Boolean,
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  id: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'focus', 'blur'])
const inputId = computed(() => props.id || `ui-input-${++nextId}`)
const descriptionId = computed(() => `${inputId.value}-description`)
const errorId = computed(() => `${inputId.value}-error`)
const describedBy = computed(() => props.error ? errorId.value : (props.description ? descriptionId.value : undefined))

function onInput(event) {
  emit('update:modelValue', event.target.value)
}
</script>

<style scoped>
.ui-field { display: grid; gap: var(--ui-space-2); min-width: 0; }
.ui-field__label { display: inline-flex; gap: var(--ui-space-1); color: var(--ui-color-text-strong); font: 700 13px/1.3 var(--ui-font-sans); }
.ui-field__required { color: var(--ui-color-danger); }
.ui-field__description, .ui-field__error { margin: 0; font-size: 12px; line-height: 1.4; }
.ui-field__description { color: var(--ui-color-text-muted); }
.ui-field__error { color: var(--ui-color-danger); }
.ui-input {
  width: 100%; min-height: 40px; box-sizing: border-box; border: 1px solid var(--ui-color-border-strong);
  border-radius: var(--ui-radius-md); padding: 0 var(--ui-space-3); background: var(--ui-color-surface);
  color: var(--ui-color-text-strong); font: 400 14px/1.4 var(--ui-font-sans); transition: border-color var(--ui-duration-fast) var(--ui-ease-standard), box-shadow var(--ui-duration-fast) var(--ui-ease-standard);
}
.ui-input::placeholder { color: var(--ui-color-text-muted); }
.ui-input:hover:not(:disabled) { border-color: var(--ui-color-text-muted); }
.ui-input:focus { outline: none; border-color: var(--ui-color-action); box-shadow: var(--ui-focus-ring); }
.ui-input--error { border-color: var(--ui-color-danger); }
.ui-input:disabled { color: var(--ui-color-text-disabled); background: var(--ui-color-surface-muted); cursor: not-allowed; opacity: .7; }
</style>
