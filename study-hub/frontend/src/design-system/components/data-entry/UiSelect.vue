<template>
  <div class="ui-field">
    <label v-if="label" class="ui-field__label" :for="selectId">
      <span>{{ label }}</span>
      <span v-if="required" class="ui-field__required" aria-hidden="true">*</span>
    </label>
    <p v-if="description && !error" :id="descriptionId" class="ui-field__description">{{ description }}</p>
    <span class="ui-select-wrap">
      <select
        :id="selectId"
        class="ui-select"
        :class="{ 'ui-select--error': Boolean(error) }"
        :value="modelValue"
        :disabled="disabled"
        :required="required"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        @change="onChange"
        @focus="$emit('focus', $event)"
        @blur="$emit('blur', $event)"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option v-for="option in options" :key="option.value" :value="option.value" :disabled="option.disabled">
          {{ option.label }}
        </option>
      </select>
      <span class="ui-select-wrap__chevron" aria-hidden="true">⌄</span>
    </span>
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
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  id: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'focus', 'blur'])
const selectId = computed(() => props.id || `ui-select-${++nextId}`)
const descriptionId = computed(() => `${selectId.value}-description`)
const errorId = computed(() => `${selectId.value}-error`)
const describedBy = computed(() => props.error ? errorId.value : (props.description ? descriptionId.value : undefined))

function onChange(event) {
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
.ui-select-wrap { position: relative; display: block; }
.ui-select { appearance: none; width: 100%; min-height: 40px; box-sizing: border-box; border: 1px solid var(--ui-color-border-strong); border-radius: var(--ui-radius-md); padding: 0 var(--ui-space-8) 0 var(--ui-space-3); background: var(--ui-color-surface); color: var(--ui-color-text-strong); font: 400 14px/1.4 var(--ui-font-sans); }
.ui-select:focus { outline: none; border-color: var(--ui-color-action); box-shadow: var(--ui-focus-ring); }
.ui-select:hover:not(:disabled) { border-color: var(--ui-color-text-muted); }
.ui-select--error { border-color: var(--ui-color-danger); }
.ui-select:disabled { color: var(--ui-color-text-disabled); background: var(--ui-color-surface-muted); cursor: not-allowed; opacity: .7; }
.ui-select-wrap__chevron { position: absolute; top: 50%; right: var(--ui-space-3); transform: translateY(-58%); color: var(--ui-color-text-muted); pointer-events: none; font-size: 17px; }
</style>
