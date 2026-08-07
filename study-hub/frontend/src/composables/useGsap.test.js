import { describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick, ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'

const contextRevert = vi.fn()
const mockMedia = {
  cleanups: [],
  add: vi.fn((_, callback) => {
    const cleanup = callback()
    if (typeof cleanup === 'function') mockMedia.cleanups.push(cleanup)
  }),
  revert: vi.fn(() => {
    mockMedia.cleanups.splice(0).forEach((cleanup) => cleanup())
  }),
}
vi.mock('../lib/gsap.js', () => ({
  gsap: {
    matchMedia: vi.fn(() => mockMedia),
    context: vi.fn((callback) => { callback(); return { revert: contextRevert } }),
  },
}))

import { readCssTimeSeconds, useGsap } from './useGsap.js'

describe('useGsap', () => {
  it('converts CSS seconds and milliseconds to seconds', () => {
    vi.stubGlobal('getComputedStyle', vi.fn(() => ({
      getPropertyValue: (name) => name === '--ui-duration-slow' ? '260ms' : '0.12s',
    })))

    expect(readCssTimeSeconds('--ui-duration-slow')).toBe(0.26)
    expect(readCssTimeSeconds('--ui-duration-fast')).toBe(0.12)
  })

  it('creates both media branches and cleans the context and media query', async () => {
    const { gsap } = await import('../lib/gsap.js')
    const media = gsap.matchMedia()
    const setup = vi.fn()
    const onReducedMotion = vi.fn()
    const child = defineComponent({
      setup() {
        const scope = ref(null)
        useGsap({ scope, setup, onReducedMotion })
        return () => h('div', { ref: scope })
      },
    })
    const wrapper = mount(child)
    await nextTick()
    await flushPromises()

    expect(media.add).toHaveBeenCalledTimes(2)
    expect(setup).toHaveBeenCalledOnce()
    expect(onReducedMotion).toHaveBeenCalledOnce()
    wrapper.unmount()
    expect(media.revert).toHaveBeenCalledOnce()
    expect(contextRevert).toHaveBeenCalledOnce()
  })
})
