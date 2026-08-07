import WorkHeatmapWidget from './WorkHeatmapWidget.vue'
const cells = Array.from({ length: 196 }, (_, id) => ({ id, level: id % 6 }))
export default { title: '仪表盘组件/工作热力 WorkHeatmapWidget', component: WorkHeatmapWidget, tags: ['autodocs'], args: { cells }, parameters: { docs: { description: { component: '4×2 工作热力模块，对应 Figma 349:169；数据变化不改变卡片尺寸。' } } } }
export const Default = {}
export const Loading = { args: { loading: true } }
export const Empty = { args: { cells: [] } }
export const Error = { args: { error: '热力数据加载失败' } }
export const Overflow = { args: { cells: Array.from({ length: 240 }, (_, index) => ({ id: index, level: index % 6 })) } }
