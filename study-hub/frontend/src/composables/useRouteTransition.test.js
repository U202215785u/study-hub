import { describe, expect, it, vi } from 'vitest'
import { createRouteTransition } from './useRouteTransition.js'

describe('createRouteTransition', () => {
  it('navigates inside a View Transition when the browser supports it', async () => {
    const navigateTo = vi.fn().mockResolvedValue(undefined)
    const nextTick = vi.fn().mockResolvedValue(undefined)
    const startViewTransition = vi.fn((update) => ({ finished: Promise.resolve().then(update) }))
    const transition = createRouteTransition({ documentRef: { startViewTransition }, matchMedia: () => ({ matches: false }), nextTick })

    await transition.navigate(navigateTo, '/kb')

    expect(startViewTransition).toHaveBeenCalledTimes(1)
    expect(navigateTo).toHaveBeenCalledWith('/kb')
    expect(nextTick).toHaveBeenCalledTimes(1)
  })

  it('navigates directly when support is missing or motion is reduced', async () => {
    const navigateTo = vi.fn().mockResolvedValue(undefined)
    const transition = createRouteTransition({ documentRef: {}, matchMedia: () => ({ matches: true }) })

    await transition.navigate(navigateTo, '/kb')

    expect(navigateTo).toHaveBeenCalledWith('/kb')
  })

  it('lets a rapid follow-up navigation bypass an active View Transition', async () => {
    let releaseTransition
    const startViewTransition = vi.fn((update) => {
      void update()
      return { finished: new Promise((resolve) => { releaseTransition = resolve }) }
    })
    const transition = createRouteTransition({ documentRef: { startViewTransition }, matchMedia: () => ({ matches: false }), nextTick: vi.fn() })
    const firstNavigate = vi.fn().mockResolvedValue(undefined)
    const secondNavigate = vi.fn().mockResolvedValue(undefined)

    const first = transition.navigate(firstNavigate, '/first')
    await Promise.resolve()
    await transition.navigate(secondNavigate, '/last')

    expect(startViewTransition).toHaveBeenCalledTimes(1)
    expect(secondNavigate).toHaveBeenCalledWith('/last')
    releaseTransition()
    await first
  })

  it('falls back to direct navigation if the View Transition API throws', async () => {
    const navigateTo = vi.fn().mockResolvedValue(undefined)
    const transition = createRouteTransition({ documentRef: { startViewTransition: () => { throw new Error('unsupported') } }, matchMedia: () => ({ matches: false }) })

    await transition.navigate(navigateTo, '/kb')

    expect(navigateTo).toHaveBeenCalledWith('/kb')
  })
})
