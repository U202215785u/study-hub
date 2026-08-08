import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import DDL from './DDL.vue'

describe('DDL create intent', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('opens a daily task with the requested category and date', async () => {
    vi.stubGlobal('fetch', vi.fn((url) => Promise.resolve({ ok: true, json: async () => String(url).includes('/ddl/categories') ? [{ id: 7, name: '深度工作' }] : [] })))
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/ddl', component: DDL }] })
    await router.push('/ddl?create=1&categoryId=7&planDate=2026-08-08')
    await router.isReady()
    const wrapper = mount(DDL, { global: { plugins: [createPinia(), router] } })
    await flushPromises()
    expect(wrapper.get('[data-testid="task-category"]').element.value).toBe('7')
    expect(wrapper.get('[data-testid="task-plan-date"]').element.value).toBe('2026-08-08')
  })
})
