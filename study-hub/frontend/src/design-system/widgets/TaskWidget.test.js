import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import TaskWidget from './TaskWidget.vue'

describe('TaskWidget', () => {
  it('emits the task identifier without mutating the task', async () => {
    const task = Object.freeze({ id: 't1', title: '项目复盘', time: '10:00 - 11:00', status: 'running', progress: 30 })
    const wrapper = mount(TaskWidget, { props: { tasks: [task] } })
    await wrapper.get('[data-task-id="t1"]').trigger('click')
    expect(wrapper.emitted('select')).toEqual([['t1']])
  })
})
