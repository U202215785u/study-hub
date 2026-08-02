import UiButton from '../components/general/UiButton.vue'
import UiPanelHeader from './UiPanelHeader.vue'

export default {
  title: '通用/PanelHeader 面板标题', component: UiPanelHeader, tags: ['autodocs'],
  parameters: { docs: { description: { component: '统一小组件的标题、辅助信息和操作区。操作出现或消失时，标题区高度保持稳定。' } } },
  args: { title: '今日任务', meta: '4 项', description: '按优先级完成今天的学习计划。' },
}

export const Default = {}
export const WithAction = { render: (args) => ({ components: { UiButton, UiPanelHeader }, setup: () => ({ args }), template: '<UiPanelHeader v-bind="args"><template #actions><UiButton size="sm" variant="text">查看全部</UiButton></template></UiPanelHeader>' }) }
export const NarrowContainer = { decorators: [() => ({ template: '<div style="width:260px"><story /></div>' })] }
