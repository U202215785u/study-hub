import UiButton from '../general/UiButton.vue'
import UiEmpty from './UiEmpty.vue'

export default {
  title: '反馈/Empty 空状态', component: UiEmpty, tags: ['autodocs'],
  parameters: { docs: { description: { component: '用于列表、搜索或面板没有内容的状态。只有存在明确下一步时才提供操作。' } } },
  args: { title: '还没有任务', description: '创建第一项任务，开始组织今天的学习。' },
}

export const Default = {}
export const WithAction = { render: (args) => ({ components: { UiButton, UiEmpty }, setup: () => ({ args }), template: '<UiEmpty v-bind="args"><template #action><UiButton size="sm">创建任务</UiButton></template></UiEmpty>' }) }
export const CustomIcon = { render: (args) => ({ components: { UiEmpty }, setup: () => ({ args }), template: '<UiEmpty v-bind="args"><template #icon><span aria-hidden="true">□</span></template></UiEmpty>' }) }
export const NarrowContainer = { decorators: [() => ({ template: '<div style="width:240px"><story /></div>' })] }
