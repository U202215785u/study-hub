import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from './UiCompactHeader.vue'

describe('UiCompactHeader', () => {
  it('renders the requested heading level and optional meta', () => {
    const wrapper = mount(UiCompactHeader, {
      props: { title: '今日任务', meta: '08月03日', level: 3 },
    })

    expect(wrapper.get('h3').text()).toBe('今日任务')
    expect(wrapper.get('.ui-compact-header__meta').text()).toBe('08月03日')
  })

  it('keeps actions in a separate slot', () => {
    const wrapper = mount(UiCompactHeader, {
      props: { title: '知识库' },
      slots: { action: '<button type="button">新增</button>' },
    })

    expect(wrapper.get('.ui-compact-header__action button').text()).toBe('新增')
  })

  it('supports the large dashboard title size used by the calendar card', () => {
    const wrapper = mount(UiCompactHeader, { props: { title: '2026年 8月', size: 'lg' } })

    expect(wrapper.get('.ui-compact-header').attributes('data-size')).toBe('lg')
    expect(UiCompactHeader.props.size.validator('lg')).toBe(true)
  })

  it('allows a card to keep its detail link in the current tab', () => {
    const wrapper = mount(UiCompactHeader, { props: { title: '工作热力', to: '/heatmap', target: '_self' } })

    expect(wrapper.get('.ui-compact-header__link').attributes('target')).toBe('_self')
  })
})
