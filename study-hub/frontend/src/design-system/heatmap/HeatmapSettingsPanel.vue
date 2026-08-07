<template>
  <section class="heatmap-settings" aria-labelledby="heatmap-settings-title">
    <div class="heatmap-settings__heading">
      <div>
        <h2 id="heatmap-settings-title">方格设置</h2>
        <p>调整显示范围、来源和方格外观。</p>
      </div>
      <span v-if="dirty" class="heatmap-settings__dirty">有未保存调整</span>
    </div>

    <div v-if="schema" class="heatmap-settings__fields">
      <div v-for="field in schema.fields" :key="field.key" class="heatmap-settings__field" :data-setting-key="field.key">
        <label v-if="field.type !== 'boolean' && field.type !== 'multiselect'" :for="`heatmap-setting-${field.key}`">{{ labels[field.key] || field.key }}</label>
        <template v-if="field.type === 'select'">
          <select :id="`heatmap-setting-${field.key}`" :value="settings[field.key]" :disabled="isDisabled(field)" @change="updateField(field, $event.target.value)">
            <option v-for="option in field.options" :key="String(option)" :value="option">{{ optionLabels[field.key]?.[option] || option }}</option>
          </select>
        </template>
        <template v-else-if="field.type === 'number'">
          <div class="heatmap-settings__range">
            <input :id="`heatmap-setting-${field.key}`" type="range" :min="field.min" :max="field.max" :step="field.step" :value="settings[field.key]" :disabled="isDisabled(field)" @input="updateField(field, $event.target.value)">
            <output>{{ settings[field.key] }}</output>
          </div>
        </template>
        <template v-else-if="field.type === 'boolean'">
          <label class="heatmap-settings__check">
            <input type="checkbox" :checked="settings[field.key]" @change="updateField(field, $event.target.checked)">
            <span>{{ labels[field.key] || field.key }}</span>
          </label>
        </template>
        <template v-else-if="field.type === 'multiselect'">
          <fieldset>
            <legend>{{ labels[field.key] || field.key }}</legend>
            <label v-for="option in field.options" :key="option" class="heatmap-settings__check">
              <input type="checkbox" :checked="settings[field.key]?.includes(option)" @change="toggleSource(option)">
              <span>{{ optionLabels[field.key]?.[option] || option }}</span>
            </label>
          </fieldset>
        </template>
        <small v-if="field.key === 'cell_radius'">方格形状下会自动归零。</small>
      </div>
    </div>

    <footer class="heatmap-settings__actions">
      <UiButton size="sm" variant="secondary" :loading="saving" :disabled="!dirty" @click="$emit('save')">保存设置</UiButton>
      <UiButton size="sm" variant="quiet" :disabled="!dirty" @click="$emit('apply')">应用预览</UiButton>
      <UiButton size="sm" variant="text" @click="$emit('reset')">恢复默认</UiButton>
    </footer>
  </section>
</template>

<script setup>
import UiButton from '../components/general/UiButton.vue'

const props = defineProps({
  schema: { type: Object, default: null },
  settings: { type: Object, default: () => ({}) },
  dirty: Boolean,
  saving: Boolean,
})
const emit = defineEmits(['update:settings', 'apply', 'save', 'reset'])

const labels = {
  range_days: '数据范围', sources: '数据来源', palette: '调色板', scale: '强度映射', cell_shape: '方格形状',
  cell_gap: '方格间距', cell_radius: '圆角', cell_opacity: '透明度', show_legend: '显示图例', show_date_labels: '显示日期', week_starts_on: '每周起始日',
}
const optionLabels = {
  range_days: { 90: '近 90 天', 196: '近 196 天', 365: '近 365 天' },
  sources: { tasks: 'DDL 任务记录', documents: '知识库文档', queue: '自动化队列' },
  cell_shape: { square: '方格', rounded: '圆角' },
  week_starts_on: { 0: '周日', 1: '周一' },
}

function isDisabled(field) {
  return field.depends_on && props.settings[field.depends_on.key] !== field.depends_on.equals
}

function updateField(field, value) {
  let next = value
  if (field.type === 'number' || (field.type === 'select' && field.options?.every((option) => typeof option === 'number'))) next = Number(value)
  const settings = { ...props.settings, [field.key]: next }
  if (field.key === 'cell_shape' && next === 'square') settings.cell_radius = 0
  emit('update:settings', settings)
}

function toggleSource(source) {
  const current = props.settings.sources || []
  const sources = current.includes(source) ? current.filter((item) => item !== source) : [...current, source]
  emit('update:settings', { ...props.settings, sources: sources.length ? sources : current })
}
</script>

<style scoped>
.heatmap-settings { display: grid; gap: 16px; }
.heatmap-settings__heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.heatmap-settings h2 { margin: 0; font-size: 16px; }
.heatmap-settings p, .heatmap-settings small { margin: 4px 0 0; color: var(--ui-color-text-muted); font-size: 11px; line-height: 1.5; }
.heatmap-settings__dirty { color: var(--ui-color-action); font-size: 11px; white-space: nowrap; }
.heatmap-settings__fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 16px; }
.heatmap-settings__field { display: grid; gap: 7px; min-width: 0; }
.heatmap-settings__field > label, .heatmap-settings legend { color: var(--ui-color-text-strong); font-size: 12px; font-weight: 700; }
.heatmap-settings select { width: 100%; min-height: 38px; border: 1px solid var(--ui-color-border-strong); border-radius: 8px; padding: 0 10px; background: var(--ui-color-surface); color: var(--ui-color-text-strong); }
.heatmap-settings select:disabled { opacity: .5; }
.heatmap-settings__range { display: flex; align-items: center; gap: 10px; }
.heatmap-settings__range input { min-width: 0; flex: 1; accent-color: var(--ui-color-action); }
.heatmap-settings output { width: 32px; color: var(--ui-color-text-muted); font-size: 12px; text-align: right; }
.heatmap-settings fieldset { display: flex; flex-wrap: wrap; gap: 8px 12px; border: 0; margin: 0; padding: 0; }
.heatmap-settings__check { display: inline-flex; align-items: center; gap: 6px; color: var(--ui-color-text); font-size: 12px; font-weight: 400; }
.heatmap-settings__check input { accent-color: var(--ui-color-action); }
.heatmap-settings__actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
@media (max-width: 640px) { .heatmap-settings__fields { grid-template-columns: 1fr; } .heatmap-settings__actions { justify-content: flex-start; } }
</style>
