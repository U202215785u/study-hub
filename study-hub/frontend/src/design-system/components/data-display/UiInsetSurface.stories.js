import UiButton from '../general/UiButton.vue'
import UiInsetSurface from './UiInsetSurface.vue'

export default {
  title: '数据展示/InsetSurface 内嵌表面',
  component: UiInsetSurface,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: '分子组件。统一仪表盘卡片内部的虚线或实线小型表面，真正的按钮和输入语义由插槽内控件提供。',
      },
    },
  },
  argTypes: {
    border: { control: 'select', options: ['dashed', 'solid'] },
    tone: { control: 'select', options: ['default', 'muted'] },
  },
  args: { border: 'dashed', tone: 'default', interactive: false },
  decorators: [() => ({ template: '<div style="width:320px;height:52px"><story /></div>' })],
}

export const Default = { render: (args) => ({ components: { UiInsetSurface }, setup: () => ({ args }), template: '<UiInsetSurface v-bind="args" style="height:100%">设计系统笔记</UiInsetSurface>' }) }
export const Interactive = { args: { interactive: true }, render: Default.render }
export const SolidMuted = { args: { border: 'solid', tone: 'muted' }, render: Default.render }
export const WithActions = { render: (args) => ({ components: { UiInsetSurface, UiButton }, setup: () => ({ args }), template: '<UiInsetSurface v-bind="args" style="height:100%"><button type="button" style="border:0;background:none;color:inherit">设计系统笔记</button><template #actions><UiButton size="xs" shape="pill">复制</UiButton></template></UiInsetSurface>' }) }
export const LongContent = { render: (args) => ({ components: { UiInsetSurface }, setup: () => ({ args }), template: '<UiInsetSurface v-bind="args" style="height:100%"><span style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">一段很长但不能撑开固定卡片宽度的内容标题</span></UiInsetSurface>' }) }
