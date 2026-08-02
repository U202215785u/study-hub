import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiInput from './UiInput.vue'

describe('UiInput', () => {
  it('associates its visible label with the native input', () => {
    const wrapper = mount(UiInput, { props: { label: '搜索', modelValue: '' } })
    const input = wrapper.get('input')
    expect(wrapper.get('label').attributes('for')).toBe(input.attributes('id'))
  })

  it('exposes errors through aria-invalid and aria-describedby', () => {
    const wrapper = mount(UiInput, { props: { label: '名称', error: '请输入名称' } })
    const input = wrapper.get('input')
    expect(input.attributes('aria-invalid')).toBe('true')
    expect(input.attributes('aria-describedby')).toContain('error')
    expect(wrapper.text()).toContain('请输入名称')
  })

  it('emits model updates from the native input', async () => {
    const wrapper = mount(UiInput, { props: { label: '名称', modelValue: '' } })
    await wrapper.get('input').setValue('Study')
    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual(['Study'])
  })
})
