import { describe, expect, it } from 'vitest'
import { getHeatmapRenderer } from './heatmapRenderers.js'

describe('heatmap renderer registry', () => {
  it('registers only the available grid renderer and leaves reserved styles without a renderer', () => {
    expect(getHeatmapRenderer('grid')).toBeTruthy()
    expect(getHeatmapRenderer('calendar')).toBeNull()
    expect(getHeatmapRenderer('circular')).toBeNull()
    expect(getHeatmapRenderer('flow')).toBeNull()
  })
})
