import { describe, expect, it } from 'vitest'
import { DEFAULT_DASHBOARD_LAYOUT } from './dashboardLayout.js'
import { DASHBOARD_REGISTRY, normalizeDashboardLayout } from './dashboardRegistry.js'

describe('dashboard registry', () => {
  it('registers all nine Figma modules and rejects incompatible layouts', () => {
    expect(Object.keys(DASHBOARD_REGISTRY)).toHaveLength(9)
    expect(normalizeDashboardLayout({ version: 999, widgets: [{ id: 'missing', size: '7x7' }] })).toEqual(DEFAULT_DASHBOARD_LAYOUT)
  })

  it('repairs invalid module sizes without dropping valid visibility and order', () => {
    const layout = normalizeDashboardLayout({
      version: 1,
      widgets: [{ id: 'knowledge', visible: false, order: 0, size: '7x7' }],
    })
    expect(layout.widgets[0]).toMatchObject({ id: 'knowledge', visible: false, order: 0, size: '2x1' })
  })
})
