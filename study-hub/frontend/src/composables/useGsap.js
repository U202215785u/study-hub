import { nextTick, onMounted, onUnmounted } from 'vue'
import { gsap } from '../lib/gsap.js'

const resolveScope = (scope) => typeof scope === 'function' ? scope() : scope?.value

export function readCssTimeSeconds(name, element = document.documentElement) {
  const raw = getComputedStyle(element).getPropertyValue(name).trim()
  const value = Number.parseFloat(raw)
  if (!Number.isFinite(value)) return 0
  return raw.endsWith('ms') ? value / 1000 : value
}

export function useGsap({ scope, setup, onReducedMotion } = {}) {
  let media
  let started = false

  const start = async () => {
    if (started) return
    started = true
    await nextTick()
    media = gsap.matchMedia()
    const element = resolveScope(scope)
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const context = gsap.context(() => setup?.({ gsap, scope: element }), element)
      return () => context.revert()
    })
    media.add('(prefers-reduced-motion: reduce)', () => {
      onReducedMotion?.({ scope: element })
    })
  }

  const cleanup = () => {
    media?.revert()
    media = undefined
    started = false
  }

  onMounted(start)
  onUnmounted(cleanup)

  return { start, cleanup }
}
