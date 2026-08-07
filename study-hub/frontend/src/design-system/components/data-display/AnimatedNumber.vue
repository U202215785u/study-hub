<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useMediaQuery } from '@vueuse/core'

const props = defineProps({
  value: { type: Number, default: 0 },
  duration: { type: Number, default: 280 },
  reducedMotion: { type: String, default: 'user' },
})

const prefersReduced = useMediaQuery('(prefers-reduced-motion: reduce)')
const reduced = computed(() => props.reducedMotion === 'always' || (props.reducedMotion === 'user' && prefersReduced.value))
const displayed = ref(0)
let frame

function targetValue(value) {
  return Number.isFinite(value) ? Math.round(value) : 0
}

function cancel() {
  if (frame) cancelAnimationFrame(frame)
  frame = undefined
}

function animate(target) {
  const from = displayed.value
  const startedAt = performance.now()
  const duration = Math.max(props.duration, 1)
  const tick = (now) => {
    const progress = Math.min((now - startedAt) / duration, 1)
    displayed.value = Math.round(from + (target - from) * progress)
    frame = progress < 1 ? requestAnimationFrame(tick) : undefined
  }
  frame = requestAnimationFrame(tick)
}

watch([() => props.value, reduced], ([value, isReduced]) => {
  cancel()
  const target = targetValue(value)
  if (isReduced) displayed.value = target
  else animate(target)
}, { immediate: true })

onBeforeUnmount(cancel)
</script>

<template>
  <span data-animated-number>{{ displayed }}</span>
</template>
