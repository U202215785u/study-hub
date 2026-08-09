import { describe, expect, it, vi } from 'vitest'
import { createDashboardFlip } from './useDashboardFlip.js'

describe('createDashboardFlip', () => {
  it('captures before mutation and plays after the DOM update', async () => {
    const calls = []
    const state = { id: 'state' }
    const Flip = {
      getState: vi.fn(() => { calls.push('getState'); return state }),
      from: vi.fn(() => { calls.push('from'); return { kill: vi.fn() } }),
    }
    const nextTick = vi.fn(async () => { calls.push('nextTick') })
    const getTargets = vi.fn(() => { calls.push('getTargets'); return ['card'] })
    const mutate = vi.fn(() => { calls.push('mutate') })
    const flip = createDashboardFlip({ Flip, gsap: {}, getTargets, nextTick, reducedMotion: false, duration: 0.18 })

    await flip.run(mutate)

    expect(calls).toEqual(['getTargets', 'getState', 'mutate', 'nextTick', 'from'])
    expect(Flip.from).toHaveBeenCalledWith(state, expect.objectContaining({
      absolute: true,
      duration: 0.18,
      onEnter: expect.any(Function),
      onLeave: expect.any(Function),
    }))
  })

  it('mutates and waits without calling Flip in reduced motion', async () => {
    const mutate = vi.fn()
    const nextTick = vi.fn()
    const Flip = { getState: vi.fn(), from: vi.fn() }
    const flip = createDashboardFlip({ Flip, gsap: {}, getTargets: vi.fn(), nextTick, reducedMotion: true, duration: 0.18 })

    await flip.run(mutate)

    expect(mutate).toHaveBeenCalledOnce()
    expect(nextTick).toHaveBeenCalledOnce()
    expect(Flip.getState).not.toHaveBeenCalled()
    expect(Flip.from).not.toHaveBeenCalled()
  })

  it('passes empty target collections through without inventing targets', async () => {
    const Flip = {
      getState: vi.fn(() => ({ id: 'empty-state' })),
      from: vi.fn(() => ({ kill: vi.fn() })),
    }
    const flip = createDashboardFlip({ Flip, gsap: {}, getTargets: vi.fn(() => []), nextTick: vi.fn(async () => {}), reducedMotion: false, duration: 0.18 })

    await flip.run(vi.fn())

    expect(Flip.getState).toHaveBeenCalledWith([])
    expect(Flip.from).toHaveBeenCalledOnce()
  })

  it('propagates synchronous mutation errors without starting a tween', async () => {
    const error = new Error('mutation failed')
    const nextTick = vi.fn()
    const Flip = { getState: vi.fn(() => ({})), from: vi.fn() }
    const flip = createDashboardFlip({ Flip, gsap: {}, getTargets: vi.fn(() => ['card']), nextTick, reducedMotion: false, duration: 0.18 })

    await expect(flip.run(() => { throw error })).rejects.toBe(error)

    expect(nextTick).not.toHaveBeenCalled()
    expect(Flip.from).not.toHaveBeenCalled()
  })

  it('cancels stale runs when rapid calls overlap before nextTick resolves', async () => {
    const ticks = []
    const firstAnimation = { kill: vi.fn() }
    const secondAnimation = { kill: vi.fn() }
    const animations = [firstAnimation, secondAnimation]
    const Flip = {
      getState: vi.fn(() => ({})),
      from: vi.fn(() => animations.shift()),
    }
    const nextTick = vi.fn(() => new Promise((resolve) => ticks.push(resolve)))
    const flip = createDashboardFlip({ Flip, gsap: {}, getTargets: vi.fn(() => ['card']), nextTick, reducedMotion: false, duration: 0.18 })

    const firstRun = flip.run(vi.fn())
    const secondRun = flip.run(vi.fn())
    ticks.shift()()
    await Promise.resolve()
    ticks.shift()()
    const [firstResult, secondResult] = await Promise.all([firstRun, secondRun])

    expect(Flip.from).toHaveBeenCalledOnce()
    expect(firstResult).toBeUndefined()
    expect(secondResult).toBe(firstAnimation)
  })

  it('kills an active animation before starting the next run', async () => {
    const firstAnimation = { kill: vi.fn() }
    const secondAnimation = { kill: vi.fn() }
    const Flip = {
      getState: vi.fn(() => ({})),
      from: vi.fn()
        .mockReturnValueOnce(firstAnimation)
        .mockReturnValueOnce(secondAnimation),
    }
    const flip = createDashboardFlip({ Flip, gsap: {}, getTargets: vi.fn(() => ['card']), nextTick: vi.fn(async () => {}), reducedMotion: false, duration: 0.18 })

    await flip.run(vi.fn())
    await flip.run(vi.fn())

    expect(firstAnimation.kill).toHaveBeenCalledOnce()
  })
})
