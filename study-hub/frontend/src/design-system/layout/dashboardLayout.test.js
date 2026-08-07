import { describe, expect, it } from 'vitest'
import {
  DEFAULT_DASHBOARD_LAYOUT,
  GRID_COLUMNS,
  GRID_GAP,
  GRID_ROW_HEIGHT,
  getWidgetGeometry,
  layoutStyle,
  normalizeDashboardLayout,
  placeWidget,
  reinsertWidget,
} from './dashboardLayout.js'

describe('Figma dashboard geometry', () => {
  it('maps the 1440px reference to eight columns and the nine approved sizes', () => {
    expect(GRID_COLUMNS).toBe(8)
    expect(GRID_ROW_HEIGHT).toBeCloseTo(153.36, 1)
    expect(GRID_GAP).toBeCloseTo(14.31, 1)
    expect(DEFAULT_DASHBOARD_LAYOUT.widgets.map((widget) => widget.id)).toEqual([
      'work-heatmap',
      'calendar-agenda',
      'today-focus',
      'automation-queue',
      'knowledge',
      'creation-entry',
      'quick-workflow',
      'daily-memory',
      'quick-command',
    ])
    expect(getWidgetGeometry('work-heatmap', 1440).width).toBeCloseTo(677, 0)
    expect(getWidgetGeometry('today-focus', 1440).height).toBeCloseTo(484, 0)
  })

  it('migrates v1 list storage to v2 coordinate-only records in reading order', () => {
    const migrated = normalizeDashboardLayout({
      version: 1,
      widgets: [
        { id: 'knowledge', visible: false, order: 0, size: '2x1' },
        { id: 'work-heatmap', visible: true, order: 1, size: '4x2' },
      ],
    })
    expect(migrated.version).toBe(2)
    expect(migrated.widgets.find((item) => item.id === 'knowledge')).toMatchObject({ visible: false, x: 2, y: 2 })
    expect(migrated.widgets.every((item) => !('size' in item))).toBe(true)
    expect(migrated.widgets.map((item) => item.order)).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8])
  })

  it('places a moved module first, then displaces collisions down the same column deterministically', () => {
    const layout = normalizeDashboardLayout(DEFAULT_DASHBOARD_LAYOUT)
    const moved = placeWidget(layout, 'quick-command', { x: 0, y: 0 })
    expect(moved.widgets.find((item) => item.id === 'quick-command')).toMatchObject({ x: 0, y: 0 })
    expect(moved.widgets.find((item) => item.id === 'work-heatmap').y).toBeGreaterThan(0)
    expect(moved.widgets.map((item) => item.id)).toEqual([...moved.widgets].sort((a, b) => a.order - b.order).map((item) => item.id))
  })

  it('reinserts a hidden module into the first legal row-major position', () => {
    const layout = normalizeDashboardLayout(DEFAULT_DASHBOARD_LAYOUT)
    layout.widgets.find((item) => item.id === 'knowledge').visible = false
    const inserted = reinsertWidget(layout, 'knowledge')
    expect(inserted.widgets.find((item) => item.id === 'knowledge')).toMatchObject({ visible: true, x: 2, y: 2 })
  })

  it('creates explicit CSS grid placement from a coordinate record', () => {
    expect(layoutStyle(DEFAULT_DASHBOARD_LAYOUT.widgets[0])).toMatchObject({
      gridColumnStart: 1,
      gridColumnEnd: 'span 4',
      gridRowStart: 1,
      gridRowEnd: 'span 2',
    })
  })
})
