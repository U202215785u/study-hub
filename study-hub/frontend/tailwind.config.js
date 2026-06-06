/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0f0f14',
        surface: '#1a1a24',
        'surface-hover': '#22222f',
        border: '#2a2a3a',
        text: '#e0e0e8',
        'text-secondary': '#8888a0',
        accent: '#7c8aff',
        'accent-glow': 'rgba(124, 138, 255, 0.15)',
        danger: '#ff5c7a',
        success: '#10b981',
        warn: '#f59e0b',
      },
      borderRadius: {
        '12': '12px',
        '8': '8px',
      }
    },
  },
  plugins: [],
}
