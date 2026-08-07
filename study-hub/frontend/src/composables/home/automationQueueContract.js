const STATUS_PROGRESS = {
  pending: 0,
  extracting: 25,
  summarizing: 60,
  importing: 85,
  running: 60,
  done: 100,
  error: 100,
}

function numericProgress(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return Math.min(100, Math.max(0, value))
  if (typeof value !== 'string') return null
  const match = value.match(/(\d+(?:\.\d+)?)/)
  if (!match) return null
  const parsed = Number(match[1])
  return Number.isFinite(parsed) ? Math.min(100, Math.max(0, parsed)) : null
}

export function normalizeAutomationTask(task = {}) {
  const status = task.status || 'pending'
  const rawProgress = task.progress_text ?? task.progressText ?? task.progress ?? ''
  const progress = numericProgress(rawProgress) ?? STATUS_PROGRESS[status] ?? 0
  const moduleName = task.module_name || task.moduleName || task.module_id || task.moduleId || 'Automation task'
  const title = task.title || task.result?.title || moduleName

  return {
    ...task,
    id: task.id || task.task_id,
    title,
    moduleName,
    status,
    progress,
    progressValue: progress,
    progressText: String(rawProgress || status),
  }
}
