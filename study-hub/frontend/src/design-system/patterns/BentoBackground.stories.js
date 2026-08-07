import BentoBackground from './BentoBackground.vue'

export default {
  title: '布局/BentoBackground 背景',
  component: BentoBackground,
  tags: ['autodocs'],
  parameters: { layout: 'fullscreen' },
  decorators: [() => ({ template: '<div style="position:relative;width:100%;height:100vh;background:#10140f"><story /></div>' })],
  argTypes: { static: { control: 'boolean' } },
}

export const Default = { args: { static: false } }
export const Static = { args: { static: true } }
