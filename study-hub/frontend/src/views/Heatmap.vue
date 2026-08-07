<template>
  <main class="heatmap-page">
    <header class="heatmap-page__header">
      <RouterLink to="/">返回首页</RouterLink>
      <div class="heatmap-page__title">
        <p>STUDY-HUB ACTIVITY</p>
        <h1>工作热力</h1>
        <span>观察学习记录，再切换到 Codex Taskboard 执行议题。</span>
      </div>
      <nav aria-label="热力图视图">
        <button :aria-selected="view === 'heatmap'" @click="setView('heatmap')">热力图</button>
        <button :aria-selected="view === 'taskboard'" @click="setView('taskboard')">任务版</button>
      </nav>
    </header>

    <TaskboardEmbed v-if="view === 'taskboard'" />

    <template v-else>
      <p v-if="error" class="heatmap-page__error">{{ error }}</p>
      <div v-else-if="loading">正在加载热力图…</div>
      <template v-else>
        <section class="styles" aria-label="热力图样式">
          <button
            v-for="style in catalog?.styles"
            :key="style.id"
            :disabled="style.status !== 'available'"
            :aria-selected="style.id === styleId"
          >
            {{ style.name }}
            <small>{{ style.status === 'available' ? '可用' : '即将支持' }}</small>
          </button>
        </section>

        <section class="workspace">
          <div>
            <h2>方格预览</h2>
            <component :is="renderer" v-if="renderer" :data="data || {}" :settings="settings" />
          </div>

          <form @submit.prevent="save">
            <h2>方格设置</h2>
            <label
              v-for="field in schema?.fields"
              :key="field.key"
              :class="{ disabled: isDisabled(field) }"
            >
              <span>{{ fieldLabel(field.key) }}</span>
              <select
                v-if="field.type === 'select'"
                :value="settings[field.key]"
                :disabled="isDisabled(field)"
                @change="heatmap.update({ [field.key]: coerce(field, $event.target.value) })"
              >
                <option v-for="value in field.options" :key="value" :value="value">{{ optionLabel(field.key, value) }}</option>
              </select>
              <span v-else-if="field.type === 'number'" class="range-control">
                <input
                  type="range"
                  :min="field.min"
                  :max="field.max"
                  :step="field.step"
                  :value="settings[field.key]"
                  :disabled="isDisabled(field)"
                  @input="heatmap.update({ [field.key]: Number($event.target.value) })"
                >
                <output>{{ settings[field.key] }}</output>
              </span>
              <input
                v-else-if="field.type === 'boolean'"
                type="checkbox"
                :checked="settings[field.key]"
                @change="heatmap.update({ [field.key]: $event.target.checked })"
              >
              <span v-else-if="field.type === 'multiselect'" class="source-options">
                <label v-for="value in field.options" :key="value">
                  <input type="checkbox" :checked="settings[field.key]?.includes(value)" @change="toggleSource(value)">
                  {{ optionLabel(field.key, value) }}
                </label>
              </span>
            </label>
            <footer>
              <button type="button" @click="apply">应用预览</button>
              <button :disabled="!dirty || saving">保存设置</button>
              <button type="button" @click="heatmap.reset">恢复默认</button>
            </footer>
          </form>
        </section>
      </template>
    </template>
  </main>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore } from '../stores/settings.js'
import { useHeatmap } from '../composables/heatmap/useHeatmap.js'
import { getHeatmapRenderer } from '../design-system/heatmap/heatmapRenderers.js'
import TaskboardEmbed from '../design-system/heatmap/TaskboardEmbed.vue'

const fieldLabels = {
  range_days: '显示范围', sources: '数据来源', palette: '配色方案', scale: '统计刻度',
  cell_shape: '方格形状', cell_gap: '方格间距', cell_radius: '圆角大小', cell_opacity: '方格透明度',
  show_legend: '显示图例', show_date_labels: '显示日期标记', week_starts_on: '每周起始日',
}
const optionLabels = {
  tasks: '任务记录', documents: '知识文档', queue: '自动化队列',
  'lime-orange-purple': '青柠、橙色、紫色', threshold: '按记录数分级',
  square: '直角方格', rounded: '圆角方格', 0: '周日', 1: '周一',
}

const route = useRoute()
const router = useRouter()
const store = useSettingsStore()
const heatmap = useHeatmap({ apiGet: store.apiGet, apiPut: store.apiPut })
const { catalog, data, styleId, settings, schema, error, loading, saving, dirty } = heatmap
const view = computed(() => route.query.view === 'taskboard' ? 'taskboard' : 'heatmap')
const renderer = computed(() => getHeatmapRenderer(styleId.value))

function setView(value) {
  router.replace({ query: { ...route.query, view: value } })
}
function isDisabled(field) {
  return Boolean(field.depends_on && heatmap.settings.value[field.depends_on.key] !== field.depends_on.equals)
}
function fieldLabel(key) {
  return fieldLabels[key] || key
}
function optionLabel(key, value) {
  if (key === 'range_days') return `最近 ${value} 天`
  return optionLabels[value] || value
}
function coerce(field, value) {
  return field.options.every((item) => typeof item === 'number') ? Number(value) : value
}
function toggleSource(value) {
  const sources = heatmap.settings.value.sources || []
  if (sources.includes(value)) {
    if (sources.length === 1) return
    heatmap.update({ sources: sources.filter((item) => item !== value) })
    return
  }
  heatmap.update({ sources: [...sources, value] })
}
async function apply() {
  await heatmap.apply()
}
async function save() {
  await heatmap.save()
  await heatmap.apply()
}

onMounted(() => heatmap.load())
</script>

<style scoped>
.heatmap-page { padding: 32px; display: grid; gap: 24px; }
.heatmap-page__header { display: flex; gap: 24px; align-items: start; border-bottom: 1px solid #3a4038; padding-bottom: 20px; }
.heatmap-page__title { flex: 1; }.heatmap-page p { color: #d7ff63; font-size: 11px; }.heatmap-page h1 { margin: 0; }.heatmap-page span { color: #8b9186; }
.heatmap-page__error { color: #ff6b78; }.styles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }.styles button { display: grid; text-align: left; padding: 14px; }.styles small { color: #8b9186; }
.workspace { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(280px, .8fr); gap: 28px; }.workspace form { display: grid; gap: 12px; }.workspace form > label { display: grid; gap: 5px; }.workspace label.disabled { opacity: .5; }.workspace footer { display: flex; gap: 8px; }.range-control { display: flex; gap: 8px; align-items: center; }.source-options { display: flex; flex-wrap: wrap; gap: 8px; }.source-options label { display: flex; gap: 4px; align-items: center; }
@media (max-width: 800px) { .workspace { grid-template-columns: 1fr; }.styles { grid-template-columns: repeat(2, 1fr); }.heatmap-page__header { flex-wrap: wrap; } }
</style>
