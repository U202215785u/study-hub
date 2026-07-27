import { ref } from 'vue'

let instance = null

const visible = ref(false)
const title = ref('确认操作')
const message = ref('')
const danger = ref(false)
let resolvePromise = null

export function useConfirm() {
  if (!instance) {
    instance = {
      visible,
      title,
      message,
      danger,
      confirm(options = {}) {
        title.value = options.title ?? '确认操作'
        message.value = options.message ?? ''
        danger.value = options.danger ?? false
        visible.value = true
        return new Promise((resolve) => {
          resolvePromise = resolve
        })
      },
      onConfirm() {
        visible.value = false
        if (resolvePromise) {
          resolvePromise(true)
          resolvePromise = null
        }
      },
      onCancel() {
        visible.value = false
        if (resolvePromise) {
          resolvePromise(false)
          resolvePromise = null
        }
      }
    }
  }
  return instance
}
