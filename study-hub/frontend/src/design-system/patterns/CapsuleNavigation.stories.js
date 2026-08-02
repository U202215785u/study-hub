import CapsuleNavigation from './CapsuleNavigation.vue'

export default {
  title: '导航/CapsuleNavigation 胶囊导航',
  component: CapsuleNavigation,
  tags: ['autodocs'],
  parameters: { layout: 'fullscreen', docs: { description: { component: '首页主导航，对应 Figma 349:98。提供搜索、通知和进入模块编辑模式的事件。' } } },
}

export const Desktop = { render: () => ({ components: { CapsuleNavigation }, template: '<CapsuleNavigation />' }) }
