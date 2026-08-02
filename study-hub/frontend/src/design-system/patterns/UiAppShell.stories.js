import UiAppShell from './UiAppShell.vue'

const renderShell = () => ({
  components: { UiAppShell },
  template: `<UiAppShell>
    <template #brand><strong>Study Hub</strong></template>
    <template #topNavigation><nav aria-label="主导航">首页　知识库　工作流</nav></template>
    <template #sidebar><div style="padding:20px">侧栏</div></template>
    <div style="min-height:500px">主内容</div>
    <template #dock><div style="padding:20px">快捷工具</div></template>
  </UiAppShell>`,
})

export default {
  title: '布局/AppShell 应用外壳', component: UiAppShell, tags: ['autodocs'], layout: 'fullscreen',
  parameters: { docs: { description: { component: '应用级结构，统一品牌区、主导航、侧栏、主内容和 Dock 的响应式关系。' } } },
}

export const Desktop1440 = { render: renderShell, parameters: { viewport: { defaultViewport: 'desktop' } } }
export const Compact1024 = { render: renderShell, parameters: { viewport: { defaultViewport: 'compact' } } }
export const Tablet768 = { render: renderShell, parameters: { viewport: { defaultViewport: 'tablet' } } }
export const Mobile390 = { render: renderShell, parameters: { viewport: { defaultViewport: 'mobile' } } }
