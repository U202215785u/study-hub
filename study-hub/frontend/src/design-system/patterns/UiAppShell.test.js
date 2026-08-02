import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiAppShell from './UiAppShell.vue'

describe('UiAppShell', () => {
  it('labels primary navigation, main content and complementary Dock landmarks', () => {
    const wrapper = mount(UiAppShell, {
      slots: { topNavigation: '导航', default: '主页', dock: '快捷工具' },
    })
    expect(wrapper.get('nav').attributes('aria-label')).toBe('主导航')
    expect(wrapper.get('main').text()).toContain('主页')
    expect(wrapper.get('aside[aria-label="快捷工具"]')).toBeTruthy()
  })
})
