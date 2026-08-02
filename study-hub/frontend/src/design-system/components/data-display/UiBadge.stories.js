import UiBadge from './UiBadge.vue'

export default {
  title: '数据展示/Badge 状态徽标', component: UiBadge, tags: ['autodocs'],
  parameters: { docs: { description: { component: '用于明确的系统状态。状态点必须与文字一起出现，不能只依赖颜色传达含义。' } } },
  argTypes: { status: { control: 'select', options: ['neutral', 'info', 'success', 'warning', 'danger'] } },
  args: { status: 'success', label: '已完成' },
}

export const Default = {}
export const Statuses = { render: () => ({ components: { UiBadge }, template: '<div style="display:grid;gap:8px"><UiBadge status="neutral" label="未开始"/><UiBadge status="info" label="进行中"/><UiBadge status="success" label="已完成"/><UiBadge status="warning" label="需关注"/><UiBadge status="danger" label="失败"/></div>' }) }
export const NarrowContainer = { decorators: [() => ({ template: '<div style="width:120px"><story /></div>' })] }
