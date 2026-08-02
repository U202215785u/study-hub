import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  AutomationQueueWidget,
  CalendarWidget,
  CreationWidget,
  KnowledgeWidget,
  TaskWidget,
  UiDashboardGrid,
  WorkflowWidget,
} from '@study-ui'
import { useSettingsStore } from '../stores/settings.js'
import Home from './Home.vue'

describe('Home dashboard composition', () => {
  let wrapper

  afterEach(() => wrapper?.unmount())

  it('composes six widgets and keeps legacy API commands reachable', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => {
      if (path.startsWith('/documents?')) return [{ id: 'k1', title: '设计系统笔记', created_at: '2026-06-07', status: 'ready' }]
      if (path === '/documents/k1') return { id: 'k1', title: '设计系统笔记', content: '内容' }
      if (path === '/automation/queue/status') return { stats: { running: 1 }, tasks: [{ task_id: 'q1', title: '抖音视频解析', status: 'error', progress: 42 }] }
      if (path === '/review/list' || path.startsWith('/sop/suggestions')) return []
      if (path === '/categories') return []
      return {}
    })
    settings.apiPost = vi.fn(async (path) => path === '/ai-search' ? { answer: '搜索结果' } : {})
    settings.apiDelete = vi.fn(async () => ({}))
    settings.apiUpload = vi.fn(async () => ({}))

    const EmptyRoute = { template: '<div />' }
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: Home }, { path: '/kb', component: EmptyRoute }, { path: '/learning', component: EmptyRoute }, { path: '/creator', component: EmptyRoute }] })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { global: { plugins: [pinia, router] } })
    await flushPromises()

    expect(wrapper.findComponent(UiDashboardGrid).exists()).toBe(true)
    for (const component of [TaskWidget, CalendarWidget, AutomationQueueWidget, KnowledgeWidget, CreationWidget, WorkflowWidget]) {
      expect(wrapper.findComponent(component).exists()).toBe(true)
    }
    expect(wrapper.findAll('[data-home-search-primary="true"]')).toHaveLength(1)
    expect(wrapper.get('[role="search"]')).toBeTruthy()
    expect(wrapper.get('nav[aria-label="首页快捷入口"]')).toBeTruthy()

    await wrapper.get('[data-home-search-input] input').setValue('原子设计')
    await wrapper.get('[data-home-search-primary="true"]').trigger('click')
    await wrapper.findComponent(KnowledgeWidget).vm.$emit('open', 'k1')
    await wrapper.findComponent(AutomationQueueWidget).vm.$emit('retry', 'q1')
    await flushPromises()

    expect(settings.apiPost).toHaveBeenCalledWith('/ai-search', { question: '原子设计' })
    expect(settings.apiGet).toHaveBeenCalledWith('/documents/k1')
    expect(settings.apiPost).toHaveBeenCalledWith('/automation/queue/retry/q1')
  })
})
