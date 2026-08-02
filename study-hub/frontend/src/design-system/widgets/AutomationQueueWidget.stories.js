import AutomationQueueWidget from './AutomationQueueWidget.vue'

const items = [
  { id: 'q1', title: '抖音视频解析', status: 'running', progress: 42 },
  { id: 'q2', title: 'B 站课程摘要', status: 'pending', progress: 0 },
  { id: 'q3', title: '小红书笔记归档', status: 'error', progress: 68 },
]
const longTitle = '这是一个用于验证自动化队列条目在极端内容长度下仍能截断且不会遮挡状态和重试操作区域的六十字中文标题示例'

export default { title: 'Study Hub/Widgets/AutomationQueueWidget', component: AutomationQueueWidget, tags: ['autodocs'], parameters: { docs: { description: { component: '首页自动化队列，对应 Figma 349:369。打开和重试事件只抛出队列 id。' } } }, args: { items } }
export const Default = {}
export const Empty = { args: { items: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '队列暂时无法加载' } }
export const LongContent = { args: { items: [{ ...items[0], title: longTitle }] } }
export const Mobile = { parameters: { viewport: { defaultViewport: 'mobile' } } }
