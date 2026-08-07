import GridHeatmapRenderer from './GridHeatmapRenderer.vue'

const renderers = Object.freeze({ grid: GridHeatmapRenderer })

export function getHeatmapRenderer(styleId) {
  return renderers[styleId] || null
}
