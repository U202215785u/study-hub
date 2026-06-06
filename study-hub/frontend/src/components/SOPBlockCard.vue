<template>
  <div
    class="bg-surface border rounded-[8px] p-3 transition-all cursor-pointer group"
    :class="selected ? 'border-accent shadow-[0_0_12px_rgba(124,138,255,0.15)]' : 'border-border hover:border-accent/40'"
    :draggable="draggable"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
  >
    <div class="flex items-start justify-between gap-2">
      <!-- Drag handle -->
      <div v-if="draggable" class="text-text-secondary/30 cursor-grab flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" title="拖拽排序">
        ⠿
      </div>

      <div class="flex-1 min-w-0" @click="$emit('select', block)">
        <div class="text-[13px] font-semibold truncate">{{ block.title }}</div>
        <div v-if="block.description" class="text-[11px] text-text-secondary mt-0.5 line-clamp-2">
          {{ block.description }}
        </div>
        <div class="flex items-center gap-1.5 mt-1.5 flex-wrap">
          <span
            v-for="tag in tags" :key="tag"
            class="text-[10px] text-text-secondary bg-white/[0.04] px-1.5 py-0.5 rounded-full"
          >{{ tag }}</span>
          <span
            v-if="block.source_type === 'wiki'"
            class="text-[10px] text-accent bg-accent/10 px-1.5 py-0.5 rounded-full"
            title="来自 Wiki"
          >📄 Wiki</span>
        </div>
      </div>

      <div class="flex gap-1 flex-shrink-0">
        <button
          @click.stop="$emit('edit', block)"
          class="text-[11px] text-text-secondary hover:text-accent bg-transparent border-none cursor-pointer px-1"
          title="编辑"
        >✏️</button>
        <button
          v-if="removable"
          @click.stop="$emit('remove', block)"
          class="text-[11px] text-text-secondary hover:text-danger bg-transparent border-none cursor-pointer px-1"
          title="移除"
        >✕</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  block: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  removable: { type: Boolean, default: false },
  draggable: { type: Boolean, default: false },
})

defineEmits(['select', 'edit', 'remove'])

const tags = computed(() => {
  const t = props.block.tags
  if (!t) return []
  if (Array.isArray(t)) return t
  try { return JSON.parse(t) } catch { return [] }
})

function onDragStart(e) {
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'new', block: props.block }))
  e.target.closest('.group\\/item')?.classList.add('opacity-40')
}

function onDragEnd(e) {
  e.target.closest('.group\\/item')?.classList.remove('opacity-40')
}
</script>
