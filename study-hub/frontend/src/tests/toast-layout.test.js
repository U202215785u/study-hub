import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import App from '../App.vue'
import { useToast } from '../composables/useToast.js'

vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/wiki/example' })
}))

describe('global feedback integration', () => {
  const toastApi = useToast()

  beforeEach(() => {
    vi.useFakeTimers()
    toastApi.toasts.value.splice(0)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('keeps multiple toasts until each timeout expires', () => {
    toastApi.success('saved', 100)
    toastApi.error('failed', 200)
    expect(toastApi.toasts.value.map(item => item.message)).toEqual(['saved', 'failed'])

    vi.advanceTimersByTime(100)
    expect(toastApi.toasts.value.map(item => item.message)).toEqual(['failed'])
    vi.advanceTimersByTime(100)
    expect(toastApi.toasts.value).toHaveLength(0)
  })

  it('keeps Wiki in full-screen layout while mounting global feedback', () => {
    const wrapper = shallowMount(App, {
      global: {
        stubs: {
          RouterView: { template: '<main data-test="wiki-view" />' }
        }
      }
    })

    expect(wrapper.find('[data-test="wiki-view"]').exists()).toBe(true)
    expect(wrapper.find('.max-w-5xl').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'AppToast' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'AppConfirm' }).exists()).toBe(true)
  })
})
