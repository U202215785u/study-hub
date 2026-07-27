import { ref } from 'vue'

let instance = null

const toasts = ref([])
let idCounter = 0

function pushToast(message, type = 'info', duration = null) {
  const id = ++idCounter
  const defaultDuration = type === 'error' ? 4000 : 2500
  const toast = {
    id,
    message,
    type, // 'success' | 'error' | 'info'
    duration: duration ?? defaultDuration
  }
  toasts.value.push(toast)
  setTimeout(() => {
    removeToast(id)
  }, toast.duration)
  return id
}

function removeToast(id) {
  const idx = toasts.value.findIndex(t => t.id === id)
  if (idx !== -1) toasts.value.splice(idx, 1)
}

export function useToast() {
  if (!instance) {
    instance = {
      toasts,
      success: (msg, duration) => pushToast(msg, 'success', duration),
      error: (msg, duration) => pushToast(msg, 'error', duration),
      info: (msg, duration) => pushToast(msg, 'info', duration),
      remove: removeToast
    }
  }
  return instance
}

// 命令式全局调用（不依赖 setup 上下文）
export const toast = {
  success: (msg, duration) => pushToast(msg, 'success', duration),
  error: (msg, duration) => pushToast(msg, 'error', duration),
  info: (msg, duration) => pushToast(msg, 'info', duration)
}
