<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        data-test="confirm-overlay"
        class="fixed inset-0 z-[9999] flex items-center justify-center"
        @click.self="onCancel"
      >
        <!-- 遮罩 -->
        <div
          data-test="confirm-backdrop"
          class="absolute inset-0 bg-black/50 backdrop-blur-sm"
          @click="onCancel"
        />
        <!-- 卡片 -->
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="app-confirm-title"
          class="relative bg-surface border border-border rounded-[14px] shadow-2xl w-full max-w-[380px] mx-4 p-6"
        >
          <h3 id="app-confirm-title" class="text-base font-semibold text-text mb-2">{{ title }}</h3>
          <p v-if="message" class="text-sm text-text-secondary leading-relaxed mb-6 whitespace-pre-line">
            {{ message }}
          </p>
          <div class="flex gap-3 justify-end">
            <button
              ref="cancelButton"
              @click="onCancel"
              class="px-4 py-2 rounded-[8px] text-sm font-medium text-text-secondary hover:bg-bg border border-border transition-colors"
            >
              取消
            </button>
            <button
              ref="confirmButton"
              @click="onConfirm"
              class="px-4 py-2 rounded-[8px] text-sm font-medium text-white transition-colors"
              :class="danger ? 'bg-danger hover:bg-danger/80' : 'bg-accent hover:bg-accent/80'"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useConfirm } from '../composables/useConfirm.js'

const { visible, title, message, danger, requestId, onConfirm, onCancel } = useConfirm()
const cancelButton = ref(null)
const confirmButton = ref(null)
let previouslyFocused = null

function focusFirstControl() {
  cancelButton.value?.focus()
}

function handleKeydown(event) {
  if (!visible.value) return

  if (event.key === 'Escape') {
    event.preventDefault()
    onCancel()
    return
  }

  if (event.key !== 'Tab') return
  const controls = [cancelButton.value, confirmButton.value].filter(Boolean)
  if (controls.length === 0) return

  const currentIndex = controls.indexOf(document.activeElement)
  const nextIndex = event.shiftKey
    ? (currentIndex <= 0 ? controls.length - 1 : currentIndex - 1)
    : (currentIndex === controls.length - 1 ? 0 : currentIndex + 1)
  event.preventDefault()
  controls[nextIndex].focus()
}

watch([visible, requestId], ([isVisible]) => {
  if (isVisible) {
    previouslyFocused = previouslyFocused || document.activeElement
    focusFirstControl()
  } else {
    previouslyFocused?.focus?.()
    previouslyFocused = null
  }
}, { flush: 'post' })

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
