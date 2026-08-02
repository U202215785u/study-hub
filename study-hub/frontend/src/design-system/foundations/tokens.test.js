import { describe, expect, it } from 'vitest'
import { semanticTokens } from './tokens'

describe('Study UI tokens', () => {
  it('keeps action, status and content colors separate', () => {
    expect(semanticTokens.color.actionPrimary).toBe('--ui-color-action')
    expect(semanticTokens.color.contentPurple).toBe('--ui-color-content-purple')
    expect(semanticTokens.color.danger).not.toBe(semanticTokens.color.contentOrange)
  })

  it('uses a four-pixel spacing grid', () => {
    expect(semanticTokens.space).toEqual([
      '--ui-space-0',
      '--ui-space-1',
      '--ui-space-2',
      '--ui-space-3',
      '--ui-space-4',
      '--ui-space-5',
      '--ui-space-6',
      '--ui-space-8',
      '--ui-space-10',
      '--ui-space-12',
    ])
  })
})
