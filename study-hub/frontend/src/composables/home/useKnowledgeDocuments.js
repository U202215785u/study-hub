import { ref } from 'vue'

export function useKnowledgeDocuments({ apiGet, apiPost, apiDelete, apiUpload, category = ref(''), notify = () => {}, confirmAction = () => true, clipboard = globalThis.navigator?.clipboard, onReparseQueued = () => {} }) {
  const documents = ref([])
  const sort = ref('created_at:desc')
  const activeDocument = ref(null)

  async function reload() {
    try {
      const [sortBy, sortOrder] = sort.value.split(':')
      documents.value = await apiGet(`/documents?sort_by=${sortBy}&sort_order=${sortOrder}`)
    } catch {
      documents.value = []
    }
  }

  async function setSort(value) {
    sort.value = value
    await reload()
  }

  async function open(id) {
    try {
      const document = await apiGet(`/documents/${id}`)
      if (document.error) return notify(document.error, true)
      activeDocument.value = document
      return document
    } catch {
      notify('加载文档失败', true)
    }
  }

  async function copy(document) {
    try {
      await clipboard.writeText(document.content || '')
      notify('已复制到剪贴板')
    } catch {
      notify('复制失败', true)
    }
  }

  async function remove(id) {
    if (!confirmAction('确定要删除这篇文档吗？')) return
    try {
      await apiDelete(`/documents/${id}`)
      notify('文档已删除')
      await reload()
    } catch {
      notify('删除失败', true)
    }
  }

  async function reparse(id) {
    const document = documents.value.find((item) => item.id === id)
    if (!document || !confirmAction(`重新识别 "${document.title}"？\n将重新提取语音文本并更新文档。`)) return
    try {
      const data = await apiPost(`/automation/reparse/${id}`)
      if (data.error) return notify(data.error, true)
      notify('已重新提交识别任务，处理完成后自动刷新')
      onReparseQueued()
    } catch {
      notify('重新识别失败', true)
    }
  }

  async function uploadFiles(files) {
    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      if (category.value) form.append('category_id', category.value)
      try {
        const data = await apiUpload('/upload', form)
        notify(data.id ? `"${file.name}" 上传成功` : '上传失败', !data.id)
      } catch {
        notify(`上传 "${file.name}" 失败`, true)
      }
    }
    await reload()
  }

  async function openInbox() {
    try {
      const data = await apiGet('/inbox/open')
      notify(data.error || '收件箱已打开', Boolean(data.error))
    } catch {
      notify('打开收件箱失败', true)
    }
  }

  return { documents, sort, activeDocument, reload, setSort, open, copy, remove, reparse, uploadFiles, openInbox }
}
