import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CreationWidget from './CreationWidget.vue'

describe('CreationWidget', () => {
  it('emits the creation id when opened', async () => {
    const item = Object.freeze({ id: 'c1', title: '文章模板', thumbnail: '', kind: 'article' })
    const wrapper = mount(CreationWidget, { props: { items: [item] } })
    await wrapper.get('[data-creation-id="c1"]').trigger('click')
    expect(wrapper.emitted('open')).toEqual([['c1']])
  })
})
