import UiDashboardGrid from './UiDashboardGrid.vue'
import UiDashboardItem from './UiDashboardItem.vue'

const renderGrid = () => ({
  components: { UiDashboardGrid, UiDashboardItem },
  template: `<UiDashboardGrid>
    <UiDashboardItem span="1x1"><div class="demo-cell">1x1</div></UiDashboardItem>
    <UiDashboardItem span="2x1"><div class="demo-cell">2x1</div></UiDashboardItem>
    <UiDashboardItem span="2x2"><div class="demo-cell">2x2</div></UiDashboardItem>
    <UiDashboardItem span="2x3"><div class="demo-cell">2x3</div></UiDashboardItem>
  </UiDashboardGrid>`,
})

export default {
  title: '布局/DashboardGrid 仪表盘网格', component: UiDashboardGrid, tags: ['autodocs'],
  parameters: { docs: { description: { component: '首页四级响应式网格：宽屏四列、紧凑桌面三列、平板两列、移动端一列。页面只声明组件跨度。' } } },
  decorators: [() => ({ template: '<div><style>.demo-cell{display:grid;min-height:100%;place-items:center;border:1px solid var(--ui-color-border);border-radius:var(--ui-radius-lg);background:var(--ui-color-surface);color:var(--ui-color-text-strong)}</style><story /></div>' })],
}

export const Responsive = { render: renderGrid }
export const Desktop1440 = { render: renderGrid, parameters: { viewport: { defaultViewport: 'desktop' } } }
export const Compact1024 = { render: renderGrid, parameters: { viewport: { defaultViewport: 'compact' } } }
export const Tablet768 = { render: renderGrid, parameters: { viewport: { defaultViewport: 'tablet' } } }
export const Mobile390 = { render: renderGrid, parameters: { viewport: { defaultViewport: 'mobile' } } }
