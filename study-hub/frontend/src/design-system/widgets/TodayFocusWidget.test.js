import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AnimatedNumber from '../components/data-display/AnimatedNumber.vue'
import TodayFocusWidget from './TodayFocusWidget.vue'

describe('TodayFocusWidget', () => {
  it('passes completed and total task counts to independent number displays', () => {
    const wrapper = mount(TodayFocusWidget, {
      props: { totalTaskCount: 8, completedTaskCount: 3 },
      global: { stubs: { RouterLink: true } },
    })

    expect(wrapper.findAllComponents(AnimatedNumber).map((component) => component.props('value'))).toEqual([3, 8])
  })
})
