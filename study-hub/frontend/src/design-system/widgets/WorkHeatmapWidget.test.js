import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import WorkHeatmapWidget from './WorkHeatmapWidget.vue'

describe('WorkHeatmapWidget', () => {
  it('renders a stable 196-cell heatmap inside the mapped Figma node', () => {
    const cells = Array.from({ length: 196 }, (_, index) => ({ id: index, level: index % 6 }))
    const wrapper = mount(WorkHeatmapWidget, { props: { cells }, global: { stubs: { RouterLink: true } } })
    expect(wrapper.attributes('data-figma-node')).toBe('349:169')
    expect(wrapper.findAll('[data-heatmap-cell]')).toHaveLength(196)
  })

  it('switches the compact module to a Taskboard entry instead of the DDL view', async () => {
    const wrapper = mount(WorkHeatmapWidget, { props: { viewMode: 'taskboard' }, global: { stubs: { RouterLink: true } } })

    expect(wrapper.findAll('[data-heatmap-cell]')).toHaveLength(0)
    expect(wrapper.text()).toContain('Codex Taskboard')
    expect(wrapper.html()).toContain('/heatmap?view=taskboard')

    await wrapper.get('.switch button:first-child').trigger('click')
    expect(wrapper.emitted('update:viewMode')).toEqual([['heatmap']])
  })
})
