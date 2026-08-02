import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiWidgetFrame from './UiWidgetFrame.vue'

describe('UiWidgetFrame', () => {
  it.each([
    [{ loading: true, error: '失败', empty: true }, 'loading'],
    [{ error: '失败', empty: true }, 'error'],
    [{ empty: true }, 'empty'],
    [{}, 'content'],
  ])('renders exactly one state with loading > error > empty > content precedence', (props, state) => {
    const wrapper = mount(UiWidgetFrame, {
      props: { title: '小组件', ...props },
      slots: { default: 'CONTENT', loading: 'LOADING', error: 'ERROR', empty: 'EMPTY' },
    })
    expect(wrapper.attributes('data-state')).toBe(state)
    expect(wrapper.get('.ui-widget-frame__body').text()).toBe(state.toUpperCase())
  })
})
