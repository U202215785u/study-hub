import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DocumentReader from './DocumentReader.vue'

describe('DocumentReader', () => {
  it('shows summary and ready tutorial tabs without requesting another API', async () => {
    const wrapper = mount(DocumentReader, {
      props: {
        summaryMarkdown: '# Summary',
        tutorialMarkdown: '# Tutorial',
        tutorialStatus: 'ready',
        tutorialReason: '',
      },
    })

    expect(wrapper.get('[role="tablist"]')).toBeTruthy()
    expect(wrapper.findAll('[role="tab"]')).toHaveLength(2)
    expect(wrapper.text()).toContain('Summary')

    await wrapper.get('[role="tab"]:nth-child(2)').trigger('click')

    expect(wrapper.text()).toContain('Tutorial')
    expect(wrapper.emitted('active-content').at(-1)).toEqual(['# Tutorial'])
  })

  it('hides tutorial tab when it was not requested', () => {
    const wrapper = mount(DocumentReader, {
      props: {
        summaryMarkdown: '# Summary',
        tutorialMarkdown: '',
        tutorialStatus: 'not_requested',
        tutorialReason: '',
      },
    })

    expect(wrapper.findAll('[role="tab"]')).toHaveLength(1)
    expect(wrapper.text()).not.toContain('图文教程')
  })

  it('shows an unavailable reason inside the tutorial tab', async () => {
    const wrapper = mount(DocumentReader, {
      props: {
        summaryMarkdown: '# Summary',
        tutorialMarkdown: '',
        tutorialStatus: 'unavailable',
        tutorialReason: '视频无法下载',
      },
    })

    await wrapper.get('[role="tab"]:nth-child(2)').trigger('click')

    expect(wrapper.text()).toContain('视频无法下载')
  })
})
