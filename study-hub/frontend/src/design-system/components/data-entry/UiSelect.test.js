import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiSelect from './UiSelect.vue'

describe('UiSelect', () => {
  const options = [
    { value: 'today', label: '今天' },
    { value: 'week', label: '本周' },
  ]

  it('emits the selected native value', async () => {
    const wrapper = mount(UiSelect, { props: { label: '范围', options, modelValue: 'today' } })
    await wrapper.get('select').setValue('week')
    expect(wrapper.emitted('update:modelValue')).toEqual([['week']])
  })

  it('associates labels and errors with the select', () => {
    const wrapper = mount(UiSelect, { props: { label: '范围', options, error: '请选择范围' } })
    const select = wrapper.get('select')
    expect(wrapper.get('label').attributes('for')).toBe(select.attributes('id'))
    expect(select.attributes('aria-invalid')).toBe('true')
    expect(select.attributes('aria-describedby')).toContain('error')
  })
})
