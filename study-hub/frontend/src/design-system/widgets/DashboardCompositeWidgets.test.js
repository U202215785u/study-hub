import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
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
    expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
    expect(wrapper.get('.calendar-agenda__week').attributes()).toMatchObject({
      role: 'group',
      'aria-label': '一周日期',
    })
  })

  it('caps the today-focus list at the four visible Figma rows and emits the selected task identifier', async () => {
    const tasks = Array.from({ length: 6 }, (_, index) => ({
      id: `task-${index + 1}`,
      title: `任务 ${index + 1}`,
      status: index === 0 ? 'done' : 'pending',
    }))
    const wrapper = mount(TodayFocusWidget, { props: { tasks, dateLabel: '8月3日' } })

    expect(wrapper.findAll('[data-task-id]')).toHaveLength(4)
    expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
    await wrapper.get('[data-task-id="task-1"]').trigger('click')
    expect(wrapper.emitted('select')).toEqual([['task-1']])
  })

  it('preserves the Figma timeline and stacked task panels when task data is empty', () => {
    const wrapper = mount(TodayFocusWidget)

    expect(wrapper.get('[data-state]').attributes('data-state')).toBe('content')
    expect(wrapper.get('.today-focus__timeline').exists()).toBe(true)
    expect(wrapper.findAll('.today-focus__layer')).toHaveLength(2)
    expect(wrapper.get('.today-focus__task').text()).toContain('今天暂无任务')
  })

  it('rotates category cards from click, drag, and keyboard', async () => {
    const categories = [{ id: 'work', name: '工作', tasks: [] }, { id: 'study', name: '学习', tasks: [] }, { id: 'life', name: '生活', tasks: [] }]
    const wrapper = mount(TodayFocusWidget, { props: { categories } })

    await wrapper.get('[data-category-id="study"]').trigger('click')
    expect(wrapper.get('[data-testid="today-card-title"]').text()).toBe('学习')

    const stack = wrapper.get('[data-testid="today-card-stack"]')
    await stack.trigger('pointerdown', { clientX: 200 })
    await stack.trigger('pointerup', { clientX: 100 })
    expect(wrapper.get('[data-testid="today-card-title"]').text()).toBe('生活')

    await stack.trigger('keydown', { key: 'ArrowRight' })
    expect(wrapper.get('[data-testid="today-card-title"]').text()).toBe('工作')
  })
})
