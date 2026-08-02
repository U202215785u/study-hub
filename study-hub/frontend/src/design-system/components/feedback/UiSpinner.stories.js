import UiSpinner from './UiSpinner.vue'

export default {
  title: '反馈/Spinner 加载中', component: UiSpinner, tags: ['autodocs'],
  parameters: { docs: { description: { component: '用于等待时间未知的局部加载。整页加载时应配合上下文文字，避免只有旋转图形。' } } },
  argTypes: { size: { control: 'select', options: ['sm', 'md', 'lg'] } },
  args: { size: 'md', label: '加载中' },
}

export const Default = {}
export const Sizes = { render: () => ({ components: { UiSpinner }, template: '<div style="display:flex;align-items:center;gap:20px"><UiSpinner size="sm"/><UiSpinner/><UiSpinner size="lg"/></div>' }) }
