import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiProgress from './UiProgress.vue'

describe('UiProgress', () => {
  it('clamps values to 0..100 and exposes the value', () => {
    const wrapper = mount(UiProgress, { props: { value: 140 } })
    expect(wrapper.get('[role="progressbar"]').attributes('aria-valuenow')).toBe('100')
    expect(wrapper.get('[role="progressbar"]').attributes('aria-valuemin')).toBe('0')
    expect(wrapper.get('[role="progressbar"]').attributes('aria-valuemax')).toBe('100')
  })

  it('renders the value label when requested', () => {
    const wrapper = mount(UiProgress, { props: { value: 42, showValue: true } })
    expect(wrapper.text()).toContain('42%')
  })
})
