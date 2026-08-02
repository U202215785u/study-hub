import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiBadge from './UiBadge.vue'

describe('UiBadge', () => {
  it('renders a status dot and a text label', () => {
    const wrapper = mount(UiBadge, { props: { status: 'success', label: '已完成' } })
    expect(wrapper.get('[data-status="success"]')).toBeTruthy()
    expect(wrapper.get('.ui-badge__dot').attributes('aria-hidden')).toBe('true')
    expect(wrapper.text()).toContain('已完成')
  })

  it('accepts only status semantics', () => {
    expect(UiBadge.props.status.validator('content-purple')).toBe(false)
  })
})
