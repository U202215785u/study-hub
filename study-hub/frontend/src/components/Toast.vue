<template>
  <div v-if="visible"
       class="fixed bottom-6 left-1/2 -translate-x-1/2 px-5 py-2.5 rounded-[8px] text-sm border z-50 transition-opacity duration-300"
       :class="isError ? 'border-danger text-danger' : 'border-border text-text bg-surface'">
    {{ message }}
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const visible = ref(false)
const message = ref('')
const isError = ref(false)
let timer = null

function show(msg, error = false) {
  message.value = msg
  isError.value = error
  visible.value = true
  clearTimeout(timer)
  timer = setTimeout(() => { visible.value = false }, 2500)
}

// Expose for provide/inject or direct ref access
defineExpose({ show })
</script>
