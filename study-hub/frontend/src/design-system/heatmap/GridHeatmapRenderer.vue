<template>
  <section class="grid-heatmap">
    <div class="grid" :style="gridStyle">
      <template v-for="slot in slots" :key="slot.key">
        <span v-if="slot.cell" class="cell" :data-level="slot.cell.level" :title="title(slot.cell)" :style="cellStyle" />
        <span v-else class="empty" />
      </template>
    </div>
    <div v-if="settings.show_date_labels" class="date-labels" aria-label="日期标记">
      <span v-for="cell in labelCells" :key="cell.date" data-heatmap-date-label>{{ cell.date.slice(5) }}</span>
    </div>
    <div v-if="settings.show_legend" class="legend">少 <i v-for="n in 5" :key="n" :data-level="n" /> 多</div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Object, default: () => ({}) }, settings: { type: Object, default: () => ({}) } })
const grid = computed(() => props.data.grid || { rows: 7, columns: 28, slot_count: 196, leading_empty_slots: 0 })
const slots = computed(() => Array.from({ length: grid.value.slot_count }, (_, index) => ({ key: index, cell: props.data.cells?.[index - grid.value.leading_empty_slots] || null })))
const labelCells = computed(() => (props.data.cells || []).filter((_, index) => index % 7 === 0))
const gridStyle = computed(() => ({ gridTemplateColumns: `repeat(${grid.value.columns}, minmax(0, 1fr))`, gap: `${props.settings.cell_gap ?? 5}px`, opacity: (props.settings.cell_opacity ?? 100) / 100 }))
const cellStyle = computed(() => ({ borderRadius: props.settings.cell_shape === 'rounded' ? `${props.settings.cell_radius || 0}px` : '0' }))
const title = (cell) => `${cell.date} · ${cell.count} 条记录 · ${Object.entries(cell.source_counts || {}).map(([source, count]) => `${source}: ${count}`).join('，')}`
</script>

<style scoped>
.grid { display: grid; }
.cell, .empty { display: block; aspect-ratio: 1; background: #292e29; }
.cell[data-level='1'] { background: #d7ff63; }.cell[data-level='2'] { background: #ff7d56; }.cell[data-level='3'] { background: #8b73ff; }.cell[data-level='4'] { background: #bfff56; }.cell[data-level='5'] { background: #ff8f69; }
.date-labels { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; font-size: 11px; color: #8b9186; }
.legend { display: flex; gap: 5px; align-items: center; margin-top: 12px; font-size: 12px; color: #8b9186; }
.legend i { width: 12px; height: 12px; background: #292e29; }.legend i[data-level='1'] { background: #d7ff63; }.legend i[data-level='2'] { background: #ff7d56; }.legend i[data-level='3'] { background: #8b73ff; }.legend i[data-level='4'] { background: #bfff56; }.legend i[data-level='5'] { background: #ff8f69; }
</style>
