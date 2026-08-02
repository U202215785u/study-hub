import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiSpinner from './UiSpinner.vue'

describe('UiSpinner', () => {
  it('uses a status role and visually hidden loading text', () => {
    const wrapper = mount(UiSpinner, { props: { label: '加载知识库' } })
    expect(wrapper.get('[role="status"]')).toBeTruthy()
    expect(wrapper.get('.ui-sr-only').text()).toBe('加载知识库')
  })
})
