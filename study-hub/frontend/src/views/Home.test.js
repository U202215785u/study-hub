import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  AutomationQueueWidget,
  BentoDashboardGrid,
  CalendarAgendaWidget,
  CreationWidget,
  DailyMemoryWidget,
  KnowledgeWidget,
  QuickCommandWidget,
  TodayFocusWidget,
  WorkHeatmapWidget,
  WorkflowWidget,
} from '@study-ui'
import { useSettingsStore } from '../stores/settings.js'
import Home from './Home.vue'

describe('Home dashboard composition', () => {
  let wrapper

  afterEach(() => wrapper?.unmount())

  it('composes nine Figma widgets and keeps existing API commands reachable', async () => {
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
    const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/kb', '/wiki', '/workflow', '/ddl', '/journal', '/brainstorm', '/settings', '/creator'].map((path) => ({ path, component: path === '/' ? Home : EmptyRoute })) })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { global: { plugins: [pinia, router] } })
    await flushPromises()

    expect(wrapper.findComponent(BentoDashboardGrid).exists()).toBe(true)
    for (const component of [WorkHeatmapWidget, CalendarAgendaWidget, TodayFocusWidget, AutomationQueueWidget, KnowledgeWidget, DailyMemoryWidget, QuickCommandWidget, CreationWidget, WorkflowWidget]) {
      expect(wrapper.findComponent(component).exists()).toBe(true)
    }
    expect(wrapper.findAll('[data-figma-node]')).toHaveLength(9)
    expect(wrapper.get('[role="search"]')).toBeTruthy()
    expect(wrapper.get('nav[aria-label="主导航"]')).toBeTruthy()

    await wrapper.get('[role="search"] input').setValue('原子设计')
    await wrapper.get('[role="search"]').trigger('submit')
    await wrapper.findComponent(KnowledgeWidget).vm.$emit('open', 'k1')
    await wrapper.findComponent(AutomationQueueWidget).vm.$emit('retry', 'q1')
    await flushPromises()

    expect(settings.apiPost).toHaveBeenCalledWith('/ai-search', { question: '原子设计' })
    expect(settings.apiGet).toHaveBeenCalledWith('/documents/k1')
    expect(settings.apiPost).toHaveBeenCalledWith('/automation/queue/retry/q1')
  })
})
