import MotionWrapper from './MotionWrapper.vue'

export default {
  title: '动效/MotionWrapper',
  component: MotionWrapper,
  parameters: {
    a11y: { disable: false },
  },
}

const previewStyle = 'display:grid;place-items:center;width:280px;height:120px;border:1px solid #3e4638;border-radius:16px;background:#1b1d1a;color:#f5f6ee;font:600 14px/1.4 sans-serif;'

export const Default = {
  args: {
    timing: 'normal',
    delay: 0,
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    whileHover: { y: -2 },
    whilePress: { scale: 0.98 },
    reducedMotion: 'user',
  },
  render: (args) => ({
    components: { MotionWrapper },
    setup: () => ({ args }),
    template: `<MotionWrapper v-bind="args" :while-hover="args.whileHover" :while-press="args.whilePress" style="${previewStyle}">悬停或按下查看动效</MotionWrapper>`,
  }),
}

export const Reduced = {
  args: {
    ...Default.args,
    reducedMotion: 'always',
  },
  render: Default.render,
}
