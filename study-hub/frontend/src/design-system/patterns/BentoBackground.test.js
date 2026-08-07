import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import BentoBackground from './BentoBackground.vue'

const componentPath = resolve(process.cwd(), 'src/design-system/patterns/BentoBackground.vue')

describe('BentoBackground', () => {
  it('defines decorative layers without interactive descendants', () => {
    const wrapper = mount(BentoBackground)
    const source = readFileSync(componentPath, 'utf8')

    expect(wrapper.attributes('aria-hidden')).toBe('true')
    expect(wrapper.classes()).toContain('bento-background')
    expect(wrapper.findAll('.bg-aurora__orb')).toHaveLength(3)
    expect(wrapper.find('.bg-aurora__ring').exists()).toBe(true)
    expect(wrapper.find('.bg-noise').exists()).toBe(true)
    expect(wrapper.find('button, a, input, [tabindex]').exists()).toBe(false)
    expect(source).toContain('class="bento-background"')
    expect(source).toContain('aria-hidden="true"')
    expect(source).toContain('class="bg-aurora"')
    expect(source).toContain('class="bg-aurora__orb bg-aurora__orb--lime"')
    expect(source).toContain('class="bg-aurora__orb bg-aurora__orb--violet"')
    expect(source).toContain('class="bg-aurora__orb bg-aurora__orb--blue"')
    expect(source).toContain('class="bg-aurora__ring"')
    expect(source).toContain('class="bg-noise"')
    expect(source).not.toMatch(/<(button|a|input)\b|tabindex=/)
  })

  it('marks the background static for edit mode', () => {
    const wrapper = mount(BentoBackground, { props: { static: true } })
    const source = readFileSync(componentPath, 'utf8')

    expect(wrapper.classes()).toContain('bento-background--static')
    expect(source).toContain(":class=\"{ 'bento-background--static': static }\"")
  })
})
