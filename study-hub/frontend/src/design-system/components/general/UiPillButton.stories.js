import UiPillButton from './UiPillButton.vue'

export default {
  title: '通用/PillButton 胶囊按钮',
  component: UiPillButton,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: '原子组件。用于仪表盘卡片内部的紧凑选项、步骤和胶囊动作；导航链接继续使用原生链接语义。',
      },
    },
  },
  argTypes: { tone: { control: 'select', options: ['neutral', 'action'] } },
  args: { active: false, disabled: false, tone: 'neutral' },
}

export const Default = { render: (args) => ({ components: { UiPillButton }, setup: () => ({ args }), template: '<UiPillButton v-bind="args">草稿箱</UiPillButton>' }) }
export const Active = { args: { active: true }, render: Default.render }
export const Action = { args: { tone: 'action' }, render: Default.render }
export const Disabled = { args: { disabled: true }, render: Default.render }
export const LongContent = { render: () => ({ components: { UiPillButton }, template: '<div style="width:120px"><UiPillButton>不会撑开容器的较长选项</UiPillButton></div>' }) }
