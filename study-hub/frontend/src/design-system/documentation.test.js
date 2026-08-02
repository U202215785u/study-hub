import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('Study UI documentation coverage', () => {
  it('documents every public component export', async () => {
    const [entry, status] = await Promise.all([
      readFile(resolve('src/design-system/index.js'), 'utf8'),
      readFile(resolve('docs/study-ui/component-status.md'), 'utf8'),
    ])
    const exports = [...entry.matchAll(/export \{ default as (Ui\w+|\w+Widget) \}/g)].map((match) => match[1])
    expect(exports.length).toBeGreaterThan(0)
    for (const name of exports) expect(status).toContain(`| ${name} |`)
  })
})
