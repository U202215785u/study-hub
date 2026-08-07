import '../src/assets/main.css'
import { setup } from '@storybook/vue3'
import { createMemoryHistory, createRouter } from 'vue-router'

const storyRouter = createRouter({
  history: createMemoryHistory(),
  routes: ['/', '/wiki', '/kb', '/workflow', '/ddl', '/journal', '/brainstorm'].map((path) => ({ path, component: { template: '<div />' } })),
})
setup((app) => { app.use(storyRouter) })

export const globalTypes = {
  reducedMotion: {
    description: 'Preview reduced motion tokens',
    defaultValue: 'normal',
    toolbar: {
      icon: 'motion',
      items: [
        { value: 'normal', title: 'Normal motion' },
        { value: 'reduce', title: 'Reduced motion' },
      ],
      dynamicTitle: true,
    },
  },
}

export default {
  decorators: [
    (story, context) => ({
      components: { story },
      setup() {
        return { reducedMotion: context.globals.reducedMotion === 'reduce' }
      },
      template: '<div :data-reduced-motion="reducedMotion ? \'true\' : undefined" :style="reducedMotion ? { \'--ui-duration-fast\': \'0ms\', \'--ui-duration-normal\': \'0ms\', \'--ui-duration-slow\': \'0ms\' } : undefined"><story /></div>',
    }),
  ],
  parameters: {
    backgrounds: {
      default: 'canvas',
      values: [
        { name: 'canvas', value: '#10140F' },
        { name: 'surface', value: '#1B1D1A' },
      ],
    },
    viewport: {
      viewports: {
        mobile: { name: 'Mobile 390', styles: { width: '390px', height: '844px' } },
        tablet: { name: 'Tablet 768', styles: { width: '768px', height: '1024px' } },
        compact: { name: 'Compact 1024', styles: { width: '1024px', height: '980px' } },
        desktop: { name: 'Desktop 1440', styles: { width: '1440px', height: '980px' } },
      },
    },
  },
}
