<template>
  <Teleport to="body">
    <div class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="pointer-events-auto flex items-center gap-2 px-4 py-2.5 rounded-[10px] text-sm font-medium shadow-lg backdrop-blur-sm border"
          :class="typeClass(t.type)"
        >
          <span class="text-base">{{ typeIcon(t.type) }}</span>
          <span>{{ t.message }}</span>
          <button
            @click="remove(t.id)"
            class="ml-1 text-current opacity-60 hover:opacity-100 transition-opacity"
          >
            ✕
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '../composables/useToast.js'

const { toasts, remove } = useToast()

function typeClass(type) {
  switch (type) {
    case 'success':
      return 'bg-green-500/10 border-green-500/30 text-green-700'
    case 'error':
      return 'bg-red-500/10 border-red-500/30 text-red-700'
    default:
      return 'bg-surface border-border text-text shadow-[0_4px_16px_rgba(0,0,0,0.15)]'
  }
}

function typeIcon(type) {
  switch (type) {
    case 'success': return '✅'
    case 'error': return '❌'
    default: return 'ℹ️'
  }
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}
</style>
