import { describe, expect, it } from 'vitest'
import { DEFAULT_DASHBOARD_LAYOUT } from '../../design-system/layout/dashboardLayout.js'
import { useDashboardLayout } from './useDashboardLayout.js'

function memoryStorage(initial = {}) {
  const data = new Map(Object.entries(initial))
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, value),
    removeItem: (key) => data.delete(key),
  }
}

describe('useDashboardLayout', () => {
  it('supports cancel, save, reload and restore-default', () => {
    const storage = memoryStorage()
    const dashboard = useDashboardLayout({ storage })
    dashboard.beginEdit()
    dashboard.hide('knowledge')
    dashboard.cancelEdit()
    expect(dashboard.layout.value).toEqual(DEFAULT_DASHBOARD_LAYOUT)

    dashboard.beginEdit()
    dashboard.hide('knowledge')
    dashboard.save()
    expect(dashboard.layout.value.widgets.find((item) => item.id === 'knowledge').visible).toBe(false)
    expect(useDashboardLayout({ storage }).layout.value.widgets.find((item) => item.id === 'knowledge').visible).toBe(false)

    dashboard.restoreDefault()
    expect(dashboard.layout.value).toEqual(DEFAULT_DASHBOARD_LAYOUT)
  })
})
