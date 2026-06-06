<template>
  <div v-if="visible" class="fixed inset-0 bg-black/70 flex items-center justify-center z-[120]" @click.self="close">
    <div class="bg-white rounded-[16px] overflow-hidden shadow-2xl w-[90%] max-w-[600px] flex flex-col">
      <!-- Cover Image -->
      <div v-if="page.cover_image" class="w-full h-[240px] overflow-hidden relative">
        <img :src="page.cover_image" alt="封面" class="w-full h-full object-cover" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
        <div class="absolute bottom-4 left-5 right-5">
          <h1 class="text-white text-[22px] font-bold leading-tight drop-shadow-lg">{{ page.title }}</h1>
        </div>
      </div>
      <div v-else class="w-full h-[160px] bg-gradient-to-br from-accent to-accent/60 flex items-center justify-center">
        <h1 class="text-white text-[22px] font-bold px-5 text-center">{{ page.title }}</h1>
      </div>

      <!-- Content -->
      <div class="p-6 flex flex-col gap-3">
        <p v-if="page.summary" class="text-gray-600 text-[14px] leading-relaxed">{{ page.summary }}</p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in tags"
            :key="tag"
            class="px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 text-[12px]"
          >
            {{ tag }}
          </span>
        </div>
        <div class="flex items-center justify-between pt-3 border-t border-gray-100">
          <span class="text-gray-400 text-[12px]">
            {{ page.category || 'Wiki' }} · {{ wordCount }}字
          </span>
          <span class="text-gray-400 text-[12px]">
            {{ date }}
          </span>
        </div>
      </div>

      <!-- Actions -->
      <div class="px-6 pb-5 flex gap-2.5 justify-end">
        <button
          class="px-4 py-2 rounded-[8px] border text-[13px] bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
          @click="close"
        >
          关闭
        </button>
        <button
          class="px-4 py-2 rounded-[8px] border text-[13px] bg-accent border-accent text-white hover:opacity-90"
          @click="copyImage"
        >
          📋 复制图片
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  page: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close'])

const tags = computed(() => {
  try { return JSON.parse(props.page.tags || '[]') } catch { return [] }
})

const wordCount = computed(() => props.page.char_count || 0)

const date = computed(() => {
  const d = props.page.updated_at || props.page.created_at
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
})

function close() {
  emit('close')
}

async function copyImage() {
  try {
    const card = document.querySelector('.bg-white.rounded-\\[16px\\]')
    if (!card) return
    const canvas = await html2canvas(card)
    canvas.toBlob(async (blob) => {
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob })
      ])
      alert('图片已复制到剪贴板')
    })
  } catch (e) {
    alert('复制失败，请手动截图')
  }
}
</script>
