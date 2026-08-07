import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import AnimatedNumber from './AnimatedNumber.vue'

describe('AnimatedNumber', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('renders the target integer when its animation reaches the end', async () => {
    const frames = []
    vi.stubGlobal('requestAnimationFrame', (callback) => {
      frames.push(callback)
      return frames.length
    })
    vi.stubGlobal('cancelAnimationFrame', vi.fn())
    vi.stubGlobal('performance', { now: () => 0 })

    const wrapper = mount(AnimatedNumber, { props: { value: 7, duration: 200, reducedMotion: 'never' } })
    frames.shift()(0)
    frames.shift()(200)
    await wrapper.vm.$nextTick()

    expect(wrapper.get('[data-animated-number]').text()).toBe('7')
  })

  it('renders the final value immediately when motion is reduced', () => {
    const wrapper = mount(AnimatedNumber, { props: { value: 12, reducedMotion: 'always' } })

    expect(wrapper.get('[data-animated-number]').text()).toBe('12')
  })
})
