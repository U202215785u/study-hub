import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import AppConfirm from '../components/AppConfirm.vue'
import { useConfirm } from '../composables/useConfirm.js'

const confirmApi = useConfirm()

async function cancelActiveConfirm() {
  if (confirmApi.visible.value) {
    confirmApi.onCancel()
    await nextTick()
  }
}

describe('global confirmation flow', () => {
  beforeEach(cancelActiveConfirm)
  afterEach(cancelActiveConfirm)

  it('settles concurrent calls in request order', async () => {
    const first = confirmApi.confirm({ title: 'First' })
    const second = confirmApi.confirm({ title: 'Second' })

    expect(confirmApi.title.value).toBe('First')
    confirmApi.onConfirm()
    await expect(first).resolves.toBe(true)

    expect(confirmApi.visible.value).toBe(true)
    expect(confirmApi.title.value).toBe('Second')
    confirmApi.onCancel()
    await expect(second).resolves.toBe(false)
    expect(confirmApi.visible.value).toBe(false)
  })

  it('focuses the dialog, resolves on Escape, and restores focus', async () => {
    const opener = document.createElement('button')
    document.body.appendChild(opener)
    opener.focus()

    const wrapper = mount(AppConfirm, { attachTo: document.body })
    const result = confirmApi.confirm({ title: 'Keyboard check' })
    await nextTick()

    expect(document.activeElement?.textContent?.trim()).toBe('取消')
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await expect(result).resolves.toBe(false)
    await nextTick()
    expect(document.activeElement).toBe(opener)

    wrapper.unmount()
    opener.remove()
  })

  it('resolves false when the backdrop is clicked', async () => {
    const wrapper = mount(AppConfirm, { attachTo: document.body })
    const result = confirmApi.confirm({ message: 'Backdrop check' })
    await nextTick()

    document.querySelector('[data-test="confirm-backdrop"]').click()
    await expect(result).resolves.toBe(false)

    wrapper.unmount()
  })
})
