import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiEmpty from './UiEmpty.vue'

describe('UiEmpty', () => {
  it('renders its action slot only when supplied', () => {
    const withoutAction = mount(UiEmpty, { props: { title: '暂无内容' } })
    expect(withoutAction.find('.ui-empty__action').exists()).toBe(false)

    const withAction = mount(UiEmpty, {
      props: { title: '暂无内容' },
      slots: { action: '<button>创建</button>' },
    })
    expect(withAction.get('.ui-empty__action').text()).toContain('创建')
  })
})
