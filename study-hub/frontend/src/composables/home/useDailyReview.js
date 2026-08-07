import { ref } from 'vue'

function responseError(data, fallback) {
  if (data && typeof data === 'object') {
    const message = data.error || data.detail || data.message
    if (typeof message === 'string' && message.trim()) return message
  }
  return fallback
}

function requiredText(data, field, fallback) {
  const value = data?.[field]
  if (typeof value === 'string' && value.trim()) return value
  throw new Error(responseError(data, fallback))
}

function localDateKey(value) {
  const date = value instanceof Date ? value : new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

export function useDailyReview({ apiPost, apiGet, notify = () => {}, now = () => new Date() }) {
  const input = ref('')
  const loading = ref(false)
  const status = ref('')
  const result = ref('')
  const history = ref([])

  async function loadHistory() {
    try {
      const data = await apiGet('/review/list')
      if (!Array.isArray(data)) throw new Error(responseError(data, 'Review history response is invalid'))
      history.value = data
    } catch {
      history.value = []
    }
  }

  async function polish() {
    const rawText = input.value.trim()
    if (!rawText) return notify('请先输入今天的笔记', true)
    loading.value = true
    status.value = '正在润色…'
    try {
      const date = localDateKey(now())
      const data = await apiPost('/review/polish', { raw_text: rawText, date })
      result.value = requiredText(data, 'polished', 'Review polish returned no result')
      status.value = '完成'
      await loadHistory()
    } catch {
      notify('润色失败', true)
      status.value = ''
    } finally {
      loading.value = false
    }
  }

  async function weeklyReport() {
    loading.value = true
    status.value = '正在生成周报…'
    try {
      const data = await apiGet('/review/weekly')
      result.value = requiredText(data, 'report', 'Weekly report returned no result')
      status.value = '完成'
    } catch {
      notify('周报生成失败', true)
      status.value = ''
    } finally {
      loading.value = false
    }
  }

  function view(item) {
    result.value = item.polished || item.raw_text || ''
  }

  return { input, loading, status, result, history, polish, weeklyReport, loadHistory, view }
}
