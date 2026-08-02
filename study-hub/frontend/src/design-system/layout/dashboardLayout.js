export const DASHBOARD_LAYOUT_VERSION = 1
export const GRID_COLUMNS = 8
export const GRID_ROW_HEIGHT = 153.36
export const GRID_GAP = 14.31

export const DEFAULT_DASHBOARD_LAYOUT = Object.freeze({
  version: DASHBOARD_LAYOUT_VERSION,
  widgets: Object.freeze([
    { id: 'work-heatmap', visible: true, order: 0, size: '4x2' },
    { id: 'calendar-agenda', visible: true, order: 1, size: '2x2' },
    { id: 'today-focus', visible: true, order: 2, size: '2x3' },
    { id: 'automation-queue', visible: true, order: 3, size: '2x2' },
    { id: 'knowledge', visible: true, order: 4, size: '2x1' },
    { id: 'creation-entry', visible: true, order: 5, size: '2x2' },
    { id: 'daily-memory', visible: true, order: 6, size: '1x1' },
    { id: 'quick-command', visible: true, order: 7, size: '1x1' },
    { id: 'quick-workflow', visible: true, order: 8, size: '2x1' },
  ]),
})

export const SIZE_RULES = Object.freeze({
  'work-heatmap': Object.freeze(['4x2']),
  'calendar-agenda': Object.freeze(['2x2']),
  'today-focus': Object.freeze(['2x3']),
  'automation-queue': Object.freeze(['2x2']),
  knowledge: Object.freeze(['2x1']),
  'daily-memory': Object.freeze(['1x1']),
  'quick-command': Object.freeze(['1x1']),
  'creation-entry': Object.freeze(['2x2']),
  'quick-workflow': Object.freeze(['2x1']),
})

const REFERENCE_HEIGHTS = Object.freeze({
  'work-heatmap': 321,
  'calendar-agenda': 321,
  'today-focus': 484,
  'automation-queue': 321,
  knowledge: 153,
  'daily-memory': 153,
  'quick-command': 153,
  'creation-entry': 321,
  'quick-workflow': 153,
})

export function getWidgetGeometry(id, viewportWidth) {
  const widget = DEFAULT_DASHBOARD_LAYOUT.widgets.find((item) => item.id === id)
  const [columns, rows] = (widget?.size || '1x1').split('x').map(Number)
  const gridWidth = Math.min(1368, Math.max(0, viewportWidth - 72))
  const cellWidth = (gridWidth - GRID_GAP * (GRID_COLUMNS - 1)) / GRID_COLUMNS

  return {
    width: cellWidth * columns + GRID_GAP * (columns - 1),
    height: REFERENCE_HEIGHTS[id] ?? (GRID_ROW_HEIGHT * rows + GRID_GAP * (rows - 1)),
  }
}
