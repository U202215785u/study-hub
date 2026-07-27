import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => ({
  plugins: [vue()],
  // Electron 环境使用相对路径 (兼容 file:// 协议)
  base: process.env.VITE_ELECTRON ? './' : '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  test: {
    environment: 'jsdom',
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true
      }
    },
    environmentOptions: {
      jsdom: {
        url: 'https://www.bing.com/search?q=test'
      }
    }
  },
  server: {
    port: 5173,
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
