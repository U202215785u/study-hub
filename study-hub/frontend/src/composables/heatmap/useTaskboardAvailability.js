import { ref } from 'vue'

export function useTaskboardAvailability({ timeout = 8000 } = {}) {
  const status = ref('idle')
  let timer = null

  function clear() {
    if (timer) clearTimeout(timer)
    timer = null
  }

  function begin() {
    clear()
    status.value = 'loading'
    timer = setTimeout(() => {
      status.value = 'offline'
      timer = null
    }, timeout)
  }

  function onLoad() {
    clear()
    status.value = 'available'
  }

  function onError() {
    clear()
    status.value = 'offline'
  }

  function dispose() {
    clear()
  }

  return { status, begin, onLoad, onError, dispose }
}
