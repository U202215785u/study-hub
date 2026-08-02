import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CalendarAgendaWidget from './CalendarAgendaWidget.vue'
import TodayFocusWidget from './TodayFocusWidget.vue'

describe('dashboard composite widgets', () => {
  it('emits calendar and agenda identifiers from the combined schedule card', async () => {
    const wrapper = mount(CalendarAgendaWidget, {
      props: {
        days: [{ date: '2026-08-03', label: '3', selected: true }],
        agenda: [{ id: 'agenda-1', title: '首页校对', time: '10:00' }],
      },
    })

    await wrapper.get('[data-date="2026-08-03"]').trigger('click')
    await wrapper.get('.calendar-agenda__panel button').trigger('click')

    expect(wrapper.emitted('select')).toEqual([['2026-08-03']])
    expect(wrapper.emitted('open')).toEqual([['agenda-1']])
  })

  it('caps the today-focus list and emits the selected task identifier', async () => {
    const tasks = Array.from({ length: 6 }, (_, index) => ({
      id: `task-${index + 1}`,
      title: `任务 ${index + 1}`,
      status: index === 0 ? 'done' : 'pending',
    }))
    const wrapper = mount(TodayFocusWidget, { props: { tasks, dateLabel: '8月3日' } })

    expect(wrapper.findAll('[data-task-id]')).toHaveLength(5)
    await wrapper.get('[data-task-id="task-1"]').trigger('click')
    expect(wrapper.emitted('select')).toEqual([['task-1']])
  })
})
