import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import KnowledgeWidget from './KnowledgeWidget.vue'

describe('KnowledgeWidget', () => {
  it('emits the document id when opened', async () => {
    const item = Object.freeze({ id: 'k1', title: '设计系统笔记', meta: '今天', status: 'ready' })
    const wrapper = mount(KnowledgeWidget, { props: { items: [item] } })
    await wrapper.get('[data-knowledge-id="k1"]').trigger('click')
    expect(wrapper.emitted('open')).toEqual([['k1']])
  })

  it('keeps the knowledge structure visible when no documents exist', () => {
    const wrapper = mount(KnowledgeWidget)
    expect(wrapper.get('h2').text()).toBe('知识库')
  })

  it('emits a separate action for opening the full knowledge base', async () => {
    const wrapper = mount(KnowledgeWidget)

    await wrapper.get('[data-knowledge-more]').trigger('click')

    expect(wrapper.get('[data-knowledge-more]').text()).toBe('展开全部')
    expect(wrapper.emitted('open-all')).toEqual([[]])
  })

  it('keeps copy and destructive actions separate from opening the document', async () => {
    const item = Object.freeze({ id: 'k1', title: '设计系统笔记', status: 'error' })
    const wrapper = mount(KnowledgeWidget, { props: { items: [item] } })

    await wrapper.get('[data-copy-id="k1"]').trigger('click')
    await wrapper.get('[data-remove-id="k1"]').trigger('click')

    expect(wrapper.emitted('copy')).toEqual([['k1']])
    expect(wrapper.emitted('remove')).toEqual([['k1']])
    expect(wrapper.emitted('open')).toBeUndefined()
  })

  it('uses the shared compact header and inset row surface', () => {
    const wrapper = mount(KnowledgeWidget, { props: { items: [{ id: 'k1', title: '设计系统' }] } })

    expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
    expect(wrapper.findComponent(UiInsetSurface).exists()).toBe(true)
  })
})
