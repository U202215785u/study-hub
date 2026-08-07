import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CapsuleNavigation from './patterns/CapsuleNavigation.vue'
import CalendarAgendaWidget from './widgets/CalendarAgendaWidget.vue'
import CreationWidget from './widgets/CreationWidget.vue'
import DailyMemoryWidget from './widgets/DailyMemoryWidget.vue'

const global = { stubs: { RouterLink: { template: '<a><slot /></a>' } } }

describe('dashboard micro-interaction contracts', () => {
  it('preserves navigation search and edit/notify event targets', async () => {
    const wrapper = mount(CapsuleNavigation, { global })
    await wrapper.find('input').setValue('vue')
    await wrapper.find('form').trigger('submit')
    await wrapper.find('[aria-label="编辑首页"]').trigger('click')
    await wrapper.find('.capsule-navigation__notice').trigger('click')

    expect(wrapper.emitted('search')).toEqual([['vue']])
    expect(wrapper.emitted('edit')).toHaveLength(1)
    expect(wrapper.emitted('notify')).toHaveLength(1)
  })

  it('emits one date selection and keeps the date size stable', async () => {
    const wrapper = mount(CalendarAgendaWidget, { global, props: {
      days: [{ date: '2026-08-04', label: '4', selected: true }], agenda: [],
    } })
    const day = wrapper.find('[data-date="2026-08-04"]')
    await day.trigger('click')

    expect(wrapper.emitted('select')).toEqual([['2026-08-04']])
    expect(day.attributes('style') || '').not.toContain('width')
    expect(day.attributes('style') || '').not.toContain('height')
  })

  it('keeps daily memory review and journal link as separate focus targets', () => {
    const wrapper = mount(DailyMemoryWidget, { global })
    expect(wrapper.findAll('button, a')).toHaveLength(2)
    expect(wrapper.find('.memory-widget__stack').exists()).toBe(true)
  })

  it('keeps creation actions, item count, and payloads unchanged', async () => {
    const wrapper = mount(CreationWidget, { global, props: { items: [{ id: 'item-1', title: '文章' }] } })
    await wrapper.find('[data-creation-action="drafts"]').trigger('click')
    await wrapper.find('[data-creation-id="item-1"]').trigger('click')

    expect(wrapper.findAll('[data-creation-id]')).toHaveLength(1)
    expect(wrapper.emitted('open')).toEqual([['drafts'], ['item-1']])
  })
})
