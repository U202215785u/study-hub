import { computed, ref } from 'vue'
import { DEFAULT_DASHBOARD_LAYOUT } from '../../design-system/layout/dashboardLayout.js'
import { normalizeDashboardLayout } from '../../design-system/layout/dashboardRegistry.js'

export const DASHBOARD_LAYOUT_STORAGE_KEY = 'study-hub:dashboard-layout:v1'
const clone = (layout) => ({ version: layout.version, widgets: layout.widgets.map((item) => ({ ...item })) })

export function useDashboardLayout({ storage = globalThis.localStorage, key = DASHBOARD_LAYOUT_STORAGE_KEY } = {}) {
  const read = () => {
    try { return normalizeDashboardLayout(JSON.parse(storage?.getItem(key) || 'null')) } catch { return clone(DEFAULT_DASHBOARD_LAYOUT) }
  }
  const layout = ref(read())
  const draft = ref(clone(layout.value))
  const isEditing = ref(false)
  const active = computed(() => isEditing.value ? draft.value : layout.value)
  const beginEdit = () => { draft.value = clone(layout.value); isEditing.value = true }
  const hide = (id) => { const item = draft.value.widgets.find((widget) => widget.id === id); if (item) item.visible = false }
  const show = (id) => { const item = draft.value.widgets.find((widget) => widget.id === id); if (item) item.visible = true }
  const reorder = (id, targetOrder) => {
    const widgets = [...draft.value.widgets].sort((a, b) => a.order - b.order)
    const index = widgets.findIndex((item) => item.id === id)
    if (index < 0) return
    const [item] = widgets.splice(index, 1)
    widgets.splice(Math.max(0, Math.min(targetOrder, widgets.length)), 0, item)
    draft.value.widgets = widgets.map((widget, order) => ({ ...widget, order }))
  }
  const save = () => { layout.value = normalizeDashboardLayout(draft.value); storage?.setItem(key, JSON.stringify(layout.value)); isEditing.value = false }
  const cancelEdit = () => { draft.value = clone(layout.value); isEditing.value = false }
  const restoreDefault = () => { layout.value = clone(DEFAULT_DASHBOARD_LAYOUT); draft.value = clone(DEFAULT_DASHBOARD_LAYOUT); storage?.removeItem(key); isEditing.value = false }
  return { layout, draft, active, isEditing, beginEdit, hide, show, reorder, save, cancelEdit, restoreDefault }
}
