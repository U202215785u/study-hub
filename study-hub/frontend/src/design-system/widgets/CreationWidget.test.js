import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import UiPillButton from '../components/general/UiPillButton.vue'
import CreationWidget from './CreationWidget.vue'

describe('CreationWidget', () => {
  it('emits the creation id when opened', async () => {
    const item = Object.freeze({ id: 'c1', title: '文章模板', thumbnail: '', kind: 'article' })
    const wrapper = mount(CreationWidget, { props: { items: [item] } })
    await wrapper.get('[data-creation-id="c1"]').trigger('click')
    expect(wrapper.emitted('open')).toEqual([['c1']])
    expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
    expect(wrapper.findComponent(UiInsetSurface).exists()).toBe(true)
    expect(wrapper.findAllComponents(UiPillButton)).toHaveLength(2)
  })

  it('emits an open action for the draft and publish entry buttons', async () => {
    const wrapper = mount(CreationWidget, { props: { items: [{ id: 'c1', title: 'Article', thumbnail: '', kind: 'article' }] } })

    await wrapper.get('[data-creation-action="drafts"]').trigger('click')
    await wrapper.get('[data-creation-action="publish"]').trigger('click')

    expect(wrapper.emitted('open')).toEqual([['drafts'], ['publish']])
  })
})
