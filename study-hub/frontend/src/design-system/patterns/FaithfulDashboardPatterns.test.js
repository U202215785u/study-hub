import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it } from 'vitest'
import CapsuleNavigation from './CapsuleNavigation.vue'
import DashboardModuleCard from './DashboardModuleCard.vue'
import GreetingBar from './GreetingBar.vue'
import WorkbenchFrame from './WorkbenchFrame.vue'

describe('Faithful dashboard patterns', () => {
  it('keeps the workbench landmarks and named slots in a stable frame', () => {
    const wrapper = mount(WorkbenchFrame, {
      slots: {
        navigation: '<nav data-test="navigation">导航</nav>',
        greeting: '<header data-test="greeting">问候</header>',
        default: '<article data-test="content">内容</article>',
        footer: '<footer data-test="footer">页脚</footer>',
      },
    })

    expect(wrapper.get('main').find('[data-test="greeting"]').exists()).toBe(true)
    expect(wrapper.get('main').find('[data-test="content"]').exists()).toBe(true)
    expect(wrapper.get('[data-test="navigation"]').exists()).toBe(true)
    expect(wrapper.get('[data-test="footer"]').exists()).toBe(true)
    expect(wrapper.get('.workbench-viewport').exists()).toBe(true)
    expect(wrapper.get('[data-dashboard-stage]').exists()).toBe(true)
  })

  it('exposes capsule navigation links and the three dashboard actions', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: ['/', '/wiki', '/kb', '/workflow', '/ddl', '/journal', '/brainstorm'].map((path) => ({ path, component: { template: '<div />' } })),
    })
    await router.push('/')
    await router.isReady()
    const wrapper = mount(CapsuleNavigation, { global: { plugins: [router] } })

    await wrapper.get('input').setValue('复盘')
    await wrapper.get('form').trigger('submit')
    await wrapper.get('.capsule-navigation__notice').trigger('click')
    await wrapper.get('[aria-label="编辑首页"]').trigger('click')

    expect(wrapper.findAll('nav a')).toHaveLength(8)
    expect(wrapper.get('.capsule-navigation__brand').attributes('target')).toBe('_blank')
    expect(wrapper.findAll('nav a').every((link) => link.attributes('target') === '_blank')).toBe(true)
    expect(wrapper.findAll('nav a').every((link) => link.attributes('rel') === 'noopener noreferrer')).toBe(true)
    expect(wrapper.emitted('search')).toEqual([['复盘']])
    expect(wrapper.emitted('notify')).toHaveLength(1)
    expect(wrapper.emitted('edit')).toHaveLength(1)
  })

  it('renders a primary heading and a live date-time region', () => {
    const wrapper = mount(GreetingBar)

    expect(wrapper.get('h1').text()).toMatch(/早上好|下午好|晚上好/)
    expect(wrapper.get('.greeting-bar__time strong').text()).toMatch(/\d+月\d+日\s+\d{2}:\d{2}/)
  })

  it.each([
    [{ loading: true, error: '请求失败', empty: true }, 'loading'],
    [{ error: '请求失败', empty: true }, 'error'],
    [{ empty: true }, 'empty'],
    [{}, 'content'],
  ])('keeps loading > error > empty > content precedence', (props, state) => {
    const wrapper = mount(DashboardModuleCard, {
      props: { title: '今日任务', ...props },
      slots: { default: '<div data-test="content">内容</div>' },
    })

    expect(wrapper.attributes('data-state')).toBe(state)
    expect(wrapper.find('[data-test="content"]').exists()).toBe(state === 'content')
    if (state === 'content') {
      expect(wrapper.get('.dashboard-module-card__content').attributes('data-card-inset')).toBe('16')
    }
  })
})
