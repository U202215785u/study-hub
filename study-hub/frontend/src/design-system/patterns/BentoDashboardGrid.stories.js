import BentoDashboardGrid from './BentoDashboardGrid.vue'

const renderGrid = () => ({
  components: { BentoDashboardGrid },
  template: '<BentoDashboardGrid><div class="bento-demo bento-demo--wide">4×2</div><div class="bento-demo">2×2</div><div class="bento-demo">2×3</div></BentoDashboardGrid>',
})

export default {
  title: '布局/BentoDashboardGrid 八列网格',
  component: BentoDashboardGrid,
  tags: ['autodocs'],
  parameters: { docs: { description: { component: 'Figma 校准的八列 Bento 网格，对应 Frame 349:96；首页模块只使用注册表中的合法跨度。' } } },
  decorators: [() => ({ template: '<div><style>.bento-demo{grid-column:span 2;grid-row:span 2;display:grid;place-items:center;border:1px solid var(--ui-color-border);border-radius:22px;background:var(--ui-color-surface);color:var(--ui-color-text-strong)}.bento-demo--wide{grid-column:span 4}</style><story /></div>' })],
}

export const Default = { render: renderGrid }
