import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import DouyinImportPanel from '../components/DouyinImportPanel.vue'
import DouyinCookieControl from '../components/DouyinCookieControl.vue'


describe('Douyin import preflight', () => {
  it('preflights input and confirms selected ready items', async () => {
    const api = {
      apiPost: vi.fn(async (path) => path.endsWith('/preflight')
        ? { batch_id: 'batch-1', status: 'ready', items: [
          { item_id: 'ready', title: 'Ready', status: 'ready', content_sources: ['subtitle'] },
          { item_id: 'duplicate', title: 'Duplicate', status: 'duplicate', content_sources: [] },
          { item_id: 'blocked', title: 'Blocked', status: 'blocked', error_message: 'Cookie required', content_sources: [] },
          { item_id: 'file', title: 'Needs file', status: 'needs_local_file', content_sources: [] },
          { item_id: 'failed', title: 'Failed', status: 'failed', error_message: 'Unavailable', content_sources: [] },
        ] }
        : { task_ids: ['task-1'] }),
      apiUpload: vi.fn(),
    }
    const wrapper = mount(DouyinImportPanel, { props: { api } })
    await wrapper.get('textarea').setValue('https://v.douyin.com/example')
    await wrapper.get('[data-test="preflight"]').trigger('click')

    expect(api.apiPost).toHaveBeenCalledWith('/automation/douyin/preflight', { input: 'https://v.douyin.com/example' })
    expect(wrapper.text()).toContain('Ready')
    expect(wrapper.text()).toContain('Duplicate')
    expect(wrapper.text()).toContain('Needs file')
    await wrapper.get('[data-test="confirm-ready"]').trigger('click')
    expect(api.apiPost).toHaveBeenLastCalledWith('/automation/douyin/confirm', {
      batch_id: 'batch-1', item_ids: ['ready'],
    })
  })

  it('uploads recovery media to the same item', async () => {
    const api = {
      apiPost: vi.fn(async () => ({ batch_id: 'batch-2', status: 'blocked', items: [
        { item_id: 'file', title: 'Needs file', status: 'needs_local_file', content_sources: [] },
      ] })),
      apiUpload: vi.fn(async () => ({ item_id: 'file', title: 'Needs file', status: 'ready', content_sources: ['local_file'] })),
    }
    const wrapper = mount(DouyinImportPanel, { props: { api } })
    await wrapper.get('textarea').setValue('https://v.douyin.com/example')
    await wrapper.get('[data-test="preflight"]').trigger('click')
    const file = new File(['video'], 'video.mp4', { type: 'video/mp4' })
    Object.defineProperty(wrapper.get('input[type="file"]').element, 'files', { value: [file] })
    await wrapper.get('input[type="file"]').trigger('change')
    expect(api.apiUpload.mock.calls[0][0]).toBe('/automation/douyin/items/file/local-file')
  })
})


describe('Douyin Cookie control', () => {
  it('shows status but never renders the saved Cookie', async () => {
    const secret = 'sessionid=secret-value'
    const api = {
      apiGet: vi.fn(async () => ({ configured: true, updated_at: '2026-07-29' })),
      apiPut: vi.fn(async () => ({ configured: true, updated_at: '2026-07-29' })),
      apiDelete: vi.fn(),
    }
    const wrapper = mount(DouyinCookieControl, { props: { api } })
    await wrapper.get('input').setValue(secret)
    await wrapper.get('[data-test="save-cookie"]').trigger('click')
    expect(api.apiPut).toHaveBeenCalledWith('/automation/douyin/cookie', { cookie: secret })
    expect(wrapper.text()).not.toContain(secret)
    expect(wrapper.get('input').element.value).toBe('')
  })
})
