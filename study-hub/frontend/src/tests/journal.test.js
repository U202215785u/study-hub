import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import JournalView from '../views/JournalView.vue'

const {
  confirmMock,
  toastErrorMock,
  apiGetMock,
  apiPostMock,
  apiDeleteMock
} = vi.hoisted(() => ({
  confirmMock: vi.fn(),
  toastErrorMock: vi.fn(),
  apiGetMock: vi.fn(),
  apiPostMock: vi.fn(),
  apiDeleteMock: vi.fn()
}))

vi.mock('../composables/useConfirm.js', () => ({
  useConfirm: () => ({ confirm: confirmMock })
}))

vi.mock('../composables/useToast.js', () => ({
  toast: { error: toastErrorMock }
}))

vi.mock('../stores/settings.js', () => ({
  useSettingsStore: () => ({
    apiGet: apiGetMock,
    apiPost: apiPostMock,
    apiDelete: apiDeleteMock
  })
}))

function mountJournal() {
  return mount(JournalView, {
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' }
      }
    }
  })
}

describe('Journal unsaved-change protection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    confirmMock.mockResolvedValue(true)
    apiGetMock.mockImplementation(async (path) => {
      if (path === '/journal/stats') return { total: 0, streak: 0 }
      return []
    })
    apiPostMock.mockResolvedValue({ error: 'offline' })
  })

  it('mounts with the shared toast and confirmation services', async () => {
    const wrapper = mountJournal()
    await flushPromises()
    expect(wrapper.find('textarea').exists()).toBe(true)
    wrapper.unmount()
  })

  it('keeps the draft and selected date when save-before-switch fails', async () => {
    const wrapper = mountJournal()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('unsaved draft')
    const heading = wrapper.findAll('div').find(node => node.classes().includes('text-[42px]'))
    const originalHeading = heading.text()
    const dates = wrapper.findAll('div').filter(node => node.classes().includes('aspect-square'))
    const target = dates.find(node => node.text() !== String(Number(originalHeading)))

    await target.trigger('click')
    await flushPromises()

    expect(apiPostMock).toHaveBeenCalledOnce()
    expect(toastErrorMock).toHaveBeenCalledWith('保存失败：offline')
    expect(wrapper.find('textarea').element.value).toBe('unsaved draft')
    expect(heading.text()).toBe(originalHeading)
    wrapper.unmount()
  })

  it('protects drafts when switching through the timeline', async () => {
    const today = new Date().toISOString().split('T')[0]
    const day = Number(today.slice(-2))
    const targetDate = `${today.slice(0, -2)}${String(day === 1 ? 2 : day - 1).padStart(2, '0')}`
    apiGetMock.mockImplementation(async (path) => {
      if (path === '/journal/stats') return { total: 2, streak: 1 }
      if (path.startsWith('/journal/entries?')) {
        return [
          { id: 1, date: today, content: 'saved today', mood: 'neutral', tags: [] },
          { id: 2, date: targetDate, content: 'old entry', mood: 'happy', tags: [] }
        ]
      }
      return []
    })

    const wrapper = mountJournal()
    await flushPromises()
    await wrapper.find('textarea').setValue('timeline draft')
    const timelineTarget = wrapper.findAll('div').find(node =>
      node.classes().includes('cursor-pointer') && node.text().includes('old entry')
    )

    await timelineTarget.trigger('click')
    await flushPromises()

    expect(confirmMock).toHaveBeenCalledOnce()
    expect(apiPostMock).toHaveBeenCalledOnce()
    expect(wrapper.find('textarea').element.value).toBe('timeline draft')
    wrapper.unmount()
  })

  it('keeps the draft when the save request throws', async () => {
    apiPostMock.mockRejectedValue(new Error('network down'))
    const wrapper = mountJournal()
    await flushPromises()

    await wrapper.find('textarea').setValue('offline draft')
    const dates = wrapper.findAll('div').filter(node => node.classes().includes('aspect-square'))
    await dates[0].trigger('click')
    await flushPromises()

    expect(toastErrorMock).toHaveBeenCalledWith('保存失败：network down')
    expect(wrapper.find('textarea').element.value).toBe('offline draft')
    wrapper.unmount()
  })
})
