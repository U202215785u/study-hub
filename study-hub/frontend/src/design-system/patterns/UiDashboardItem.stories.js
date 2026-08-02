import UiDashboardItem from './UiDashboardItem.vue'

export default {
  title: '布局/DashboardItem 网格项目',
  component: UiDashboardItem,
  tags: ['autodocs'],
  args: { span: '2x2' },
  argTypes: { span: { control: 'select', options: ['1x1', '2x1', '2x2', '2x3'] } },
  parameters: { docs: { description: { component: '声明组件在仪表盘中的合法跨度，不改变内容语义。' } } },
}

export const Default = { render: (args) => ({ components: { UiDashboardItem }, setup: () => ({ args }), template: '<UiDashboardItem v-bind="args"><div style="min-height:153px;border:1px solid var(--ui-color-border);border-radius:22px;padding:20px">{{ args.span }}</div></UiDashboardItem>' }) }
