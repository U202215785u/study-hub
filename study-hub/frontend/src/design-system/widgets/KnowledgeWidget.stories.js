import KnowledgeWidget from './KnowledgeWidget.vue'

const items = [
  { id: 'k1', title: '设计系统笔记', meta: '今天', status: 'ready' },
  { id: 'k2', title: 'Vue 组件测试清单', meta: '昨天', status: 'indexing' },
  { id: 'k3', title: '首页信息架构', meta: '6 月 3 日', status: 'ready' },
]
const longTitle = '这是一个用于验证知识条目在极端内容长度下仍然保持稳定截断并且不会遮挡更新时间和状态信息的六十字中文标题示例'

export default { title: 'Study Hub Widgets/知识库 KnowledgeWidget', component: KnowledgeWidget, tags: ['autodocs'], parameters: { docs: { description: { component: '首页最近知识列表，对应 Figma 349:471。打开文档只抛出文档 id。' } } }, args: { items } }
export const Default = {}
export const Empty = { args: { items: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '知识列表暂时无法加载' } }
export const LongContent = { args: { items: [{ ...items[0], title: longTitle }] } }
export const Mobile = { parameters: { viewport: { defaultViewport: 'mobile' } } }
