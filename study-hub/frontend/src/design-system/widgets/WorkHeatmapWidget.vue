<template>
  <DashboardModuleCard data-figma-node="349:169" title="工作热力" :loading="viewMode === 'heatmap' && loading" :error="viewMode === 'heatmap' ? error : ''" :empty="viewMode === 'heatmap' && !cells.length && !loading && !error" empty-text="还没有工作记录">
    <div class="heatmap-widget" :data-view-mode="viewMode">
      <UiCompactHeader title="工作热力" :to="detailTo" target="_self" size="md">
        <template #action>
          <div class="heatmap-widget__switcher" role="tablist" aria-label="工作模块视图">
            <button type="button" data-view-switch="heatmap" :aria-selected="viewMode === 'heatmap'" @click="emit('update:viewMode', 'heatmap')">热力图</button>
            <button type="button" data-view-switch="taskboard" :aria-selected="viewMode === 'taskboard'" @click="emit('update:viewMode', 'taskboard')">任务版</button>
          </div>
        </template>
      </UiCompactHeader>
      <div v-if="viewMode === 'heatmap'" class="heatmap-widget__content">
        <div class="heatmap-widget__grid" role="img" aria-label="近期工作热力" :style="gridStyle">
          <i v-for="(cell, index) in visibleCells" :key="cell.id ?? index" data-heatmap-cell :data-level="cell.level ?? 0" />
        </div>
        <p>{{ caption }}</p>
      </div>
      <TaskboardEmbed v-else compact />
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
import TaskboardEmbed from '../heatmap/TaskboardEmbed.vue'

const props = defineProps({
  cells: { type: Array, default: () => [] },
  caption: { type: String, default: '近 7 天高峰：21:00 - 23:00' },
  loading: Boolean,
  error: { type: String, default: '' },
  viewMode: { type: String, default: 'heatmap', validator: (value) => ['heatmap', 'taskboard'].includes(value) },
  settings: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:viewMode'])
const visibleCells = computed(() => props.cells.slice(0, 196))
const detailTo = computed(() => ({ path: '/heatmap', query: { view: props.viewMode } }))
const gridStyle = computed(() => ({
  gap: `${props.settings.cell_gap ?? 5}px`,
  '--heatmap-opacity': (props.settings.cell_opacity ?? 100) / 100,
  '--heatmap-radius': props.settings.cell_shape === 'rounded' ? `${props.settings.cell_radius || 0}px` : '0px',
}))
</script>

<style scoped>
.heatmap-widget { display: grid; height: 100%; min-height: 0; box-sizing: border-box; grid-template-rows: auto minmax(0, 1fr) auto; }
.heatmap-widget__content { display: grid; min-height: 0; grid-template-rows: minmax(0, 1fr) auto; gap: 8px; }
.heatmap-widget__grid { display: grid; width: 100%; max-height: 149px; align-self: center; aspect-ratio: 4.1; grid-template-columns: repeat(28, minmax(0, 1fr)); grid-template-rows: repeat(7, minmax(0, 1fr)); }
.heatmap-widget__grid i { border-radius: var(--heatmap-radius, 0px); background: #292e29; opacity: var(--heatmap-opacity, 1); }
.heatmap-widget__grid i[data-level='1'] { background: #d7ff63; }
.heatmap-widget__grid i[data-level='2'] { background: #ff7d56; }
.heatmap-widget__grid i[data-level='3'] { background: #8b73ff; }
.heatmap-widget__grid i[data-level='4'] { background: #bfff56; }
.heatmap-widget__grid i[data-level='5'] { background: #ff8f69; }
.heatmap-widget p { margin: 0; color: #6f7770; font-size: 11px; }
.heatmap-widget__switcher { display: inline-flex; gap: 2px; border: 1px solid rgb(245 246 238 / 12%); border-radius: 7px; padding: 2px; background: rgb(0 0 0 / 18%); }
.heatmap-widget__switcher button { border: 0; border-radius: 5px; padding: 5px 7px; background: transparent; color: #8b9186; font: 700 10px/1 var(--ui-font-sans); cursor: pointer; }
.heatmap-widget__switcher button[aria-selected='true'] { background: #d7ff63; color: #11140f; }
</style>
