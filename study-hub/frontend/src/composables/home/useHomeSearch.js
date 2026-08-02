import { ref } from 'vue'

export function useHomeSearch({ apiPost, openExternal = () => {}, loadCommands = () => ({}), notify = () => {} }) {
  const mode = ref('ai')
  const query = ref('')
  const category = ref('')
  const loading = ref(false)
  const hasResult = ref(false)
  const answer = ref('')
  const sources = ref('')
  const error = ref('')

  async function submit() {
    const value = query.value.trim()
    if (!value) return
    loading.value = true
    hasResult.value = true
    error.value = ''
    answer.value = ''
    sources.value = ''

    try {
      if (mode.value === 'web') {
        const sessionId = `sh_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
        openExternal(`https://www.bing.com/search?q=${encodeURIComponent(value)}&ref=studyhub&sid=${sessionId}`)
        return
      }

      if (mode.value === 'cmd') {
        const url = loadCommands()[value]
        if (url) openExternal(url)
        else notify(`未知命令: ${value}`, true)
        return
      }

      if (mode.value === 'kb') {
        const payload = { question: value }
        if (category.value) payload.category_id = Number.parseInt(category.value, 10)
        const data = await apiPost('/rag/query', payload)
        if (data.error) error.value = data.answer || data.error
        else {
          answer.value = data.answer || ''
          sources.value = data.sources?.join('；') || ''
        }
        return
      }

      const data = await apiPost('/ai-search', { question: value })
      if (data.error) error.value = data.answer || data.error
      else answer.value = data.answer || ''
    } catch {
      error.value = '无法连接后端服务'
    } finally {
      loading.value = false
    }
  }

  function searchKnowledge() {
    mode.value = 'kb'
    return submit()
  }

  function onKeydown(event) {
    if (event.key === 'Enter') return submit()
  }

  return { mode, query, category, loading, hasResult, answer, sources, error, submit, searchKnowledge, onKeydown }
}
