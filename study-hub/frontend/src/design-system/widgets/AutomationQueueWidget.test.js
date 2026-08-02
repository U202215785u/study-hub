import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AutomationQueueWidget from './AutomationQueueWidget.vue'

describe('AutomationQueueWidget', () => {
  it('emits an item id for retry and open actions', async () => {
    const item = Object.freeze({ id: 'q1', title: '抖音视频解析', status: 'error', progress: 42 })
    const wrapper = mount(AutomationQueueWidget, { props: { items: [item] } })
    await wrapper.get('[data-queue-id="q1"]').trigger('click')
    await wrapper.get('[data-retry-id="q1"]').trigger('click')
    expect(wrapper.emitted('open')).toEqual([['q1']])
    expect(wrapper.emitted('retry')).toEqual([['q1']])
  })

  it('keeps the create action visible when the real queue is empty', () => {
    const wrapper = mount(AutomationQueueWidget)
    expect(wrapper.findAll('button').some((button) => button.text().includes('开始解析'))).toBe(true)
  })
})
