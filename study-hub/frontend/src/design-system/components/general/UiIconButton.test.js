import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import UiIconButton from './UiIconButton.vue'

describe('UiIconButton', () => {
  it('requires an accessible label', () => {
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => {})
    try {
      expect(() => mount(UiIconButton)).toThrow(/label/)
    } finally {
      warning.mockRestore()
    }
  })

  it('uses the label for its accessible name and tooltip', () => {
    const wrapper = mount(UiIconButton, {
      props: { label: '打开搜索' },
      slots: { default: '<span aria-hidden="true">S</span>' },
    })

    expect(wrapper.get('button').attributes('aria-label')).toBe('打开搜索')
    expect(wrapper.get('button').attributes('title')).toBe('打开搜索')
  })
})
