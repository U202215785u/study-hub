import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const source = readFileSync(resolve(process.cwd(), 'src/design-system/patterns/DashboardModuleCard.vue'), 'utf8')

describe('DashboardModuleCard transparency contract', () => {
  it('keeps a solid fallback and limits glass enhancement to supported browsers', () => {
    expect(source).toContain('background: #1b1d1a')
    expect(source).toContain('@supports (backdrop-filter: blur(1px))')
    expect(source).toContain('backdrop-filter: blur(12px)')
    expect(source).toContain('-webkit-backdrop-filter: blur(12px)')
  })

  it('handles reduced transparency independently from reduced motion', () => {
    expect(source).toContain('@media (prefers-reduced-transparency: reduce)')
    expect(source).toContain('backdrop-filter: none')
  })
})
