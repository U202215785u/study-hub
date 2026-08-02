import UiIconButton from './UiIconButton.vue'

export default {
  title: '通用/IconButton 图标按钮',
  component: UiIconButton,
  tags: ['autodocs'],
  args: { label: '添加任务', size: 'md', variant: 'quiet' },
}

export const Default = {
  render: (args) => ({ components: { UiIconButton }, setup: () => ({ args }), template: '<UiIconButton v-bind="args">＋</UiIconButton>' }),
}
