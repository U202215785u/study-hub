import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../lib/gsap.js', () => ({
  gsap: {
    matchMedia: () => ({
      add: (_, callback) => callback?.(),
      revert: vi.fn(),
    }),
    context: (callback) => { callback?.(); return { revert: vi.fn() } },
    utils: { selector: (root) => (selector) => [...(root?.querySelectorAll?.(selector) || [])] },
    timeline: () => ({ from: vi.fn().mockReturnThis() }),
    fromTo: vi.fn(),
    to: vi.fn(),
  },
  Flip: { getState: vi.fn(), from: vi.fn() },
}))

import {
  AutomationQueueWidget,
  BentoDashboardGrid,
  CalendarAgendaWidget,
  CreationWidget,
  DailyMemoryWidget,
  KnowledgeWidget,
  MotionWrapper,
  QuickCommandWidget,
  TodayFocusWidget,
  WorkHeatmapWidget,
  WorkflowWidget,
} from '@study-ui'
import { useSettingsStore } from '../stores/settings.js'
import { toLocalDateKey } from '../composables/home/useHomeDashboardData.js'
import Home from './Home.vue'

describe('Home dashboard composition', () => {
  let wrapper

  afterEach(() => {
    wrapper?.unmount()
    vi.useRealTimers()
  })

  it('composes nine Figma widgets and keeps existing API commands reachable', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => {
      if (path.startsWith('/workstation/search?')) return { groups: [], assistant: { enabled: false, label: '问一问 AI 助手', status: '暂未开放' } }
      if (path === '/ddl/tasks') return [{ id: 'd1', title: '真实日程', plan_date: toLocalDateKey(new Date()), start_time: '09:00', end_time: '10:00', status: 'in_progress', updated_at: new Date().toISOString() }]
      if (path.startsWith('/documents?')) return [
        { id: 'k1', title: '设计系统笔记', created_at: '2026-06-07', status: 'ready' },
        { id: 'k2', title: '知识库交互规范', created_at: '2026-06-06', status: 'ready' },
      ]
      if (path === '/documents/k1') return { id: 'k1', title: '设计系统笔记', content: '内容' }
      if (path === '/automation/queue/status') return { stats: { running: 1 }, tasks: [{ task_id: 'q1', title: '抖音视频解析', status: 'error', progress: 42 }] }
      if (path === '/heatmap/catalog') return { default_style_id: 'grid', styles: [{ id: 'grid', name: '方格', status: 'available', settings_schema: { fields: [{ key: 'range_days', type: 'select', options: [90, 196, 365], default: 196 }, { key: 'sources', type: 'multiselect', options: ['tasks'], default: ['tasks'] }, { key: 'cell_shape', type: 'select', options: ['square'], default: 'square' }, { key: 'cell_radius', type: 'number', min: 0, max: 8, step: 1, default: 0 }] } }] }
      if (path === '/heatmap/preferences') return { style_id: 'grid', settings: { range_days: 196, sources: ['tasks'], cell_shape: 'square', cell_radius: 0 } }
      if (path.startsWith('/heatmap/data?')) return { cells: [{ date: '2026-08-03', count: 1, level: 1 }], grid: { rows: 7, columns: 28, slot_count: 196, leading_empty_slots: 0, trailing_empty_slots: 195 }, summary: { total: 1, active_days: 1 } }
      if (path === '/review/list' || path.startsWith('/sop/suggestions')) return []
      if (path === '/categories') return []
      return {}
    })
    settings.apiPost = vi.fn(async () => ({}))
    settings.apiDelete = vi.fn(async () => ({}))
    settings.apiUpload = vi.fn(async () => ({}))

    const EmptyRoute = { template: '<div />' }
    const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/kb', '/wiki', '/workflow', '/ddl', '/journal', '/brainstorm', '/settings', '/creator'].map((path) => ({ path, component: path === '/' ? Home : EmptyRoute })) })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { attachTo: document.body, global: { plugins: [pinia, router] } })
    await flushPromises()

    expect(wrapper.findComponent(BentoDashboardGrid).exists()).toBe(true)
    expect(wrapper.findAllComponents(MotionWrapper)).toHaveLength(9)
    for (const component of [WorkHeatmapWidget, CalendarAgendaWidget, TodayFocusWidget, AutomationQueueWidget, KnowledgeWidget, DailyMemoryWidget, QuickCommandWidget, CreationWidget, WorkflowWidget]) {
      expect(wrapper.findComponent(component).exists()).toBe(true)
    }
    expect(wrapper.findAll('[data-figma-node]')).toHaveLength(9)
    expect(wrapper.get('[data-module-id="work-heatmap"]').attributes('style')).toContain('grid-column-start: 1')
    expect(wrapper.get('[data-module-id="work-heatmap"]').attributes('style')).toContain('grid-row-start: 1')
    expect(wrapper.get('[data-home-motion="navigation"]')).toBeTruthy()
    expect(wrapper.get('[data-home-motion="greeting"]')).toBeTruthy()
    expect(wrapper.findAll('[data-home-motion="widget"]')).toHaveLength(9)
    expect(wrapper.findAll('[data-flip-id]')).toHaveLength(9)
    expect(wrapper.findAll('[data-flip-id]').map((node) => node.attributes('data-flip-id'))).toEqual(expect.arrayContaining([
      'work-heatmap', 'calendar-agenda', 'today-focus', 'automation-queue', 'knowledge', 'daily-memory', 'quick-command', 'creation-entry', 'quick-workflow',
    ]))
    expect(wrapper.findComponent(WorkHeatmapWidget).props('viewMode')).toBe('heatmap')
    await wrapper.findComponent(WorkHeatmapWidget).vm.$emit('update:viewMode', 'taskboard')
    await wrapper.vm.$nextTick()
    expect(wrapper.get('[data-taskboard-compact]').text()).toContain('Codex Taskboard')
    expect(wrapper.get('[role="search"]')).toBeTruthy()
    expect(wrapper.get('nav[aria-label="主导航"]')).toBeTruthy()
    expect(wrapper.findComponent(TodayFocusWidget).props('tasks')).toEqual([
      expect.objectContaining({ id: 'd1', title: '真实日程', time: '09:00 - 10:00', status: 'running' }),
    ])
    expect(wrapper.findComponent(CalendarAgendaWidget).props('agenda')).toEqual([
      expect.objectContaining({ id: 'd1', title: '真实日程', time: '09:00 - 10:00' }),
    ])

    await wrapper.findComponent(CalendarAgendaWidget).vm.$emit('select', '2026-08-03')
    await wrapper.vm.$nextTick()
    expect(wrapper.findComponent(CalendarAgendaWidget).props('days')).toEqual(expect.arrayContaining([
      expect.objectContaining({ date: '2026-08-03', selected: true }),
    ]))

    await wrapper.get('[role="search"] input').setValue('原子设计')
    await wrapper.get('[role="search"]').trigger('submit')
    await wrapper.findComponent(KnowledgeWidget).vm.$emit('open', 'k1')
    await wrapper.findComponent(KnowledgeWidget).vm.$emit('open-all')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/')
    expect(wrapper.get('[aria-labelledby="document-title"]').classes()).toContain('home-document-modal__panel')
    expect(wrapper.get('[aria-label="知识库"]')).toBeTruthy()
    expect(wrapper.findAll('[data-knowledge-drawer-id]')).toHaveLength(2)
    await wrapper.get('[aria-label="关闭知识库"]').trigger('click')
    await wrapper.findComponent(AutomationQueueWidget).vm.$emit('retry', 'q1')
    await flushPromises()

    expect(settings.apiGet).toHaveBeenCalledWith('/workstation/search?q=%E5%8E%9F%E5%AD%90%E8%AE%BE%E8%AE%A1')
    expect(settings.apiGet).toHaveBeenCalledWith('/documents/k1')
    expect(settings.apiPost).toHaveBeenCalledWith('/automation/queue/retry/q1')
  })

  it('keeps all selected-day tasks in category counts while capping visible tasks', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    const selectedDate = toLocalDateKey(new Date())
    const tasks = Array.from({ length: 6 }, (_, id) => ({
      id: `task-${id}`,
      title: `任务 ${id}`,
      plan_date: selectedDate,
      category_id: 'work',
      status: id === 5 ? 'done' : 'todo',
    }))
    settings.apiGet = vi.fn(async (path) => {
      if (path === '/ddl/tasks') return tasks
      if (path === '/ddl/categories') return [{ id: 'work', name: '工作' }]
      if (path === '/automation/queue/status') return { stats: {}, tasks: [] }
      if (path === '/review/list' || path.startsWith('/sop/suggestions') || path.startsWith('/documents?')) return []
      if (path === '/heatmap/catalog') return { default_style_id: 'grid', styles: [] }
      if (path === '/heatmap/preferences') return { style_id: 'grid', settings: { range_days: 196, sources: ['tasks'] } }
      if (path.startsWith('/heatmap/data?')) return { cells: [], grid: { rows: 7, columns: 28, slot_count: 196 }, summary: { total: 0, active_days: 0 } }
      return {}
    })
    settings.apiPost = vi.fn(async () => ({}))
    settings.apiDelete = vi.fn(async () => ({}))
    settings.apiUpload = vi.fn(async () => ({}))

    const EmptyRoute = { template: '<div />' }
    const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/kb', '/wiki', '/workflow', '/ddl', '/journal', '/brainstorm', '/settings', '/creator'].map((path) => ({ path, component: path === '/' ? Home : EmptyRoute })) })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { attachTo: document.body, global: { plugins: [pinia, router] } })
    await flushPromises()

    const todayFocus = wrapper.findComponent(TodayFocusWidget)
    expect(todayFocus.props('tasks')).toHaveLength(5)
    expect(todayFocus.props('categories')[0].tasks).toHaveLength(6)
  })

  it('keeps calendar, review, creation, workflow and automation entry actions reachable', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => {
      if (path === '/ddl/tasks' || path === '/review/list' || path === '/categories' || path.startsWith('/documents?') || path.startsWith('/sop/suggestions')) return []
      if (path === '/automation/queue/status') return { stats: {}, tasks: [] }
      return {}
    })
    settings.apiPost = vi.fn(async () => ({}))
    settings.apiDelete = vi.fn(async () => ({}))
    settings.apiUpload = vi.fn(async () => ({}))

    const EmptyRoute = { template: '<div />' }
    const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/kb', '/wiki', '/workflow', '/ddl', '/journal', '/brainstorm', '/settings', '/creator'].map((path) => ({ path, component: path === '/' ? Home : EmptyRoute })) })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { attachTo: document.body, global: { plugins: [pinia, router], stubs: { Transition: false } } })
    await flushPromises()

    const reviewTrigger = wrapper.findComponent(DailyMemoryWidget).get('button').element
    reviewTrigger.focus()
    reviewTrigger.click()
    await flushPromises()
    expect(wrapper.get('[aria-labelledby="review-title"]')).toBeTruthy()
    expect(document.activeElement).toBe(wrapper.get('[aria-labelledby="review-title"] button').element)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await new Promise((resolve) => setTimeout(resolve, 220))
    await flushPromises()
    expect(wrapper.find('[aria-labelledby="review-title"]').exists()).toBe(false)
    expect(document.activeElement).toBe(reviewTrigger)

    await wrapper.findComponent(CalendarAgendaWidget).vm.$emit('open', 'd1')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/ddl')
    await router.push('/')
    await flushPromises()

    const calendar = wrapper.findComponent(CalendarAgendaWidget)
    const currentDate = toLocalDateKey(new Date())
    const previousDateButton = calendar.findAll('button[data-date]').find((button) => button.attributes('data-date') !== currentDate)
    await previousDateButton.trigger('click')
    expect(calendar.get('button.selected').attributes('data-date')).not.toBe(currentDate)
    await calendar.get('.calendar-agenda__today').trigger('click')
    expect(calendar.get('button.selected').attributes('data-date')).toBe(currentDate)

    const workflow = wrapper.findComponent(WorkflowWidget)
    await workflow.get('input').setValue('https://example.com/workflow-source')
    await workflow.get('input').trigger('keydown.enter')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/workflow')
    expect(router.currentRoute.value.query.url).toBe('https://example.com/workflow-source')
    await router.push('/')
    await flushPromises()

    const queue = wrapper.findComponent(AutomationQueueWidget)
    await queue.get('input[data-queue-input]').setValue('https://example.com/queue-source')
    await queue.get('[data-queue-create]').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.get('[aria-labelledby="automation-title"] input').element.value).toBe('https://example.com/queue-source')

    await wrapper.findComponent(CreationWidget).get('[data-creation-action="drafts"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/creator')
    await router.push('/')
    await flushPromises()

    await wrapper.findComponent(CreationWidget).get('[data-creation-action="publish"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/creator')
    await router.push('/')
    await flushPromises()

    await wrapper.findComponent(CreationWidget).vm.$emit('open', 'missing')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/creator')
    await router.push('/')
    await flushPromises()

    await wrapper.findComponent(WorkflowWidget).vm.$emit('run', 'collect')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/workflow')
    await router.push('/')
    await flushPromises()

    await wrapper.findComponent(AutomationQueueWidget).vm.$emit('create')
    await wrapper.vm.$nextTick()
    await wrapper.get('[aria-labelledby="automation-title"] input').setValue('https://example.com/video')
    expect(wrapper.get('[aria-labelledby="automation-title"] input[type="checkbox"]')).toBeTruthy()
    await wrapper.get('[aria-labelledby="automation-title"] input[type="checkbox"]').setValue(true)
    await wrapper.get('[aria-labelledby="automation-title"] footer button').trigger('click')
    await flushPromises()
    expect(settings.apiPost).toHaveBeenCalledWith('/automation/queue', {
      module_id: 'douyin-summary',
      input: 'https://example.com/video',
      include_tutorial: true,
    })
  })

  it('confirms before restoring the default dashboard layout', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => {
      if (path === '/automation/queue/status') return { stats: {}, tasks: [] }
      return []
    })
    settings.apiPost = vi.fn(async () => ({}))
    settings.apiDelete = vi.fn(async () => ({}))
    settings.apiUpload = vi.fn(async () => ({}))

    const EmptyRoute = { template: '<div />' }
    const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/creator'].map((path) => ({ path, component: path === '/' ? Home : EmptyRoute })) })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { attachTo: document.body, global: { plugins: [pinia, router] } })
    await flushPromises()

    const confirmSpy = vi.spyOn(window, 'confirm')
    await wrapper.get('[aria-label="编辑首页"]').trigger('click')
    await wrapper.get('[data-hide-id="knowledge"]').trigger('click')

    confirmSpy.mockReturnValue(false)
    await wrapper.get('[data-editor-restore]').trigger('click')
    expect(confirmSpy).toHaveBeenCalledWith('将恢复默认布局并丢弃当前自定义布局，是否继续？')
    expect(wrapper.find('[data-editor-module-id="knowledge"] [data-show-id="knowledge"]').exists()).toBe(true)

    confirmSpy.mockReturnValue(true)
    await wrapper.get('[data-editor-restore]').trigger('click')
    expect(wrapper.find('[data-editor-restore]').exists()).toBe(false)
    confirmSpy.mockRestore()
  })

  it('keeps the automation dialog open when queue submission fails', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => {
      if (path === '/automation/queue/status') return { stats: {}, tasks: [] }
      return []
    })
    settings.apiPost = vi.fn().mockRejectedValue(new Error('server unavailable'))
    settings.apiDelete = vi.fn().mockResolvedValue({})
    settings.apiUpload = vi.fn().mockResolvedValue({})

    const EmptyRoute = { template: '<div />' }
    const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/workflow', '/creator'].map((path) => ({ path, component: path === '/' ? Home : EmptyRoute })) })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { attachTo: document.body, global: { plugins: [pinia, router] } })
    await flushPromises()

    await wrapper.findComponent(AutomationQueueWidget).vm.$emit('create', 'https://example.com/video')
    await wrapper.vm.$nextTick()
    await wrapper.get('[aria-labelledby="automation-title"] footer button').trigger('click')
    await flushPromises()

    expect(wrapper.get('[aria-labelledby="automation-title"]')).toBeTruthy()
    expect(wrapper.get('.home-toast[data-error="true"]')).toBeTruthy()
  })

  it('closes the queue from the outside while keeping clicks inside the drawer', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => {
      if (path === '/automation/queue/status') return { stats: {}, tasks: [] }
      return []
    })
    settings.apiPost = vi.fn(async () => ({}))
    settings.apiDelete = vi.fn(async () => ({}))
    settings.apiUpload = vi.fn(async () => ({}))

    const EmptyRoute = { template: '<div />' }
    const router = createRouter({ history: createMemoryHistory(), routes: ['/', '/workflow'].map((path) => ({ path, component: path === '/' ? Home : EmptyRoute })) })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { attachTo: document.body, global: { plugins: [pinia, router] } })
    await flushPromises()

    await wrapper.findComponent(AutomationQueueWidget).vm.$emit('open')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.home-drawer').exists()).toBe(true)

    await wrapper.get('.home-drawer').trigger('click')
    expect(wrapper.find('.home-drawer').exists()).toBe(true)

    await wrapper.get('.home-drawer-backdrop').trigger('click')
    expect(wrapper.find('.home-drawer').exists()).toBe(false)
  })

  it('shows one successful feedback when a queued task first completes', async () => {
    vi.useFakeTimers()
    let queueReads = 0
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => {
      if (path === '/automation/queue/status') {
        queueReads += 1
        return { tasks: [{ task_id: 'q1', title: '解析任务', status: queueReads === 1 ? 'running' : 'done' }] }
      }
      if (path === '/ddl/tasks' || path === '/review/list' || path === '/categories' || path.startsWith('/documents?') || path.startsWith('/sop/suggestions')) return []
      if (path === '/heatmap/catalog') return { default_style_id: 'grid', styles: [] }
      if (path === '/heatmap/preferences') return { style_id: 'grid', settings: {} }
      if (path.startsWith('/heatmap/data?')) return { cells: [] }
      return {}
    })
    settings.apiPost = vi.fn(async () => ({}))
    settings.apiDelete = vi.fn(async () => ({}))
    settings.apiUpload = vi.fn(async () => ({}))

    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: Home }] })
    await router.push('/')
    await router.isReady()
    wrapper = mount(Home, { attachTo: document.body, global: { plugins: [pinia, router] } })
    await flushPromises()
    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()

    expect(wrapper.get('.home-toast').text()).toContain('解析任务已完成')
  })
})
