import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CalendarWidget from './CalendarWidget.vue'

describe('CalendarWidget', () => {
  it('emits the selected date identifier', async () => {
    const day = Object.freeze({ date: '2026-06-07', label: '7', selected: true, eventTones: ['lime'] })
    const wrapper = mount(CalendarWidget, { props: { days: [day] } })
    await wrapper.get('[data-date="2026-06-07"]').trigger('click')
    expect(wrapper.emitted('select')).toEqual([['2026-06-07']])
  })
})
