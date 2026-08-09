import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
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

describe('ContentParser Markdown documents', () => {
  beforeEach(() => {
    apiGet.mockReset()
  })

  it('renders a library document through the shared Markdown reader', async () => {
    apiGet.mockResolvedValue({
      id: 42,
      title: 'Markdown document',
      content: '# Markdown heading\n\n**Bold text**\n\n- list item\n\n`inline()`\n\n| Name | Value |\n| --- | --- |\n| renderer | shared |',
    })

    const wrapper = mount(ContentParser, {
      global: {
        stubs: {
          'router-link': true,
          ContentImportWorkspace: true,
          ContentLibrary: {
            template: '<button data-testid="open-document" @click="$emit(\'open\', 42)">Open</button>',
          },
        },
      },
    })

    await wrapper.findAll('aside button')[1].trigger('click')
    await wrapper.get('[data-testid="open-document"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('.markdown-content h1').text()).toBe('Markdown heading')
    expect(wrapper.get('.markdown-content strong').text()).toBe('Bold text')
    expect(wrapper.get('.markdown-content li').text()).toBe('list item')
    expect(wrapper.get('.markdown-content code').text()).toBe('inline()')
    expect(wrapper.get('.markdown-content table').text()).toContain('renderer')
    expect(wrapper.find('pre').exists()).toBe(false)
  })
})
