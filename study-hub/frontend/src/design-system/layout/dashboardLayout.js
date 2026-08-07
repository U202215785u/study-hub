export const DASHBOARD_LAYOUT_VERSION = 2
export const GRID_COLUMNS = 8
export const GRID_ROW_HEIGHT = 153.36
export const GRID_GAP = 14.31

export const SIZE_RULES = Object.freeze({
  'work-heatmap': Object.freeze(['4x2']), 'calendar-agenda': Object.freeze(['2x2']),
  'today-focus': Object.freeze(['2x3']), 'automation-queue': Object.freeze(['2x2']),
  knowledge: Object.freeze(['2x1']), 'daily-memory': Object.freeze(['1x1']),
  'quick-command': Object.freeze(['1x1']), 'creation-entry': Object.freeze(['2x2']),
  'quick-workflow': Object.freeze(['2x1']),
})

const DEFAULT_WIDGETS = Object.freeze([
  { id: 'work-heatmap', visible: true, order: 0, x: 0, y: 0 },
  { id: 'calendar-agenda', visible: true, order: 1, x: 4, y: 0 },
  { id: 'today-focus', visible: true, order: 2, x: 6, y: 0 },
  { id: 'automation-queue', visible: true, order: 3, x: 0, y: 2 },
  { id: 'knowledge', visible: true, order: 4, x: 2, y: 2 },
  { id: 'creation-entry', visible: true, order: 5, x: 4, y: 2 },
  { id: 'quick-workflow', visible: true, order: 6, x: 2, y: 3 },
  { id: 'daily-memory', visible: true, order: 7, x: 6, y: 3 },
  { id: 'quick-command', visible: true, order: 8, x: 7, y: 3 },
])

export const DEFAULT_DASHBOARD_LAYOUT = Object.freeze({ version: DASHBOARD_LAYOUT_VERSION, widgets: DEFAULT_WIDGETS })
const clone = (layout) => ({ version: layout.version, widgets: layout.widgets.map((item) => ({ ...item })) })

export function getWidgetSpan(id) {
  const [columns = 1, rows = 1] = (SIZE_RULES[id]?.[0] || '1x1').split('x').map(Number)
  return { columns, rows }
}

export function sortByReadingOrder(widgets) {
  return [...widgets].sort((a, b) => a.y - b.y || a.x - b.x || a.order - b.order)
}

const overlaps = (a, b) => a.x < b.x + b.columns && a.x + a.columns > b.x && a.y < b.y + b.rows && a.y + a.rows > b.y
const occupied = (placed, candidate) => placed.some((item) => overlaps(item, candidate))
const candidateAt = (widget, x, y) => ({ ...widget, ...getWidgetSpan(widget.id), x, y })
const legal = (candidate) => candidate.x >= 0 && candidate.y >= 0 && candidate.x + candidate.columns <= GRID_COLUMNS

function firstFree(widget, placed, startY = 0, preferredX) {
  const span = getWidgetSpan(widget.id)
  if (Number.isInteger(preferredX)) {
    for (let y = Math.max(0, startY); ; y += 1) {
      const candidate = { ...widget, ...span, x: preferredX, y }
      if (legal(candidate) && !occupied(placed, candidate)) return candidate
    }
  }
  for (let y = Math.max(0, startY); ; y += 1) {
    for (let x = 0; x <= GRID_COLUMNS - span.columns; x += 1) {
      const candidate = { ...widget, ...span, x, y }
      if (!occupied(placed, candidate)) return candidate
    }
  }
}

function normalizeVisible(widgets) {
  const placed = []
  for (const widget of sortByReadingOrder(widgets.filter((item) => item.visible))) {
    const candidate = candidateAt(widget, widget.x, widget.y)
    placed.push(legal(candidate) && !occupied(placed, candidate) ? candidate : firstFree(widget, placed, widget.y, widget.x))
  }
  return placed.map(({ columns, rows, ...widget }) => widget)
}

function withReadingOrder(widgets) {
  const visible = normalizeVisible(widgets)
  const byId = new Map(visible.map((item) => [item.id, item]))
  const combined = widgets.map((item) => byId.get(item.id) || item)
  return { version: DASHBOARD_LAYOUT_VERSION, widgets: sortByReadingOrder(combined).map((item, order) => ({ ...item, order })) }
}

function migrateV1(input) {
  const incoming = new Map((input.widgets || []).map((item) => [item?.id, item]))
  const source = [...DEFAULT_WIDGETS].sort((a, b) => (incoming.get(a.id)?.order ?? 1000 + a.order) - (incoming.get(b.id)?.order ?? 1000 + b.order))
  const placed = []
  const widgets = source.map((fallback) => {
    const incomingItem = incoming.get(fallback.id)
    const widget = { ...fallback, visible: incomingItem?.visible !== false }
    if (!widget.visible) return widget
    const next = firstFree(widget, placed)
    placed.push(next)
    return { id: widget.id, visible: true, x: next.x, y: next.y, order: fallback.order }
  })
  return withReadingOrder(widgets)
}

export function normalizeDashboardLayout(input) {
  if (!input || !Array.isArray(input.widgets)) return clone(DEFAULT_DASHBOARD_LAYOUT)
  if (input.version === 1) return migrateV1(input)
  if (input.version !== DASHBOARD_LAYOUT_VERSION) return clone(DEFAULT_DASHBOARD_LAYOUT)
  const incoming = new Map(input.widgets.map((item) => [item?.id, item]))
  const widgets = DEFAULT_WIDGETS.map((fallback) => {
    const item = incoming.get(fallback.id)
    if (!item) return { ...fallback }
    const span = getWidgetSpan(fallback.id)
    return {
      id: fallback.id, visible: item.visible !== false,
      x: Number.isInteger(item.x) ? Math.min(Math.max(0, item.x), GRID_COLUMNS - span.columns) : fallback.x,
      y: Number.isInteger(item.y) && item.y >= 0 ? item.y : fallback.y,
      order: Number.isFinite(item.order) ? item.order : fallback.order,
    }
  })
  return withReadingOrder(widgets)
}

export function placeWidget(layout, id, target) {
  const widgets = normalizeDashboardLayout(layout).widgets
  const moved = widgets.find((item) => item.id === id)
  if (!moved || !moved.visible) return { version: DASHBOARD_LAYOUT_VERSION, widgets }
  const span = getWidgetSpan(id)
  const targetWidget = { ...moved, x: Math.min(Math.max(0, Math.floor(target.x || 0)), GRID_COLUMNS - span.columns), y: Math.max(0, Math.floor(target.y || 0)) }
  const placed = [{ ...targetWidget, ...span }]
  for (const widget of sortByReadingOrder(widgets.filter((item) => item.id !== id && item.visible))) {
    const candidate = candidateAt(widget, widget.x, widget.y)
    placed.push(!occupied(placed, candidate) ? candidate : firstFree(widget, placed, widget.y, widget.x))
  }
  const positions = new Map(placed.map(({ columns, rows, ...widget }) => [widget.id, widget]))
  return withReadingOrder(widgets.map((widget) => positions.get(widget.id) || widget))
}

export function reinsertWidget(layout, id) {
  const widgets = normalizeDashboardLayout(layout).widgets
  const item = widgets.find((widget) => widget.id === id)
  if (!item) return { version: DASHBOARD_LAYOUT_VERSION, widgets }
  const placed = widgets.filter((widget) => widget.visible && widget.id !== id).map((widget) => candidateAt(widget, widget.x, widget.y))
  const next = firstFree({ ...item, visible: true }, placed)
  return withReadingOrder(widgets.map((widget) => widget.id === id ? { ...widget, visible: true, x: next.x, y: next.y } : widget))
}

export function layoutStyle(widget) {
  const { columns, rows } = getWidgetSpan(widget.id)
  return { gridColumnStart: widget.x + 1, gridColumnEnd: `span ${columns}`, gridRowStart: widget.y + 1, gridRowEnd: `span ${rows}` }
}

const REFERENCE_HEIGHTS = Object.freeze({ 'work-heatmap': 321, 'calendar-agenda': 321, 'today-focus': 484, 'automation-queue': 321, knowledge: 153, 'daily-memory': 153, 'quick-command': 153, 'creation-entry': 321, 'quick-workflow': 153 })
export function getWidgetGeometry(id, viewportWidth) {
  const { columns, rows } = getWidgetSpan(id)
  const gridWidth = Math.min(1368, Math.max(0, viewportWidth - 72))
  const cellWidth = (gridWidth - GRID_GAP * (GRID_COLUMNS - 1)) / GRID_COLUMNS
  return { width: cellWidth * columns + GRID_GAP * (columns - 1), height: REFERENCE_HEIGHTS[id] ?? (GRID_ROW_HEIGHT * rows + GRID_GAP * (rows - 1)) }
}
