export function createDashboardFlip({ Flip, gsap, getTargets, nextTick, reducedMotion = false, duration = 0.18 }) {
  let activeAnimation
  let runId = 0

  const run = async (mutate) => {
    const currentRunId = ++runId
    activeAnimation?.kill?.()
    activeAnimation = undefined

    if (reducedMotion) {
      mutate()
      await nextTick()
      return undefined
    }

    const targets = getTargets()
    const state = Flip.getState(targets)
    mutate()
    await nextTick()
    if (currentRunId !== runId) return undefined
    activeAnimation = Flip.from(state, {
      absolute: true,
      duration,
      ease: 'power2.out',
      onEnter: (elements) => gsap.fromTo(elements, { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration, ease: 'power2.out' }),
      onLeave: (elements) => gsap.to(elements, { opacity: 0, scale: 0.96, duration, ease: 'power2.out' }),
    })
    return activeAnimation
  }

  return { run }
}
