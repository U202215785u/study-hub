import WorkflowWidget from './WorkflowWidget.vue'

const steps = [
  { id: 'w1', label: '收集', status: 'done' },
  { id: 'w2', label: '理解', status: 'done' },
  { id: 'w3', label: '整理', status: 'running' },
  { id: 'w4', label: '输出', status: 'pending' },
]
const longTitle = '这是一个用于验证学习流程步骤在极端内容长度下仍然稳定截断并且不会破坏节点连接线与交互区域的六十字中文标题示例'

export default { title: 'Study Hub/Widgets/WorkflowWidget', component: WorkflowWidget, tags: ['autodocs'], parameters: { docs: { description: { component: '首页学习流程，对应 Figma 349:459。运行步骤只抛出步骤 id。' } } }, args: { steps } }
export const Default = {}
export const Empty = { args: { steps: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '流程暂时无法加载' } }
export const LongContent = { args: { steps: [{ ...steps[0], label: longTitle }] } }
export const Mobile = { parameters: { viewport: { defaultViewport: 'mobile' } } }
