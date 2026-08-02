import UiTag from './UiTag.vue'

export default {
  title: '数据展示/Tag 标签', component: UiTag, tags: ['autodocs'],
  parameters: { docs: { description: { component: '用于内容分类、来源和主题。Tag 的色调不表达成功、警告等状态语义。' } } },
  argTypes: { tone: { control: 'select', options: ['neutral', 'lime', 'purple', 'orange', 'peach', 'cream'] } },
  args: { tone: 'neutral' },
}

export const Default = { render: (args) => ({ components: { UiTag }, setup: () => ({ args }), template: '<UiTag v-bind="args">知识卡片</UiTag>' }) }
export const Tones = { render: () => ({ components: { UiTag }, template: '<div style="display:flex;gap:8px;flex-wrap:wrap"><UiTag>默认</UiTag><UiTag tone="lime">学习</UiTag><UiTag tone="purple">知识</UiTag><UiTag tone="orange">创作</UiTag><UiTag tone="peach">回顾</UiTag><UiTag tone="cream">计划</UiTag></div>' }) }
export const NarrowContainer = { ...Default, decorators: [() => ({ template: '<div style="width:120px"><story /></div>' })] }
