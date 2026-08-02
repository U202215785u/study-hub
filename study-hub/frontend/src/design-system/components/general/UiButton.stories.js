import UiButton from './UiButton.vue'
import UiIconButton from './UiIconButton.vue'

export default {
  title: '通用/Button 按钮',
  component: UiButton,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: '用于触发即时操作。一个操作区域最多保留一个 primary 按钮，危险操作使用 danger 并配合确认流程。',
      },
    },
  },
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'quiet', 'text', 'danger'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
  },
  args: { variant: 'primary', size: 'md', loading: false, disabled: false, block: false },
}

export const Primary = { args: {}, render: (args) => ({ components: { UiButton }, setup: () => ({ args }), template: '<UiButton v-bind="args">开始工作</UiButton>' }) }

export const Variants = {
  render: () => ({
    components: { UiButton },
    template: `<div style="display:flex;gap:12px;flex-wrap:wrap">
      <UiButton>主要操作</UiButton><UiButton variant="secondary">次要操作</UiButton>
      <UiButton variant="quiet">安静操作</UiButton><UiButton variant="text">文字操作</UiButton>
      <UiButton variant="danger">危险操作</UiButton>
    </div>`,
  }),
}

export const Sizes = {
  render: () => ({ components: { UiButton }, template: '<div style="display:flex;align-items:center;gap:12px"><UiButton size="sm">小</UiButton><UiButton>中</UiButton><UiButton size="lg">大</UiButton></div>' }),
}

export const WithIcon = {
  render: () => ({ components: { UiButton, UiIconButton }, template: '<div style="display:flex;gap:12px"><UiButton><template #prefix>＋</template>新建任务</UiButton><UiIconButton label="添加任务">＋</UiIconButton></div>' }),
}

export const Loading = { args: { loading: true }, render: Primary.render }
export const Disabled = { args: { disabled: true }, render: Primary.render }
export const Danger = { args: { variant: 'danger' }, render: Primary.render }
export const Block = { args: { block: true }, render: Primary.render }
