const recordDate = (item) => (item?.plan_date || item?.due_date || '').slice(0, 10)
const activityDate = (item) => (item?.updated_at || item?.created_at || '').slice(0, 10)
const scheduleTime = (item) => {
  if (item?.start_time && item?.end_time) return `${item.start_time} - ${item.end_time}`
  if (item?.start_time) return item.start_time
  return '未安排时间'
}
const widgetStatus = (status) => ({ in_progress: 'running', todo: 'pending' })[status] || status || 'pending'

export function toLocalDateKey(value) {
  const date = value instanceof Date ? value : new Date(value)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function createHomeDashboardData() {
  return {
    mapDocuments(items = []) {
      return items.slice(0, 2).map((item) => ({
        id: item.id,
        title: item.title || '未命名文档',
        meta: item.created_at?.slice(0, 10) || '最近',
        status: item.status || 'ready',
      }))
    },
    mapQueue(items = []) {
      return items.slice(0, 3).map((item) => ({
        id: item.id || item.task_id,
        title: item.title || item.module_id || '自动化任务',
        status: item.status || 'pending',
        progress: Number(item.progressValue ?? item.percent ?? item.progress ?? 0),
      }))
    },
    mapCommands(items = []) {
      return items.slice(0, 2).map((item, index) => ({
        id: item.id || `command-${index}`,
        title: item.title || item.name || '快捷指令',
        route: item.route || item.url || '',
      }))
    },
    mapLaunchers(items = []) {
      return items.slice(0, 2).map((item, index) => ({
        id: `launcher-${index}`,
        title: item.name || item.title || '继续创作',
        thumbnail: item.thumbnail || '',
        kind: item.kind || 'template',
        url: item.url || '',
      }))
    },
    mapAgenda(items = [], selectedDate = '') {
      return items.filter((item) => recordDate(item) === selectedDate).slice(0, 2).map((item) => ({
        id: item.id,
        title: item.title || '未命名任务',
        time: scheduleTime(item),
        tone: item.status === 'done' ? 'purple' : 'lime',
      }))
    },
    mapTodayTasks(items = [], selectedDate = '') {
      return items.filter((item) => recordDate(item) === selectedDate).slice(0, 5).map((item) => ({
        id: item.id,
        title: item.title || '未命名任务',
        time: scheduleTime(item),
        status: widgetStatus(item.status),
        progress: Number(item.progress || 0),
      }))
    },
    mapActivityHeatmap({ tasks = [], documents = [], queue = [] } = {}, endDate = new Date()) {
      const counts = new Map()
      for (const item of [...tasks, ...documents, ...queue]) {
        const date = activityDate(item)
        if (date) counts.set(date, (counts.get(date) || 0) + 1)
      }
      const end = new Date(endDate)
      end.setHours(12, 0, 0, 0)
      return Array.from({ length: 196 }, (_, index) => {
        const date = new Date(end)
        date.setDate(end.getDate() - (195 - index))
        const id = toLocalDateKey(date)
        const count = counts.get(id) || 0
        return { id, count, level: Math.min(count, 5) }
      })
    },
  }
}
