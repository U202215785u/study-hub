import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import MotionWrapper from './MotionWrapper.vue'

describe('MotionWrapper', () => {
  let media

  beforeEach(() => {
    const listeners = new Set()
    media = {
      matches: false,
      addEventListener: vi.fn((name, listener) => name === 'change' && listeners.add(listener)),
      removeEventListener: vi.fn((name, listener) => name === 'change' && listeners.delete(listener)),
      dispatchChange() {
        listeners.forEach((listener) => listener({ matches: media.matches, media: media.media }))
      },
    }
    vi.stubGlobal('matchMedia', vi.fn(() => media))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('forwards ordinary attributes and keeps object motion props', () => {
    const wrapper = mount(MotionWrapper, {
      attrs: { class: 'item', 'data-module-id': 'knowledge' },
      props: { whileHover: { y: -2 }, whilePress: { scale: 0.98 } },
      slots: { default: '<span data-test="content">内容</span>' },
    })

    expect(wrapper.attributes('class')).toContain('item')
    expect(wrapper.attributes('data-module-id')).toBe('knowledge')
    expect(wrapper.props('whileHover')).toEqual({ y: -2 })
    expect(wrapper.props('whilePress')).toEqual({ scale: 0.98 })
    expect(wrapper.get('[data-test="content"]').text()).toBe('内容')
  })

  it('keeps hover and press feedback immediate when entrance is staggered', () => {
    const wrapper = mount(MotionWrapper, {
      props: {
        delay: 0.48,
        whileHover: { y: -2 },
        whilePress: { scale: 0.98 },
      },
    })

    const motionProps = wrapper.vm.$.subTree.props
    expect(motionProps.transition).toEqual({ duration: 0.18, delay: 0.48 })
    expect(motionProps['while-hover']).toMatchObject({
      transition: { duration: 0.08, delay: 0 },
    })
    expect(motionProps['while-press']).toMatchObject({
      transition: { duration: 0.08, delay: 0 },
    })
  })

  it('renders the final state and disables gestures when reduced motion is always on', () => {
    const wrapper = mount(MotionWrapper, {
      props: { reducedMotion: 'always', whileHover: { y: -2 }, whilePress: { scale: 0.98 } },
    })

    expect(wrapper.attributes('data-motion-state')).toBe('final')
  })

  it('responds to reduced-motion media changes and removes the listener', async () => {
    const wrapper = mount(MotionWrapper)
    expect(wrapper.attributes('data-motion-state')).toBe('animated')

    media.matches = true
    media.dispatchChange()
    await nextTick()
    expect(wrapper.attributes('data-motion-state')).toBe('final')

    media.matches = false
    media.dispatchChange()
    await nextTick()
    expect(wrapper.attributes('data-motion-state')).toBe('animated')

    wrapper.unmount()
    expect(media.removeEventListener).toHaveBeenCalledOnce()
  })
})
