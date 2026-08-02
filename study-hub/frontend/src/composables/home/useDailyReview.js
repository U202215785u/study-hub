import { ref } from 'vue'

export function useDailyReview({ apiPost, apiGet, notify = () => {}, now = () => new Date() }) {
  const input = ref('')
  const loading = ref(false)
  const status = ref('')
  const result = ref('')
  const history = ref([])

  async function loadHistory() {
    try {
      history.value = await apiGet('/review/list')
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
      const date = now().toISOString().slice(0, 10)
      const data = await apiPost('/review/polish', { raw_text: rawText, date })
      result.value = data.polished || ''
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
      result.value = data.report || ''
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
