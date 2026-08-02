import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiTag from './UiTag.vue'

describe('UiTag', () => {
  it('supports content tones without status semantics', () => {
    const wrapper = mount(UiTag, { props: { tone: 'purple' }, slots: { default: '知识' } })
    expect(wrapper.get('[data-tone="purple"]').text()).toContain('知识')
    expect(wrapper.get('[data-tone="purple"]').attributes('role')).toBeUndefined()
  })

  it('rejects the status-only content-purple name', () => {
    expect(UiTag.props.tone.validator('content-purple')).toBe(false)
  })
})
