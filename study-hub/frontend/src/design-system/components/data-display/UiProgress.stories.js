import UiProgress from './UiProgress.vue'

export default {
  title: '数据展示/Progress 进度', component: UiProgress, tags: ['autodocs'],
  parameters: { docs: { description: { component: '用于展示可量化的完成比例。连续进度使用 linear，阶段任务使用 segmented。' } } },
  argTypes: { type: { control: 'select', options: ['linear', 'segmented'] } },
  args: { value: 64, label: '本周目标', showValue: true },
}

export const Linear = {}
export const Segmented = { args: { type: 'segmented', value: 70, label: '学习阶段' } }
export const Empty = { args: { value: 0 } }
export const Complete = { args: { value: 100 } }
export const NarrowContainer = { decorators: [() => ({ template: '<div style="width:180px"><story /></div>' })] }
