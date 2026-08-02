import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiPanelHeader from './UiPanelHeader.vue'

describe('UiPanelHeader', () => {
  it('renders title and meta while reserving the actions region', () => {
    const wrapper = mount(UiPanelHeader, { props: { title: '今日任务', meta: '4 项' } })
    expect(wrapper.get('h2').text()).toBe('今日任务')
    expect(wrapper.text()).toContain('4 项')
    expect(wrapper.get('.ui-panel-header__actions')).toBeTruthy()
  })

  it('renders actions in the stable actions region', () => {
    const wrapper = mount(UiPanelHeader, {
      props: { title: '今日任务' },
      slots: { actions: '<button>新增</button>' },
    })
    expect(wrapper.get('.ui-panel-header__actions button').text()).toBe('新增')
  })
})
