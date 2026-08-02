import { ref } from 'vue'

export function useAutomationQueue({ apiGet, apiPost, apiDelete, interval = 3000, onCompleted = () => {}, notify = () => {}, onApiKeyInvalid = () => {} }) {
  const items = ref([])
  const stats = ref({ total: 0, pending: 0, running: 0, done: 0, error: 0 })
  const stepsByTask = ref({})
  const progressByTask = ref({})
  const seenCompleted = new Set()
  let timer = null

  async function refresh() {
    try {
      const data = await apiGet('/automation/queue/status')
      if (data.stats) stats.value = { ...stats.value, ...data.stats }
      if (!data.tasks) return

      items.value = data.tasks.map((task) => ({ ...task, id: task.id || task.task_id }))
      let hasNewCompletion = false
      for (const task of data.tasks) {
        if (task.steps) stepsByTask.value[task.task_id] = task.steps
        if (task.progress) progressByTask.value[task.task_id] = task.progress
        if ((task.status === 'done' || task.status === 'error') && !seenCompleted.has(task.task_id)) {
          seenCompleted.add(task.task_id)
          hasNewCompletion = true
        }
      }
      if (hasNewCompletion) onCompleted()
    } catch {
      // Polling is best-effort; the next interval retries.
    }
  }

  function start() {
    if (timer) return
    void refresh()
    timer = setInterval(refresh, interval)
  }

  function stop() {
    if (!timer) return
    clearInterval(timer)
    timer = null
  }

  async function clear() {
    try {
      await apiDelete('/automation/queue/clear')
      await refresh()
      notify('已清除已完成任务')
    } catch {
      notify('清除失败', true)
    }
  }

  async function retry(id) {
    try {
      const data = await apiPost(`/automation/queue/retry/${id}`)
      if (data.error) {
        if (data.api_key_invalid) onApiKeyInvalid(data.error)
        else notify(data.error, true)
        return
      }
      notify('任务已重新提交')
      await refresh()
    } catch {
      notify('重试失败', true)
    }
  }

  return { items, stats, stepsByTask, progressByTask, refresh, start, stop, clear, retry }
}
