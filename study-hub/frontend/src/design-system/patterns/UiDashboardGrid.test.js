import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiDashboardGrid from './UiDashboardGrid.vue'
import UiDashboardItem from './UiDashboardItem.vue'

describe('UiDashboardGrid', () => {
  it('owns the dashboard grid contract', () => {
    const wrapper = mount(UiDashboardGrid, { slots: { default: '<div>内容</div>' } })
    expect(wrapper.classes()).toContain('ui-dashboard-grid')
  })
})

describe('UiDashboardItem', () => {
  it.each(['1x1', '2x1', '2x2', '2x3'])('maps %s to a data-span contract', (span) => {
    const wrapper = mount(UiDashboardItem, { props: { span } })
    expect(wrapper.attributes('data-span')).toBe(span)
  })
})
