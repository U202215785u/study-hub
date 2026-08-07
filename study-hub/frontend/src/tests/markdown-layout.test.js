import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const styles = readFileSync(resolve(process.cwd(), 'src/assets/main.css'), 'utf8')

describe('Markdown reading surface layout', () => {
  it('lets the paper surface span the full reader width', () => {
    expect(styles).toMatch(/\.markdown-content\s*\{[\s\S]*?max-width:\s*none;[\s\S]*?width:\s*100%;/)
  })
})
