import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import WorkbenchFrame from './WorkbenchFrame.vue'

describe('WorkbenchFrame background slot', () => {
  it('does not create background DOM when the slot is omitted', () => {
    const wrapper = mount(WorkbenchFrame, {
      slots: { default: '<article data-test="content">内容</article>' },
    })

    expect(wrapper.find('[data-dashboard-background]').exists()).toBe(false)
  })

  it('renders the background slot inside the scaled dashboard stage', () => {
    const wrapper = mount(WorkbenchFrame, {
      slots: {
        background: '<div data-dashboard-background class="bento-background" />',
        default: '<article data-test="content">内容</article>',
      },
    })

    const stage = wrapper.get('[data-dashboard-stage]')
    expect(stage.find('[data-dashboard-background]').exists()).toBe(true)
    expect(stage.find('[data-dashboard-background]').element.parentElement).toBe(stage.element)
  })
})
