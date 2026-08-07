import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiPillButton from './UiPillButton.vue'

describe('UiPillButton', () => {
  it('uses pressed button semantics and emits click', async () => {
    const wrapper = mount(UiPillButton, {
      props: { active: true },
      slots: { default: '一键发布' },
    })

    expect(wrapper.get('button').attributes('aria-pressed')).toBe('true')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('preserves disabled native semantics', async () => {
    const wrapper = mount(UiPillButton, {
      props: { disabled: true },
      slots: { default: '不可用' },
    })

    expect(wrapper.get('button').attributes('disabled')).toBeDefined()
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })
})
