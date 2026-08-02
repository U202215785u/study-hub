import UiSelect from './UiSelect.vue'

const options = [
  { value: 'today', label: '今天' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
]

export default {
  title: '数据录入/Select 选择器', component: UiSelect, tags: ['autodocs'],
  parameters: { docs: { description: { component: '用于从有限选项中选择一个值。选项较多或需要搜索时，应升级为组合式选择模式。' } } },
  args: { label: '时间范围', modelValue: 'today', options, description: '决定仪表盘显示的数据范围。' },
}

export const Default = {}
export const Error = { args: { modelValue: '', error: '请选择时间范围', placeholder: '请选择' } }
export const Disabled = { args: { disabled: true } }
export const NarrowContainer = { decorators: [() => ({ template: '<div style="width:220px"><story /></div>' })] }
