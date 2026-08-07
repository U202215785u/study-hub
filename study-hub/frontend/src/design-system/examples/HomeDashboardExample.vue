<template>
  <WorkbenchFrame>
    <template #navigation><CapsuleNavigation /></template>
    <template #greeting><GreetingBar /></template>

    <div class="example-dashboard-grid" data-visual-anchor="grid">
      <BentoDashboardGrid>
        <div
          v-for="widget in widgets"
          :key="widget.id"
          class="example-dashboard-grid__item"
          :data-module-id="widget.id"
          :style="widgetStyle(widget)"
        >
          <component :is="registry[widget.id].component" v-bind="propsFor(widget.id)" />
        </div>
      </BentoDashboardGrid>
    </div>

    <template #footer><footer class="example-dashboard-footer"><span>v1.0</span><b>月亮</b></footer></template>
  </WorkbenchFrame>
</template>

<script setup>
import { DEFAULT_DASHBOARD_LAYOUT } from '../layout/dashboardLayout.js'
import { DASHBOARD_REGISTRY } from '../layout/dashboardRegistry.js'
import BentoDashboardGrid from '../patterns/BentoDashboardGrid.vue'
import CapsuleNavigation from '../patterns/CapsuleNavigation.vue'
import GreetingBar from '../patterns/GreetingBar.vue'
import WorkbenchFrame from '../patterns/WorkbenchFrame.vue'

const registry = DASHBOARD_REGISTRY
const widgets = DEFAULT_DASHBOARD_LAYOUT.widgets

const heatmapCells = Array.from({ length: 196 }, (_, index) => ({
  id: index,
  level: [0, 0, 0, 0, 1, 2, 0, 3][index % 8],
}))
const calendarDays = ['2', '3', '4', '5', '6', '7', '8'].map((label, index) => ({
  date: `2026-08-${String(index + 2).padStart(2, '0')}`,
  label,
  selected: label === '3',
}))
const queueItems = [{ id: 'q1', title: 'Codex 自带一套长期记忆系统', status: 'done', progress: 100 }]
const knowledgeItems = [
  { id: 'k1', title: 'Codex 自带一套长期记忆系统 Memories', status: 'ready' },
  { id: 'k2', title: '自媒体人的技能盘点与整理', status: 'ready' },
]
const creationItems = [
  { id: 'c1', title: 'Claude', kind: 'article' },
  { id: 'c2', title: 'ChatGPT', kind: 'article' },
]
const workflowSteps = [
  { id: 'w1', label: '网页输入' },
  { id: 'w2', label: '执行' },
  { id: 'w3', label: '输出' },
]

function widgetStyle(widget) {
  const [columns, rows] = widget.size.split('x').map(Number)
  return { '--widget-columns': columns, '--widget-rows': rows }
}

function propsFor(id) {
  return {
    'work-heatmap': { cells: heatmapCells, caption: '近 7 天：28 次记录' },
    'calendar-agenda': { days: calendarDays, agenda: [], monthLabel: '2026年 8月' },
    'today-focus': { tasks: [], dateLabel: '08月03日' },
    'automation-queue': { items: queueItems },
    knowledge: { items: knowledgeItems },
    'daily-memory': { title: '今日手账' },
    'quick-command': { commands: [{ id: 'a', title: '更新日志' }, { id: 'b', title: '编译Wiki' }] },
    'creation-entry': { items: creationItems },
    'quick-workflow': { steps: workflowSteps },
  }[id] || {}
}
</script>

<style scoped>
.example-dashboard-grid { width: calc(100% + 12px); height: 656px; margin-top: 20px; margin-left: -6px; }
.example-dashboard-grid :deep(.bento-dashboard-grid) { grid-auto-flow: row dense; }
.example-dashboard-grid__item { min-width: 0; min-height: 0; grid-column: span var(--widget-columns); grid-row: span var(--widget-rows); align-self: stretch; }
.example-dashboard-footer { position: absolute; right: 46px; bottom: 0; left: 46px; display: flex; height: 55px; box-sizing: border-box; align-items: center; justify-content: space-between; padding-bottom: 20px; color: var(--ui-color-text-muted); font-size: 12px; }
.example-dashboard-footer b { display: inline-flex; height: 34px; align-items: center; border-radius: 18px; padding: 0 17px; background: var(--ui-color-action); color: var(--ui-color-action-text); font-weight: 800; }
</style>
