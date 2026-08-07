import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DashboardModuleCard from './DashboardModuleCard.vue'

describe('DashboardModuleCard motion', () => {
  it('uses a keyed state node for loading, error, empty, and content', async () => {
    const wrapper = mount(DashboardModuleCard, { props: { title: '任务', loading: true } })
    const first = wrapper.find('[data-card-state]').element

    await wrapper.setProps({ loading: false, error: '请求失败' })
    expect(wrapper.find('[data-card-state]').classes()).toContain('dashboard-module-card__state--error')
    expect(wrapper.find('[data-card-state]').element).not.toBe(first)

    await wrapper.setProps({ error: '', empty: true })
    expect(wrapper.find('[data-card-state]').text()).toContain('暂无内容')
    await wrapper.setProps({ empty: false })
    expect(wrapper.find('[data-card-state]').attributes('data-card-inset')).toBe('16')
  })
})
