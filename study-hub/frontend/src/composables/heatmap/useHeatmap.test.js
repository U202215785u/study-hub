import { describe, expect, it, vi } from 'vitest'
import { useHeatmap } from './useHeatmap.js'

const catalog = { default_style_id: 'grid', styles: [{ id: 'grid', status: 'available', settings_schema: { fields: [{ key: 'range_days', type: 'select', options: [90, 196], default: 196 }, { key: 'sources', type: 'multiselect', options: ['tasks'], default: ['tasks'] }, { key: 'cell_shape', type: 'select', options: ['square'], default: 'square' }, { key: 'cell_radius', type: 'number', min: 0, max: 8, step: 1, default: 0 }] } }] }

describe('useHeatmap', () => {
  it('loads the shared contract with browser-local date and dashboard fixed range', async () => {
    const get = vi.fn(async (path) => path === '/heatmap/catalog' ? catalog : path === '/heatmap/preferences' ? { style_id: 'grid', settings: { range_days: 90, sources: ['tasks'], cell_shape: 'square', cell_radius: 8 } } : { cells: [] })
    const heatmap = useHeatmap({ apiGet: get, fixedRangeDays: 196, now: () => new Date(2026, 7, 3) })
    await heatmap.load()
    expect(get).toHaveBeenCalledWith(expect.stringContaining('range_days=196'))
    expect(get).toHaveBeenCalledWith(expect.stringContaining('end_date=2026-08-03'))
    expect(heatmap.settings.value.cell_radius).toBe(0)
  })

  it('keeps restored defaults as an unsaved draft', async () => {
    const get = vi.fn(async (path) => path === '/heatmap/catalog' ? catalog : path === '/heatmap/preferences' ? { style_id: 'grid', settings: { range_days: 90, sources: ['tasks'], cell_shape: 'square', cell_radius: 0 } } : { cells: [] })
    const heatmap = useHeatmap({ apiGet: get })
    await heatmap.load()

    heatmap.reset()

    expect(heatmap.settings.value.range_days).toBe(196)
    expect(heatmap.dirty.value).toBe(true)
  })
})
