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
  }
}
