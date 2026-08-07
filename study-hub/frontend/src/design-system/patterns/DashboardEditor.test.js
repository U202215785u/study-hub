import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { DEFAULT_DASHBOARD_LAYOUT } from '../layout/dashboardLayout.js'
import DashboardEditor from './DashboardEditor.vue'

describe('DashboardEditor', () => {
  it('exposes hide, save, cancel and restore controls', async () => {
    const wrapper = mount(DashboardEditor, { props: { widgets: DEFAULT_DASHBOARD_LAYOUT.widgets } })
    await wrapper.get('[data-hide-id="knowledge"]').trigger('click')
    await wrapper.get('[data-editor-save]').trigger('click')
    await wrapper.get('[data-editor-cancel]').trigger('click')
    await wrapper.get('[data-editor-restore]').trigger('click')
    expect(wrapper.emitted('hide')).toEqual([['knowledge']])
    expect(wrapper.emitted('save')).toHaveLength(1)
    expect(wrapper.emitted('cancel')).toHaveLength(1)
    expect(wrapper.emitted('restore')).toHaveLength(1)
  })

  it('shows a disabled undo control until the draft has a reversible change', async () => {
    const wrapper = mount(DashboardEditor, { props: { widgets: DEFAULT_DASHBOARD_LAYOUT.widgets, canUndo: false } })
    expect(wrapper.get('[data-editor-undo]').attributes('disabled')).toBeDefined()
    await wrapper.setProps({ canUndo: true })
    await wrapper.get('[data-editor-undo]').trigger('click')
    expect(wrapper.emitted('undo')).toHaveLength(1)
  })
})
