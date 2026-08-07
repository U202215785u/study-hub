import { describe, expect, it, vi } from 'vitest'
import { playHomeEntrance } from './useHomeEntrance.js'

describe('playHomeEntrance', () => {
  it('animates navigation and greeting without competing with widget motion', () => {
    const targets = {
      '[data-home-motion="navigation"]': ['nav'],
      '[data-home-motion="greeting"]': ['greeting'],
      '[data-home-motion="widget"]': ['one', 'two'],
    }
    const timeline = { from: vi.fn().mockReturnThis() }
    const gsap = { utils: { selector: () => (selector) => targets[selector] }, timeline: vi.fn(() => timeline) }

    const result = playHomeEntrance({ gsap, root: {}, duration: 0.18 })

    expect(result).toBe(timeline)
    expect(gsap.timeline).toHaveBeenCalledOnce()
    expect(timeline.from.mock.calls.map(([target]) => target)).toEqual([['nav'], ['greeting']])
  })
})
