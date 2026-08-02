import GreetingBar from './GreetingBar.vue'

export default {
  title: '导航/GreetingBar 问候信息',
  component: GreetingBar,
  tags: ['autodocs'],
  parameters: { docs: { description: { component: '首页问候、真实日期时间和天气信息，对应 Figma 349:127。' } } },
}

export const Default = { render: () => ({ components: { GreetingBar }, template: '<GreetingBar />' }) }
