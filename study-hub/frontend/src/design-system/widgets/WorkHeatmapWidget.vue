<template>
  <DashboardModuleCard data-figma-node="349:169" title="工作热力" :loading="viewMode === 'heatmap' && loading" :error="viewMode === 'heatmap' ? error : ''" :empty="viewMode === 'heatmap' && !cells.length && !loading && !error" empty-text="还没有工作记录">
    <div class="heatmap-widget">
      <div class="heatmap-widget__head"><RouterLink :to="{path:'/heatmap',query:{view:viewMode}}"><h2>工作热力</h2></RouterLink><div class="switch"><button :aria-selected="viewMode==='heatmap'" @click="$emit('update:viewMode','heatmap')">热力图</button><button :aria-selected="viewMode==='taskboard'" @click="$emit('update:viewMode','taskboard')">任务版</button></div></div>
      <div v-if="viewMode === 'heatmap'" class="heatmap-widget__grid" aria-label="近期工作热力" :style="gridStyle">
        <i v-for="(cell, index) in visibleCells" :key="cell.id ?? index" data-heatmap-cell :data-level="cell.level ?? 0" />
      </div>
      <div v-if="viewMode === 'taskboard'" class="taskboard"><strong>Codex Taskboard</strong><span>study-hub 项目任务版</span><RouterLink to="/heatmap?view=taskboard">打开完整任务版</RouterLink></div><p v-else>{{ caption }}</p>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed } from 'vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ cells: { type: Array, default: () => [] }, caption: { type: String, default: '正在读取统一热力数据' }, loading: Boolean, error: { type: String, default: '' }, viewMode: { type: String, default: 'heatmap' }, settings: { type: Object, default: () => ({}) } })
defineEmits(['update:viewMode'])
const visibleCells = computed(() => props.cells.slice(0, 196))
const gridStyle = computed(() => ({ gap: `${props.settings.cell_gap ?? 5}px`, '--radius': props.settings.cell_shape === 'rounded' ? `${props.settings.cell_radius || 0}px` : '0', opacity: (props.settings.cell_opacity ?? 100) / 100 }))
</script>

<style scoped>
.heatmap-widget { height: 100%; box-sizing: border-box; padding: 20px 23px; }.heatmap-widget__head{display:flex;justify-content:space-between;align-items:center}.heatmap-widget__head a{color:inherit;text-decoration:none}
h2 { margin: 0; font-size: 18px; }
.heatmap-widget__grid { display: grid; grid-template-columns: repeat(28, 17px); grid-auto-rows: 17px; gap: 5px; margin: 38px 6px 0; }
.heatmap-widget__grid i { border-radius: var(--radius); background: #292e29; }
.heatmap-widget__grid i[data-level='1'] { background: #d7ff63; }
.heatmap-widget__grid i[data-level='2'] { background: #ff7d56; }
.heatmap-widget__grid i[data-level='3'] { background: #8b73ff; }
.heatmap-widget__grid i[data-level='4'] { background: #bfff56; }
.heatmap-widget__grid i[data-level='5'] { background: #ff8f69; }
p { position: absolute; bottom: 18px; left: 23px; margin: 0; color: #6f7770; font-size: 11px; }
.switch{display:flex;gap:2px}.switch button[aria-selected='true']{background:#d7ff63;color:#11140f}.taskboard{display:grid;gap:8px;padding-top:35px}.taskboard span{color:#8b9186;font-size:12px}.taskboard a{color:#d7ff63;font-size:12px}
</style>
