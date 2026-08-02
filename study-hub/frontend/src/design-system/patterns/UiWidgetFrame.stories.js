import UiWidgetFrame from './UiWidgetFrame.vue'

export default {
  title: '数据展示/WidgetFrame 小组件框架', component: UiWidgetFrame, tags: ['autodocs'],
  parameters: { docs: { description: { component: '仪表盘小组件的统一容器，负责标题、内边距和 loading > error > empty > content 状态优先级。' } } },
  args: { title: '知识库', meta: '12 篇', description: '最近更新的学习资料。' },
}

export const Content = { render: (args) => ({ components: { UiWidgetFrame }, setup: () => ({ args }), template: '<UiWidgetFrame v-bind="args"><p style="margin:0">内容区域</p></UiWidgetFrame>' }) }
export const Loading = { ...Content, args: { loading: true } }
export const Error = { ...Content, args: { error: '暂时无法加载，请稍后重试。' } }
export const Empty = { ...Content, args: { empty: true, emptyTitle: '暂无文档', emptyDescription: '创建或导入第一篇文档。' } }
export const StatePrecedence = { ...Content, args: { loading: true, error: '失败', empty: true } }
export const NarrowContainer = { ...Content, decorators: [() => ({ template: '<div style="width:280px"><story /></div>' })] }
