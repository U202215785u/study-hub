import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import DailyMemoryWidget from './DailyMemoryWidget.vue'
import QuickCommandWidget from './QuickCommandWidget.vue'

describe('compact dashboard widgets', () => {
  it('maps daily memory to the 1x1 Figma card', () => {
    const wrapper = mount(DailyMemoryWidget, { props: { title: '今日手账' } })
    expect(wrapper.attributes('data-figma-node')).toBe('349:484')
    expect(wrapper.text()).toContain('今日手账')
  })

  it('caps visible quick commands at two', () => {
    const wrapper = mount(QuickCommandWidget, { props: { commands: [
      { id: 'a', title: '更新日志' }, { id: 'b', title: '编译Wiki' }, { id: 'c', title: '隐藏项' },
    ] } })
    expect(wrapper.attributes('data-figma-node')).toBe('349:510')
    expect(wrapper.findAll('[data-command-id]')).toHaveLength(2)
    expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
    expect(wrapper.findAllComponents(UiInsetSurface)).toHaveLength(2)
  })
})
