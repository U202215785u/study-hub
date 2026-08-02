import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import BentoDashboardGrid from './BentoDashboardGrid.vue'

describe('BentoDashboardGrid', () => {
  it('exposes the eight-column Figma grid contract', () => {
    const wrapper = mount(BentoDashboardGrid, { slots: { default: '<article data-widget="test" />' } })
    expect(wrapper.classes()).toContain('bento-dashboard-grid')
    expect(wrapper.attributes('data-columns')).toBe('8')
    expect(wrapper.find('[data-widget="test"]').exists()).toBe(true)
  })
})
