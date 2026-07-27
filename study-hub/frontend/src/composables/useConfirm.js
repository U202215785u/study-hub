import { ref } from 'vue'

let instance = null

const visible = ref(false)
const title = ref('确认操作')
const message = ref('')
const danger = ref(false)
const requestId = ref(0)
const pendingRequests = []
let activeRequest = null

function showNextRequest() {
  if (activeRequest || pendingRequests.length === 0) return

  activeRequest = pendingRequests.shift()
  const options = activeRequest.options
  title.value = options.title ?? '确认操作'
  message.value = options.message ?? ''
  danger.value = options.danger ?? false
  requestId.value++
  visible.value = true
}

function settleActiveRequest(result) {
  if (!activeRequest) return

  const request = activeRequest
  activeRequest = null
  request.resolve(result)

  if (pendingRequests.length > 0) {
    showNextRequest()
  } else {
    visible.value = false
  }
}

export function useConfirm() {
  if (!instance) {
    instance = {
      visible,
      title,
      message,
      danger,
      requestId,
      confirm(options = {}) {
        return new Promise((resolve) => {
          pendingRequests.push({ options, resolve })
          showNextRequest()
        })
      },
      onConfirm() {
        settleActiveRequest(true)
      },
      onCancel() {
        settleActiveRequest(false)
      }
    }
  }
  return instance
}
