import { ref } from 'vue'

export function useContentParser(api) {
  const batch = ref(null)
  const tasks = ref([])

  async function preflight(input, mode) {
    batch.value = await api.apiPost('/content-parser/preflight', { input, mode })
    return batch.value
  }

  async function refreshTasks() {
    const data = await api.apiGet('/automation/queue/status')
    tasks.value = data.tasks || []
    return tasks.value
  }

  async function confirm(itemIds) {
    if (!batch.value?.batch_id) throw new Error('请先检查链接')
    const result = await api.apiPost('/content-parser/confirm', {
      batch_id: batch.value.batch_id,
      item_ids: itemIds,
    })
    await refreshTasks()
    return result
  }

  return { batch, tasks, preflight, confirm, refreshTasks }
}
