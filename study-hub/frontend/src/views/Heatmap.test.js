import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useSettingsStore } from '../stores/settings.js'
import Heatmap from './Heatmap.vue'

const catalog = {
  default_style_id: 'grid',
  styles: [
    { id: 'grid', name: '方格', status: 'available', settings_schema: { fields: [
      { key: 'range_days', type: 'select', options: [90, 196, 365], default: 196 },
      { key: 'sources', type: 'multiselect', options: ['tasks', 'documents', 'queue'], default: ['tasks', 'documents', 'queue'] },
      { key: 'cell_shape', type: 'select', options: ['square', 'rounded'], default: 'square' },
      { key: 'cell_radius', type: 'number', min: 0, max: 8, step: 1, default: 0, depends_on: { key: 'cell_shape', equals: 'rounded' } },
    ] } },
    { id: 'calendar', name: '日历', status: 'reserved', settings_schema: null },
  ],
}

describe('Heatmap view', () => {
  let wrapper

  afterEach(() => wrapper?.unmount())

  it('renders catalog-backed Chinese labels and keeps reserved styles disabled', async () => {
    const pinia = createPinia()
    const settings = useSettingsStore(pinia)
    settings.apiGet = vi.fn(async (path) => path === '/heatmap/catalog' ? catalog : path === '/heatmap/preferences' ? { style_id: 'grid', settings: {} } : { cells: [], grid: { columns: 28, slot_count: 196, leading_empty_slots: 0 } })
    settings.apiPut = vi.fn(async () => ({ style_id: 'grid', settings: {} }))
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div />' } }, { path: '/heatmap', component: Heatmap }] })
    await router.push('/heatmap?view=heatmap')
    await router.isReady()

    wrapper = mount(Heatmap, { global: { plugins: [pinia, router] } })
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(settings.apiGet).toHaveBeenCalledWith('/heatmap/catalog')
    expect(settings.apiGet).toHaveBeenCalledWith('/heatmap/preferences')
    expect(settings.apiGet).toHaveBeenCalledWith(expect.stringContaining('/heatmap/data?'))
    expect(wrapper.text()).toContain('显示范围')
    expect(wrapper.text()).not.toContain('range_days')
    expect(wrapper.get('.styles button:nth-child(2)').attributes('disabled')).toBeDefined()
  })
})
