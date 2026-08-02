import '../src/assets/main.css'

export default {
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
        desktop: { name: 'Desktop 1440', styles: { width: '1440px', height: '980px' } },
      },
    },
  },
}
