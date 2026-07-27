<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        class="fixed inset-0 z-[9999] flex items-center justify-center"
        @click.self="onCancel"
      >
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" />
        <!-- 卡片 -->
        <div
          class="relative bg-surface border border-border rounded-[14px] shadow-2xl w-full max-w-[380px] mx-4 p-6"
          @keydown.esc="onCancel"
        >
          <h3 class="text-base font-semibold text-text mb-2">{{ title }}</h3>
          <p v-if="message" class="text-sm text-text-secondary leading-relaxed mb-6 whitespace-pre-line">
            {{ message }}
          </p>
          <div class="flex gap-3 justify-end">
            <button
              @click="onCancel"
              class="px-4 py-2 rounded-[8px] text-sm font-medium text-text-secondary hover:bg-bg border border-border transition-colors"
            >
              取消
            </button>
            <button
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
import { useConfirm } from '../composables/useConfirm.js'

const { visible, title, message, danger, onConfirm, onCancel } = useConfirm()
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
