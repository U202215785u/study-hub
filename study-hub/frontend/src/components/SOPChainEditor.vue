<template>
  <div
    class="bg-surface border rounded-[12px] p-5 transition-all"
    :class="dragOver ? 'border-accent shadow-[0_0_20px_rgba(124,138,255,0.2)]' : 'border-border'"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="text-[15px] font-semibold">{{ chain.name }}</span>
        <button
          @click="$emit('edit-chain')"
          class="text-[11px] text-text-secondary hover:text-accent bg-transparent border-none cursor-pointer"
          title="编辑链路信息"
        >✏️</button>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="dragHint" class="text-[10px] text-accent animate-pulse">{{ dragHint }}</span>
        <span class="text-[11px] text-text-secondary">{{ blocks.length }} 个环节</span>
      </div>
    </div>
    <div v-if="chain.description" class="text-[12px] text-text-secondary mb-4 -mt-1">
      {{ chain.description }}
    </div>

    <!-- Empty state -->
    <div
      v-if="!flatBlocks.length"
      class="text-center py-10 text-text-secondary text-[13px] border-2 border-dashed border-border rounded-[10px] transition-colors"
      :class="dragOver ? 'border-accent bg-accent/5' : ''"
    >
      <p class="text-3xl mb-2">🔗</p>
      <p>链路中还没有环节</p>
      <p class="text-[11px] mt-1">从左侧拖拽环节到此处，或点击下方添加</p>
    </div>

    <!-- Block sequence with drop zones -->
    <div v-else class="flex flex-col gap-0">
      <!-- Drop zone before first block -->
      <div class="transition-all duration-200" :class="dropIndex === 0 ? 'h-[12px]' : 'h-[2px]'">
        <div class="h-full rounded-full transition-all" :class="dropIndex === 0 ? 'bg-accent h-[3px] shadow-[0_0_8px_rgba(124,138,255,0.5)]' : 'bg-transparent'"></div>
      </div>

      <template v-for="(item, i) in flatBlocks" :key="item.cb_id || item.block.id">
        <!-- Branch connector -->
        <div
          v-if="item._depth > 0"
          class="flex items-center"
          :style="{paddingLeft: (item._depth * 28) + 'px'}"
        >
          <svg width="20" height="22" class="flex-shrink-0 text-text-secondary/20">
            <line x1="10" y1="0" x2="10" y2="22" stroke="currentColor" stroke-width="1.5" />
            <line x1="10" y1="11" x2="20" y2="11" stroke="currentColor" stroke-width="1.5" />
          </svg>
          <span class="text-[10px] text-text-secondary/50 ml-1">{{ item.branch_label || '分支' }}</span>
        </div>

        <!-- Arrow between top-level blocks -->
        <div
          v-if="item._depth === 0 && item._topIndex > 0"
          class="flex items-center gap-2 py-0.5"
        >
          <div class="flex-1 h-px bg-border/30"></div>
        </div>

        <!-- Block row -->
        <div
          data-block-row
          class="flex items-center gap-2 group relative py-0.5"
          :class="[
            item._depth > 0 ? '' : '',
            dragSourceId === item.cb_id ? 'opacity-30' : ''
          ]"
          :style="{marginLeft: item._depth > 0 ? (item._depth * 28) + 'px' : '0'}"
          :draggable="true"
          @dragstart="onBlockDragStart($event, item)"
          @dragend="onBlockDragEnd"
        >
          <!-- Step number -->
          <div class="flex items-center gap-2 flex-shrink-0" style="min-width: 30px">
            <span
              v-if="item._depth === 0"
              class="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0"
              :class="stepColor(item._topIndex)"
            >
              {{ item._topIndex + 1 }}
            </span>
            <span v-else class="w-6 flex-shrink-0"></span>
          </div>

          <!-- Drag handle -->
          <div class="text-text-secondary/20 cursor-grab flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-[14px]" title="拖拽排序">
            ⠿
          </div>

          <!-- Block card -->
          <div class="flex-1 min-w-0">
            <SOPBlockCard
              :block="item.block"
              :removable="true"
              @select="$emit('select-block', item.block)"
              @edit="$emit('edit-block', item.block)"
              @remove="$emit('remove-block', item)"
            />
          </div>

          <!-- Action buttons -->
          <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
            <button
              @click="$emit('add-branch', item)"
              class="text-[10px] text-text-secondary hover:text-accent bg-white/[0.06] px-1.5 py-1 rounded border-none cursor-pointer"
              title="添加分支"
            >↳ 分支</button>
            <button
              v-if="canMoveUp(item, i)"
              @click="quickMove(item, -1)"
              class="text-[10px] text-text-secondary hover:text-accent bg-white/[0.06] px-1.5 py-1 rounded border-none cursor-pointer"
              title="上移"
            >▲</button>
            <button
              v-if="canMoveDown(item, i)"
              @click="quickMove(item, 1)"
              class="text-[10px] text-text-secondary hover:text-accent bg-white/[0.06] px-1.5 py-1 rounded border-none cursor-pointer"
              title="下移"
            >▼</button>
          </div>
        </div>

        <!-- Drop zone after this block -->
        <div class="transition-all duration-200" :class="dropIndex === i + 1 ? 'h-[12px]' : 'h-[2px]'">
          <div class="h-full rounded-full transition-all" :class="dropIndex === i + 1 ? 'bg-accent h-[3px] shadow-[0_0_8px_rgba(124,138,255,0.5)]' : 'bg-transparent'"></div>
        </div>
      </template>
    </div>

    <!-- Quick add button at bottom -->
    <div v-if="blocks.length > 0" class="mt-4 pt-3 border-t border-border flex items-center gap-2">
      <span class="text-[11px] text-text-secondary">快速操作：</span>
      <button
        @click="$emit('edit-chain')"
        class="text-[11px] text-text-secondary hover:text-accent bg-white/[0.04] px-2 py-1 rounded border-none cursor-pointer"
      >编辑信息</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SOPBlockCard from './SOPBlockCard.vue'

const props = defineProps({
  chain: { type: Object, required: true },
  blocks: { type: Array, required: true },
})

const emit = defineEmits([
  'select-block', 'edit-block', 'remove-block',
  'move-up', 'move-down', 'edit-chain', 'add-branch',
  'reorder-blocks', 'drop-block',
])

// ── Drag state ──
const dragOver = ref(false)
const dragSourceId = ref(null)
const dropIndex = ref(-1)
const dragHint = ref('')

// ── Flatten blocks with depth ──
const flatBlocks = computed(() => {
  const result = []
  let topIndex = 0
  for (const item of props.blocks) {
    if (!item.parent_id) {
      result.push({ ...item, _depth: 0, _topIndex: topIndex })
      topIndex++
      const children = props.blocks.filter(b => b.parent_id === item.cb_id)
      for (const child of children) {
        result.push({ ...child, _depth: 1, _topIndex: topIndex - 1 })
      }
    } else {
      if (!props.blocks.find(b => b.cb_id === item.parent_id)) {
        result.push({ ...item, _depth: 0, _topIndex: topIndex })
        topIndex++
      }
    }
  }
  return result
})

function stepColor(index) {
  const colors = [
    'bg-accent text-white',
    'bg-emerald-500/20 text-emerald-400',
    'bg-blue-500/20 text-blue-400',
    'bg-amber-500/20 text-amber-400',
    'bg-purple-500/20 text-purple-400',
    'bg-rose-500/20 text-rose-400',
  ]
  return colors[index % colors.length]
}

function canMoveUp(item, i) {
  const fbs = flatBlocks.value
  if (item._depth !== 0) return false
  for (let j = i - 1; j >= 0; j--) {
    if (fbs[j]._depth === 0) return true
  }
  return false
}

function canMoveDown(item, i) {
  const fbs = flatBlocks.value
  if (item._depth !== 0) return false
  for (let j = i + 1; j < fbs.length; j++) {
    if (fbs[j]._depth === 0) return true
  }
  return false
}

// ── Drag handlers ──
function onDragOver(e) {
  dragOver.value = true
  const dataTypes = e.dataTransfer.types || []
  dragHint.value = '松手插入此处'

  // Calculate drop position based on mouse Y, skipping the dragged block
  if (flatBlocks.value.length > 0) {
    const container = e.currentTarget
    const allRows = container.querySelectorAll('[data-block-row]')
    const y = e.clientY
    let idx = flatBlocks.value.length // default: append to end
    let visibleIdx = 0
    allRows.forEach((el) => {
      // Skip the row that's currently being dragged (opacity-30)
      if (el.classList.contains('opacity-30')) return
      const rect = el.getBoundingClientRect()
      if (y < rect.top + rect.height / 2) {
        idx = Math.min(idx, visibleIdx)
      }
      visibleIdx++
    })
    dropIndex.value = idx
  } else {
    dropIndex.value = 0
  }
}

function onDragLeave(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) {
    dragOver.value = false
    dragHint.value = ''
    dropIndex.value = -1
  }
}

function onDrop(e) {
  dragOver.value = false
  dragHint.value = ''
  const raw = e.dataTransfer.getData('text/plain')
  const idx = dropIndex.value
  dropIndex.value = -1

  // Internal reorder
  if (dragSourceId.value) {
    const targetIdx = idx >= 0 && idx < flatBlocks.value.length ? idx : flatBlocks.value.length
    emit('reorder-blocks', { cb_id: dragSourceId.value, targetIndex: targetIdx })
    dragSourceId.value = null
    return
  }

  // External drop (new block from library)
  if (raw) {
    try {
      const data = JSON.parse(raw)
      if (data.type === 'new' && data.block) {
        const targetIdx = idx >= 0 ? idx : props.blocks.length
        emit('drop-block', { block: data.block, targetIndex: targetIdx })
      }
    } catch { /* ignore */ }
  }
}

// ── Internal block drag ──
function onBlockDragStart(e, item) {
  dragSourceId.value = item.cb_id
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'reorder', cb_id: item.cb_id }))
  // Hide the dragged element's drop zone by making it fade
  const row = e.target.closest('[data-block-row]')
  if (row) row.classList.add('opacity-30')
}

function onBlockDragEnd(e) {
  const row = e.target.closest('[data-block-row]')
  if (row) row.classList.remove('opacity-30')
  dragSourceId.value = null
  dropIndex.value = -1
}

// ── Quick move (button click) ──
function quickMove(item, delta) {
  if (delta < 0) emit('move-up', item)
  else emit('move-down', item)
}
</script>
