import { describe, expect, it } from 'vitest'
import {
  DEFAULT_DASHBOARD_LAYOUT,
  GRID_COLUMNS,
  GRID_GAP,
  GRID_ROW_HEIGHT,
  getWidgetGeometry,
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
      'daily-memory',
      'quick-command',
      'creation-entry',
      'quick-workflow',
    ])
    expect(getWidgetGeometry('work-heatmap', 1440).width).toBeCloseTo(677, 0)
    expect(getWidgetGeometry('today-focus', 1440).height).toBeCloseTo(484, 0)
  })
})
