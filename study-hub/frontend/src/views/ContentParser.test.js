import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import ContentParser from './ContentParser.vue'

const apiGet = vi.fn()

vi.mock('../stores/settings.js', () => ({
  useSettingsStore: () => ({ apiGet }),
}))

vi.mock('../composables/useContentParser.js', () => ({
  useContentParser: () => ({
    batch: ref(null),
    tasks: ref([]),
    refreshTasks: vi.fn().mockResolvedValue([]),
    preflight: vi.fn(),
    confirm: vi.fn(),
  }),
}))

describe('ContentParser', () => {
  it('shows an ASR error code when opening a fallback document', async () => {
    apiGet
      .mockResolvedValueOnce({ items: [{ id: 7, title: 'Fallback video', source: 'douyin-summary' }], counts: {} })
      .mockResolvedValueOnce({
        id: 7,
        title: 'Fallback video',
        content: '# Fallback video',
        asr_status: 'fallback',
        asr_error: '火山引擎 ASR 失败: 200',
      })

    const wrapper = mount(ContentParser, { global: { stubs: ['router-link'] } })
    await wrapper.findAll('aside button')[1].trigger('click')
    await Promise.resolve()
    await wrapper.find('article button').trigger('click')
    await Promise.resolve()

    expect(wrapper.text()).toContain('PARSER-ASR-2001')
    expect(wrapper.text()).toContain('火山引擎 ASR 失败: 200')
  })
})
