import TaskWidget from './TaskWidget.vue'

const tasks = [
  { id: 't1', title: '项目复盘', time: '10:00 - 11:00', status: 'running', progress: 30 },
  { id: 't2', title: '整理设计系统笔记', time: '14:00 - 15:30', status: 'pending', progress: 0 },
  { id: 't3', title: '完成阅读清单', time: '18:00 - 18:30', status: 'done', progress: 100 },
]
const longTitle = '这是一条用于验证仪表盘组件在极端内容长度下仍然保持稳定布局并且不会遮挡状态与操作区域的六十字学习任务标题示例'

export default { title: 'Study Hub/Widgets/TaskWidget', component: TaskWidget, tags: ['autodocs'], parameters: { docs: { description: { component: '首页任务时间线，对应 Figma 349:405。点击任务只抛出任务 id。' } } }, args: { tasks } }
export const Default = {}
export const Empty = { args: { tasks: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '任务暂时无法加载' } }
export const LongContent = { args: { tasks: [{ ...tasks[0], title: longTitle }] } }
export const Mobile = { parameters: { viewport: { defaultViewport: 'mobile' } } }
