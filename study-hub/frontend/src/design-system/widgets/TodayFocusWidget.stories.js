import TodayFocusWidget from './TodayFocusWidget.vue'
const tasks = [{ id: 'a', title: '整理资料', status: 'running', time: '2 hours ago' }, { id: 'b', title: '完成复盘', status: 'done', time: '1 hour ago' }]
export default { title: 'Study Hub Widgets/今日任务 TodayFocusWidget', component: TodayFocusWidget, tags: ['autodocs'], args: { tasks, dateLabel: '08月03日' }, parameters: { docs: { description: { component: '2×3 今日任务模块，对应 Figma 349:405；最多显示五项。' } } } }
export const Default = {}
export const Empty = { args: { tasks: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '任务加载失败' } }
export const Overflow = { args: { tasks: Array.from({ length: 7 }, (_, index) => ({ id: index, title: `真实任务 ${index + 1}`, status: 'pending', time: '未安排时间' })) } }
