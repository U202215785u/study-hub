import DailyMemoryWidget from './DailyMemoryWidget.vue'
export default { title: 'Study Hub Widgets/今日手账 DailyMemoryWidget', component: DailyMemoryWidget, tags: ['autodocs'], parameters: { docs: { description: { component: '1×1 今日手账入口，对应 Figma 349:484。' } } } }
export const Default = { args: { title: '今日手账' } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '手账加载失败' } }
