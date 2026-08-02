import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiButton from './UiButton.vue'

describe('UiButton', () => {
  it('emits one click and blocks clicks while loading', async () => {
    const wrapper = mount(UiButton, { slots: { default: '保存' } })

    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)

    await wrapper.setProps({ loading: true })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
    expect(wrapper.attributes('aria-busy')).toBe('true')
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('exposes its visual contract without changing native button semantics', () => {
    const wrapper = mount(UiButton, {
      props: { variant: 'secondary', size: 'lg', block: true },
      slots: { default: '继续' },
    })

    expect(wrapper.element.tagName).toBe('BUTTON')
    expect(wrapper.attributes('type')).toBe('button')
    expect(wrapper.attributes('data-variant')).toBe('secondary')
    expect(wrapper.attributes('data-size')).toBe('lg')
    expect(wrapper.attributes('data-block')).toBe('true')
  })
})
