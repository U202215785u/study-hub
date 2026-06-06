import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Electron 环境：配置全局错误处理
if (window.electronAPI) {
  app.config.errorHandler = (err, instance, info) => {
    console.error('[Vue Error]', err, info)
    // 未来可扩展：通过 IPC 发送到主进程记录日志
  }
}

app.mount('#app')
