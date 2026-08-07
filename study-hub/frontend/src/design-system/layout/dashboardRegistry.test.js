import { describe, expect, it } from 'vitest'
import { DEFAULT_DASHBOARD_LAYOUT } from './dashboardLayout.js'
import { DASHBOARD_REGISTRY, normalizeDashboardLayout } from './dashboardRegistry.js'

describe('dashboard registry', () => {
  it('registers all nine Figma modules and rejects incompatible layouts', () => {
    expect(Object.keys(DASHBOARD_REGISTRY)).toHaveLength(9)
    expect(normalizeDashboardLayout({ version: 999, widgets: [{ id: 'missing', size: '7x7' }] })).toEqual(DEFAULT_DASHBOARD_LAYOUT)
  })

  it('derives v2 widget spans from the registry rather than persisted sizes', () => {
    const layout = normalizeDashboardLayout({
      version: 2,
      widgets: [{ id: 'knowledge', visible: false, order: 0, x: 7, y: 2, size: '7x7' }],
    })
    expect(layout.widgets.find((item) => item.id === 'knowledge')).toMatchObject({ id: 'knowledge', visible: false, x: 6, y: 2 })
    expect(layout.widgets.find((item) => item.id === 'knowledge')).not.toHaveProperty('size')
  })
})
