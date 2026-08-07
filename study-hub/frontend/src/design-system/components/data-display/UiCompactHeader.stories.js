import UiCompactHeader from './UiCompactHeader.vue'

export default {
  title: '数据展示/CompactHeader 紧凑标题',
  component: UiCompactHeader,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: '分子组件。用于固定高度仪表盘卡片中的单行标题、辅助信息和右侧操作。',
      },
    },
  },
  argTypes: {
    level: { control: 'select', options: [2, 3, 4, 5, 6] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
  },
  args: { title: '知识库', meta: '2 篇', level: 2, size: 'sm' },
}

export const Default = {}
export const Medium = { args: { size: 'md', title: '创作入口' } }
export const Large = { args: { size: 'lg', title: '2026年 8月' } }
export const WithAction = { render: (args) => ({ components: { UiCompactHeader }, setup: () => ({ args }), template: '<UiCompactHeader v-bind="args"><template #action><button type="button">新增</button></template></UiCompactHeader>' }) }
export const LongContent = { args: { title: '一个很长但不会挤压右侧信息或改变卡片高度的标题' }, decorators: [() => ({ template: '<div style="width:220px"><story /></div>' })] }
