import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import GridHeatmapRenderer from './GridHeatmapRenderer.vue'

describe('GridHeatmapRenderer', () => {
  it('keeps real cells separate from padded grid slots', () => {
    const wrapper = mount(GridHeatmapRenderer, { props: { data: { cells: [{ date: '2026-08-03', count: 2, level: 2, source_counts: { tasks: 2 } }], grid: { columns: 13, slot_count: 91, leading_empty_slots: 2 } }, settings: { cell_gap: 4, cell_shape: 'square', show_legend: true } } })
    expect(wrapper.findAll('.cell')).toHaveLength(1)
    expect(wrapper.findAll('.empty')).toHaveLength(90)
    expect(wrapper.get('.cell').attributes('title')).toContain('tasks: 2')
    expect(wrapper.get('.grid').attributes('style')).toContain('repeat(13')
  })

  it('shows date labels only when the saved display option enables them', () => {
    const data = { cells: [{ date: '2026-08-03', count: 1, level: 1, source_counts: { tasks: 1 } }], grid: { columns: 1, slot_count: 1, leading_empty_slots: 0 } }
    const hidden = mount(GridHeatmapRenderer, { props: { data, settings: { show_date_labels: false } } })
    const visible = mount(GridHeatmapRenderer, { props: { data, settings: { show_date_labels: true } } })

    expect(hidden.find('[data-heatmap-date-label]').exists()).toBe(false)
    expect(visible.get('[data-heatmap-date-label]').text()).toContain('08-03')
  })
})
