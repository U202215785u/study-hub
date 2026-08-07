const defaultDocument = typeof document === 'undefined' ? undefined : document
const defaultMatchMedia = typeof window === 'undefined' ? undefined : window.matchMedia

export function createRouteTransition({ documentRef = defaultDocument, matchMedia = defaultMatchMedia, nextTick = () => Promise.resolve() } = {}) {
  let running = false

  async function navigate(navigateTo, target) {
    const reducedMotion = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)')?.matches
    if (running || reducedMotion || typeof documentRef?.startViewTransition !== 'function') return navigateTo(target)

    running = true
    let navigationResult
    let started = false
    try {
      const transition = documentRef.startViewTransition(async () => {
        navigationResult = await navigateTo(target)
        await nextTick()
      })
      started = true
      try {
        await transition?.finished
      } catch {
        // Navigation has already been requested; retain its result rather than retrying it.
      }
      return navigationResult
    } catch {
      return started ? navigationResult : navigateTo(target)
    } finally {
      running = false
    }
  }

  return { navigate }
}
