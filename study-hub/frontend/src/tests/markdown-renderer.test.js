import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

describe('MarkdownRenderer reading controls', () => {
  beforeEach(() => {
    localStorage.clear()
    window.matchMedia = () => ({ matches: false })
  })

  it('uses the Kami paper theme even when the system prefers dark mode', () => {
    window.matchMedia = () => ({ matches: true })

    const wrapper = mount(MarkdownRenderer, {
      props: { content: 'Readable text' }
    })

    expect(wrapper.get('.markdown-content').attributes('data-theme')).toBe('parchment')
  })

  it('migrates a legacy dark theme preference back to the paper theme', () => {
    localStorage.setItem('markdown-theme', 'dark')

    const wrapper = mount(MarkdownRenderer, {
      props: { content: 'Readable text' }
    })

    expect(wrapper.get('.markdown-content').attributes('data-theme')).toBe('parchment')
  })

  it('restores the theme control and persists the next background', async () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: '# Test document' }
    })

    const themeButton = wrapper.get('[data-testid="markdown-theme-toggle"]')
    expect(themeButton.text()).toContain('米白')

    await themeButton.trigger('click')

    expect(wrapper.get('.markdown-content').attributes('data-theme')).toBe('kraft')
    expect(localStorage.getItem('markdown-theme')).toBe('kraft')
    expect(themeButton.text()).toContain('牛皮纸')
  })

  it('offers three font sizes and persists the selected size', async () => {
    const wrapper = mount(MarkdownRenderer, {
      props: { content: 'Readable text' }
    })

    const sizeButtons = wrapper.findAll('[data-testid^="markdown-font-"]')
    expect(sizeButtons.map(button => button.text())).toEqual(['小', '标准', '大'])
    expect(wrapper.get('[data-testid="markdown-font-standard"]').attributes('aria-pressed')).toBe('true')

    await wrapper.get('[data-testid="markdown-font-large"]').trigger('click')

    expect(wrapper.get('.markdown-content').attributes('data-font-size')).toBe('large')
    expect(localStorage.getItem('markdown-font-size')).toBe('large')
    expect(wrapper.get('[data-testid="markdown-font-large"]').attributes('aria-pressed')).toBe('true')
  })
})
