import { computed, ref } from 'vue'
import { DEFAULT_DASHBOARD_LAYOUT, normalizeDashboardLayout, placeWidget, reinsertWidget } from '../../design-system/layout/dashboardLayout.js'

export const DASHBOARD_LAYOUT_STORAGE_KEY = 'study-hub:dashboard-layout:v1'
const clone = (layout) => ({ version: layout.version, widgets: layout.widgets.map((item) => ({ ...item })) })

export function useDashboardLayout({ storage = globalThis.localStorage, key = DASHBOARD_LAYOUT_STORAGE_KEY } = {}) {
  const read = () => {
    try { return normalizeDashboardLayout(JSON.parse(storage?.getItem(key) || 'null')) } catch { return clone(DEFAULT_DASHBOARD_LAYOUT) }
  }
  const layout = ref(read())
  const draft = ref(clone(layout.value))
  const isEditing = ref(false)
  const history = ref([])
  const canUndo = computed(() => history.value.length > 0)
  const active = computed(() => isEditing.value ? draft.value : layout.value)
  const remember = () => { history.value.push(clone(draft.value)) }
  const beginEdit = () => { draft.value = clone(layout.value); history.value = []; isEditing.value = true }
  const hide = (id) => { const item = draft.value.widgets.find((widget) => widget.id === id); if (item?.visible) { remember(); item.visible = false } }
  const show = (id) => { const item = draft.value.widgets.find((widget) => widget.id === id); if (item && !item.visible) { remember(); draft.value = reinsertWidget(draft.value, id) } }
  const move = (id, target) => { if (draft.value.widgets.some((widget) => widget.id === id && widget.visible)) { remember(); draft.value = placeWidget(draft.value, id, target) } }
  const undo = () => { const previous = history.value.pop(); if (previous) draft.value = previous }
  const reorder = (id, targetOrder) => {
    const widgets = [...draft.value.widgets].sort((a, b) => a.order - b.order)
    const index = widgets.findIndex((item) => item.id === id)
    if (index < 0) return
    const [item] = widgets.splice(index, 1)
    widgets.splice(Math.max(0, Math.min(targetOrder, widgets.length)), 0, item)
    remember()
    draft.value = normalizeDashboardLayout({ version: 1, widgets: widgets.map((widget, order) => ({ ...widget, order, size: undefined })) })
  }
  const save = () => { layout.value = normalizeDashboardLayout(draft.value); storage?.setItem(key, JSON.stringify(layout.value)); history.value = []; isEditing.value = false }
  const cancelEdit = () => { draft.value = clone(layout.value); history.value = []; isEditing.value = false }
  const restoreDefault = () => { layout.value = clone(DEFAULT_DASHBOARD_LAYOUT); draft.value = clone(DEFAULT_DASHBOARD_LAYOUT); history.value = []; storage?.removeItem(key); isEditing.value = false }
  return { layout, draft, active, isEditing, canUndo, beginEdit, hide, show, move, undo, reorder, save, cancelEdit, restoreDefault }
}
