import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import WorkstationSearchPanel from './WorkstationSearchPanel.vue'

describe('WorkstationSearchPanel', () => {
  it('renders groups, exposes unavailable state, and emits only internal actions', async () => {
    const wrapper = mount(WorkstationSearchPanel, {
      props: {
        open: true,
        assistant: { enabled: false, label: '问一问 AI 助手', status: '暂未开放' },
        groups: [
          { id: 'knowledge', label: '文章与知识', status: 'ready', items: [{ id: 'd1', title: '笔记', summary: '摘要', navigation: { kind: 'document', document_id: 'd1' } }] },
          { id: 'records', label: '工作记录', status: 'unavailable', message: '工作记录暂时不可用', items: [] },
        ],
      },
    })
    await wrapper.get('.workstation-search-panel__item').trigger('click')
    await wrapper.get('.workstation-search-panel__error button').trigger('click')
    expect(wrapper.emitted('open-document')).toEqual([['d1']])
    expect(wrapper.emitted('retry')).toHaveLength(1)
    expect(wrapper.get('[aria-label="问一问 AI 助手"]').attributes('disabled')).toBeDefined()
  })
})
