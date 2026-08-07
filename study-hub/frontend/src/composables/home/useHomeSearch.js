import { ref } from 'vue'
import catalog from '../../../../shared/workstation-search-catalog.json'

const SAFE_PATHS = new Set(catalog.map((entry) => entry.navigation.path))

export function isSafeNavigation(navigation) {
  return navigation?.kind === 'route'
    && typeof navigation.path === 'string'
    && navigation.path.startsWith('/')
    && SAFE_PATHS.has(navigation.path)
    && (navigation.query == null || (typeof navigation.query === 'object' && !Array.isArray(navigation.query)))
}

export function useHomeSearch({ apiGet, debounceMs = 250 }) {
  const query = ref('')
  const expanded = ref(false)
  const groups = ref([])
  const loading = ref(false)
  const error = ref('')
  const lastQuery = ref('')
  const assistant = ref({ enabled: false, label: '问一问 AI 助手', status: '暂未开放' })
  let timer
  let requestId = 0

  function open() { expanded.value = true }
  function close() { expanded.value = false }

  async function searchNow() {
    const value = query.value.trim()
    expanded.value = true
    if (!value) {
      groups.value = []
      error.value = ''
      loading.value = false
      return
    }

    const currentRequest = ++requestId
    loading.value = true
    error.value = ''
    lastQuery.value = value
    try {
      const data = await apiGet(`/workstation/search?q=${encodeURIComponent(value)}`)
      if (currentRequest !== requestId) return
      groups.value = Array.isArray(data.groups) ? data.groups : []
      assistant.value = data.assistant || assistant.value
    } catch {
      if (currentRequest !== requestId) return
      groups.value = []
      error.value = '搜索服务暂时不可用'
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  function scheduleSearch() {
    clearTimeout(timer)
    open()
    if (!query.value.trim()) {
      groups.value = []
      error.value = ''
      return
    }
    timer = setTimeout(searchNow, debounceMs)
  }

  function retry() {
    if (lastQuery.value) query.value = lastQuery.value
    return searchNow()
  }

  return { query, expanded, groups, loading, error, lastQuery, assistant, open, close, searchNow, scheduleSearch, retry, isSafeNavigation }
}
