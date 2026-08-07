import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiInsetSurface from './UiInsetSurface.vue'

describe('UiInsetSurface', () => {
  it('keeps interaction semantics in its slotted controls', () => {
    const wrapper = mount(UiInsetSurface, {
      props: { border: 'dashed', interactive: true },
      slots: {
        default: '<button type="button">打开文档</button>',
        actions: '<button type="button">复制</button>',
      },
    })

    expect(wrapper.get('.ui-inset-surface').attributes('data-border')).toBe('dashed')
    expect(wrapper.get('.ui-inset-surface').attributes('data-interactive')).toBe('true')
    expect(wrapper.findAll('button')).toHaveLength(2)
    expect(wrapper.find('.ui-inset-surface > button').exists()).toBe(false)
  })

  it('exposes solid muted variants without adding a role', () => {
    const wrapper = mount(UiInsetSurface, {
      props: { border: 'solid', tone: 'muted' },
      slots: { default: '内容' },
    })

    expect(wrapper.get('.ui-inset-surface').attributes()).toMatchObject({
      'data-border': 'solid',
      'data-tone': 'muted',
    })
    expect(wrapper.get('.ui-inset-surface').attributes('role')).toBeUndefined()
  })
})
