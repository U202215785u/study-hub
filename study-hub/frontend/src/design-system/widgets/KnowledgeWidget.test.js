import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
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
})
