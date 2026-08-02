import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import WorkHeatmapWidget from './WorkHeatmapWidget.vue'

describe('WorkHeatmapWidget', () => {
  it('renders a stable 196-cell heatmap inside the mapped Figma node', () => {
    const cells = Array.from({ length: 196 }, (_, index) => ({ id: index, level: index % 6 }))
    const wrapper = mount(WorkHeatmapWidget, { props: { cells } })
    expect(wrapper.attributes('data-figma-node')).toBe('349:169')
    expect(wrapper.findAll('[data-heatmap-cell]')).toHaveLength(196)
  })
})
