import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import UiPillButton from '../components/general/UiPillButton.vue'
import WorkflowWidget from './WorkflowWidget.vue'

describe('WorkflowWidget', () => {
  it('emits the workflow step id when run', async () => {
    const step = Object.freeze({ id: 'w1', label: '收集', status: 'done' })
    const wrapper = mount(WorkflowWidget, { props: { steps: [step] } })
    await wrapper.get('[data-run-id="w1"]').trigger('click')
    expect(wrapper.emitted('run')).toEqual([['w1']])
    expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
    expect(wrapper.findComponent(UiInsetSurface).exists()).toBe(true)
    expect(wrapper.findComponent(UiPillButton).exists()).toBe(true)
  })
})
