import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import WorkHeatmapWidget from './WorkHeatmapWidget.vue'

describe('WorkHeatmapWidget', () => {
  it('renders a stable 196-cell heatmap inside the mapped Figma node', () => {
    const cells = Array.from({ length: 196 }, (_, index) => ({ id: index, level: index % 6 }))
    const wrapper = mount(WorkHeatmapWidget, { props: { cells }, global: { stubs: { RouterLink: true } } })
    expect(wrapper.attributes('data-figma-node')).toBe('349:169')
    expect(wrapper.findAll('[data-heatmap-cell]')).toHaveLength(196)
    expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
    expect(wrapper.get('.heatmap-widget__grid').attributes()).toMatchObject({
      role: 'img',
      'aria-label': '近期工作热力',
    })
  })

  it('switches between heatmap and the compact Codex Taskboard view', async () => {
    const wrapper = mount(WorkHeatmapWidget, { props: { cells: [{ id: 1, level: 1 }], viewMode: 'heatmap' } })

    expect(wrapper.get('[data-view-mode="heatmap"]').exists()).toBe(true)
    await wrapper.get('[data-view-switch="taskboard"]').trigger('click')
    expect(wrapper.emitted('update:viewMode')).toEqual([['taskboard']])

    await wrapper.setProps({ viewMode: 'taskboard' })
    expect(wrapper.get('[data-taskboard-compact]').text()).toContain('Codex Taskboard')
    expect(wrapper.find('iframe').exists()).toBe(false)
  })

  it('switches the compact module to a Taskboard entry instead of the DDL view', async () => {
    const wrapper = mount(WorkHeatmapWidget, { props: { viewMode: 'taskboard' }, global: { stubs: { RouterLink: true } } })

    expect(wrapper.findAll('[data-heatmap-cell]')).toHaveLength(0)
    expect(wrapper.text()).toContain('Codex Taskboard')
    expect(wrapper.html()).toContain('/heatmap?view=taskboard')

    await wrapper.get('[data-view-switch="heatmap"]').trigger('click')
    expect(wrapper.emitted('update:viewMode')).toEqual([['heatmap']])
  })
})
