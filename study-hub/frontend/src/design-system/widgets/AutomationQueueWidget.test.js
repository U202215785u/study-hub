import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiProgress from '../components/data-display/UiProgress.vue'
import UiButton from '../components/general/UiButton.vue'
import AutomationQueueWidget from './AutomationQueueWidget.vue'

describe('AutomationQueueWidget', () => {
  it('shows the article parsing title in the reserved header area', () => {
    const wrapper = mount(AutomationQueueWidget)
    expect(wrapper.get('.queue-widget__title').text()).toBe('文章解析')
  })

  it('opens the full content parser when its title is selected', () => {
    const wrapper = mount(AutomationQueueWidget)
    expect(wrapper.findComponent(UiCompactHeader).props('to')).toBe('/content-parser')
  })

  it('emits an item id for retry and open actions', async () => {
    const item = Object.freeze({ id: 'q1', title: '抖音视频解析', status: 'error', progress: 42 })
    const wrapper = mount(AutomationQueueWidget, { props: { items: [item] } })
    await wrapper.get('[data-queue-id="q1"]').trigger('click')
    await wrapper.get('[data-retry-id="q1"]').trigger('click')
    expect(wrapper.emitted('open')).toEqual([['q1']])
    expect(wrapper.emitted('retry')).toEqual([['q1']])
    expect(wrapper.findComponent(UiProgress).props()).toMatchObject({ size: 'compact', status: 'danger' })
    expect(wrapper.findAllComponents(UiButton).every((button) => button.props('size') === 'xs')).toBe(true)
  })

  it('keeps the create action visible when the real queue is empty', () => {
    const wrapper = mount(AutomationQueueWidget)
    expect(wrapper.findAll('button').some((button) => button.text().includes('开始解析'))).toBe(true)
    expect(wrapper.findAll('[data-queue-row]')).toHaveLength(3)
    expect(wrapper.get('[data-queue-input]').exists()).toBe(true)
  })
})
