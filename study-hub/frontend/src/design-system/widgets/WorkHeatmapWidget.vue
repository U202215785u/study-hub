<template>
  <DashboardModuleCard data-figma-node="349:169" title="工作热力" :loading="loading" :error="error" :empty="!cells.length && !loading && !error" empty-text="还没有工作记录">
    <div class="heatmap-widget">
      <h2>工作热力</h2>
      <div class="heatmap-widget__grid" aria-label="近期工作热力">
        <i v-for="(cell, index) in visibleCells" :key="cell.id ?? index" data-heatmap-cell :data-level="cell.level ?? 0" />
      </div>
      <p>{{ caption }}</p>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed } from 'vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ cells: { type: Array, default: () => [] }, caption: { type: String, default: '近 7 天高峰：21:00 - 23:00' }, loading: Boolean, error: { type: String, default: '' } })
const visibleCells = computed(() => props.cells.slice(0, 196))
</script>

<style scoped>
.heatmap-widget { height: 100%; box-sizing: border-box; padding: 20px 23px; }
h2 { margin: 0; font-size: 18px; }
.heatmap-widget__grid { display: grid; grid-template-columns: repeat(28, 17px); grid-auto-rows: 17px; gap: 5px; margin: 38px 6px 0; }
.heatmap-widget__grid i { border-radius: 5px; background: #292e29; }
.heatmap-widget__grid i[data-level='1'] { background: #d7ff63; }
.heatmap-widget__grid i[data-level='2'] { background: #ff7d56; }
.heatmap-widget__grid i[data-level='3'] { background: #8b73ff; }
.heatmap-widget__grid i[data-level='4'] { background: #bfff56; }
.heatmap-widget__grid i[data-level='5'] { background: #ff8f69; }
p { position: absolute; bottom: 18px; left: 23px; margin: 0; color: #6f7770; font-size: 11px; }
</style>
