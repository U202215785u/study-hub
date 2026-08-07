export function playHomeEntrance({ gsap, root, duration = 0.18 }) {
  const select = gsap.utils.selector(root)
  const timeline = gsap.timeline()
  const clearProps = 'transform,opacity'

  timeline.from(select('[data-home-motion="navigation"]'), {
    opacity: 0,
    y: 8,
    duration,
    clearProps,
  })
  timeline.from(select('[data-home-motion="greeting"]'), {
    opacity: 0,
    y: 8,
    duration,
    clearProps,
  }, '-=0.08')
  return timeline
}
