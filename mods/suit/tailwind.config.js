/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#f97316',
          light: '#fff7ed',
        },
        secondary: '#3b82f6',
        success: '#22c55e',
        danger: '#ef4444',
        warning: '#f59e0b',
        bg: '#f8fafc',
        surface: '#ffffff',
        text: {
          DEFAULT: '#1e293b',
          muted: '#64748b',
        },
        border: '#e2e8f0',
      },
    },
  },
  plugins: [],
}
