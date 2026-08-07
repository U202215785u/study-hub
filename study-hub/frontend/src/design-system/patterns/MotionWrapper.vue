<script setup>
import { computed } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { motion } from 'motion-v'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  timing: { type: String, default: 'normal' },
  delay: { type: Number, default: 0 },
  initial: { type: [Boolean, Object], default: () => ({ opacity: 0, y: 16 }) },
  animate: { type: [Boolean, Object], default: () => ({ opacity: 1, y: 0 }) },
  exit: { type: [String, Array, Object], default: undefined },
  whileHover: { type: [Boolean, Object], default: undefined },
  whilePress: { type: [Boolean, Object], default: undefined },
  reducedMotion: { type: String, default: 'user' },
})

const prefersReduced = useMediaQuery('(prefers-reduced-motion: reduce)')

const reduced = computed(() => props.reducedMotion === 'always' || (props.reducedMotion === 'user' && prefersReduced.value))
const resolvedInitial = computed(() => reduced.value ? false : props.initial)
const resolvedExit = computed(() => reduced.value ? undefined : props.exit)
const gestureTransition = computed(() => reduced.value ? { duration: 0, delay: 0 } : { duration: 0.08, delay: 0 })
const withGestureTransition = (gesture) => {
  if (!gesture || typeof gesture !== 'object' || Array.isArray(gesture)) return gesture
  return {
    ...gesture,
    transition: { ...gestureTransition.value, ...(gesture.transition || {}) },
  }
}
const resolvedWhileHover = computed(() => reduced.value ? undefined : withGestureTransition(props.whileHover))
const resolvedWhilePress = computed(() => reduced.value ? undefined : withGestureTransition(props.whilePress))
const resolvedTransition = computed(() => reduced.value ? { duration: 0 } : {
  duration: props.timing === 'fast' ? 0.12 : props.timing === 'slow' ? 0.26 : 0.18,
  delay: props.delay,
})
</script>

<template>
  <motion.div
    v-bind="$attrs"
    :data-motion-state="reduced ? 'final' : 'animated'"
    :initial="resolvedInitial"
    :animate="props.animate"
    :exit="resolvedExit"
    :while-hover="resolvedWhileHover"
    :while-press="resolvedWhilePress"
    :transition="resolvedTransition"
  >
    <slot />
  </motion.div>
</template>
