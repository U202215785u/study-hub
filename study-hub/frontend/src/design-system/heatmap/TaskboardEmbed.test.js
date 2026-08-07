import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import TaskboardEmbed from './TaskboardEmbed.vue'

describe('TaskboardEmbed', () => {
  it('uses the fixed study-hub iframe and its lifecycle state', async () => {
    const wrapper = mount(TaskboardEmbed, { global: { stubs: { RouterLink: true } } })
    expect(wrapper.get('iframe').attributes('src')).toBe('http://127.0.0.1:47823/?project=study-hub')
    await wrapper.get('iframe').trigger('load')
    expect(wrapper.get('header').attributes('data-status')).toBe('available')
  })
  it('keeps the homepage version compact without an iframe timer', () => {
    const timer = vi.spyOn(global, 'setTimeout')
    const wrapper = mount(TaskboardEmbed, { props: { compact: true }, global: { stubs: { RouterLink: true } } })
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.get('[data-taskboard-compact]').text()).toContain('study-hub')
    expect(timer).not.toHaveBeenCalled(); timer.mockRestore()
  })

  it('marks an unloaded cross-origin iframe unavailable and allows a retry', async () => {
    vi.useFakeTimers()
    const wrapper = mount(TaskboardEmbed, { global: { stubs: { RouterLink: true } } })
    await vi.advanceTimersByTimeAsync(8000)
    await wrapper.vm.$nextTick()

    expect(wrapper.get('header').attributes('data-status')).toBe('offline')
    await wrapper.get('button').trigger('click')
    expect(wrapper.get('header').attributes('data-status')).toBe('loading')

    wrapper.unmount()
    vi.useRealTimers()
  })
})
