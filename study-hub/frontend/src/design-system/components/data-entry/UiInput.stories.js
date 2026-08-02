import UiInput from './UiInput.vue'

export default {
  title: '数据录入/Input 输入框', component: UiInput, tags: ['autodocs'],
  parameters: { docs: { description: { component: '用于短文本录入。始终提供可见标签；说明文字与错误信息占用同一辅助区域。' } } },
  args: { label: '任务名称', modelValue: '', placeholder: '输入任务名称', description: '名称应便于快速识别。' },
}

export const Default = {}
export const Required = { args: { required: true } }
export const Error = { args: { modelValue: '未命名', error: '名称已被使用' } }
export const Disabled = { args: { modelValue: '每周回顾', disabled: true } }
export const NarrowContainer = { decorators: [() => ({ template: '<div style="width:220px"><story /></div>' })] }
