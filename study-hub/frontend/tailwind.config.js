/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--ui-color-canvas)',
        surface: 'var(--ui-color-surface)',
        'surface-hover': 'var(--ui-color-surface-raised)',
        border: 'var(--ui-color-border)',
        text: 'var(--ui-color-text)',
        'text-secondary': 'var(--ui-color-text-muted)',
        accent: 'var(--ui-color-action)',
        'accent-glow': 'rgb(215 255 99 / 15%)',
        danger: 'var(--ui-color-danger)',
        success: 'var(--ui-color-success)',
        warn: 'var(--ui-color-warning)',
        warning: 'var(--ui-color-warning)',
      },
      borderRadius: {
        '12': '12px',
        '8': '8px',
      }
    },
  },
  plugins: [],
}
