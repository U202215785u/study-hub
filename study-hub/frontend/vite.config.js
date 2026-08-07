import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { FRONTEND_DEV_PORT } from './src/config/ports.js'

export default defineConfig(({ mode }) => ({
  plugins: [vue()],
  resolve: {
    alias: {
      '@study-ui': fileURLToPath(new URL('./src/design-system/index.js', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js'],
  },
  // Electron 环境使用相对路径 (兼容 file:// 协议)
  base: process.env.VITE_ELECTRON ? './' : '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          animations: ['gsap', 'gsap/Flip'],
        },
      },
    },
  },
  server: {
    port: FRONTEND_DEV_PORT,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8741',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/mods': {
        target: 'http://localhost:8741',
        changeOrigin: true,
      },
      '/second-self/api': {
        target: 'http://localhost:8741',
        changeOrigin: true,
      }
    }
  }
}))
