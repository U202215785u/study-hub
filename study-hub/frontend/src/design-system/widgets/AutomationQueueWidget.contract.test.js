import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AutomationQueueWidget from './AutomationQueueWidget.vue'

describe('AutomationQueueWidget input contract', () => {
  it('accepts a controlled URL and emits the value on enter and create', async () => {
    const wrapper = mount(AutomationQueueWidget, { props: { modelValue: '' } })
    const input = wrapper.get('input[data-queue-input]')

    await input.setValue('https://example.com/video')
    await input.trigger('keyup.enter')
    await wrapper.get('[data-queue-create]').trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['https://example.com/video']])
    expect(wrapper.emitted('submit')).toEqual([['https://example.com/video']])
    expect(wrapper.emitted('create')).toEqual([['https://example.com/video']])
  })
})
