<template>
  <div class="bg-surface border border-border rounded-[12px] p-4">
    <div class="flex items-center justify-between mb-3">
      <span class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px]">
        Wiki 建议队列 ({{ suggestions.length }})
      </span>
      <button
        @click="$emit('analyze')"
        :disabled="analyzing"
        class="px-3 py-1.5 bg-accent text-white rounded-[8px] text-[11px] cursor-pointer border-none hover:opacity-90 disabled:opacity-50"
      >
        {{ analyzing ? '分析中…' : `分析 Wiki 知识库${unmatchedCount ? ` (${unmatchedCount}篇)` : ''}` }}
      </button>
    </div>

    <div v-if="!suggestions.length && !analyzing" class="text-center py-6 text-text-secondary text-[12px]">
      <p class="text-xl mb-1">💡</p>
      <p>暂无待处理建议</p>
      <p class="text-[11px] mt-0.5">点击"分析 Wiki 知识库"让 AI 自动匹配</p>
    </div>

    <div v-if="analyzing" class="text-center py-6 text-text-secondary text-[12px]">
      <p class="text-lg mb-1">⏳</p>
      <p>AI 正在分析 Wiki 页面…</p>
    </div>

    <div v-else class="flex flex-col gap-2 max-h-[400px] overflow-y-auto">
      <div
        v-for="s in suggestions" :key="s.id"
        class="bg-bg border border-border rounded-[8px] p-3"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5 mb-1">
              <span class="text-[10px] px-1.5 py-0.5 rounded-full font-semibold"
                :class="typeBadgeClass(s.suggestion_type)"
              >{{ typeLabel(s.suggestion_type) }}</span>
              <span class="text-[12px] font-semibold truncate">{{ s.suggested_title }}</span>
            </div>
            <div class="text-[11px] text-text-secondary leading-relaxed">
              {{ s.rationale }}
            </div>
            <!-- extract_chain: show steps -->
            <div v-if="s.suggestion_type === 'extract_chain' && parseSteps(s)" class="mt-2 flex flex-col gap-0.5">
              <div v-for="(step, si) in parseSteps(s)" :key="si" class="text-[10px] text-text-secondary flex items-center gap-1">
                <span class="w-4 h-4 rounded-full bg-accent/10 text-accent flex items-center justify-center text-[9px] font-bold flex-shrink-0">{{ si + 1 }}</span>
                <span class="truncate">{{ step.title }}</span>
              </div>
            </div>
            <!-- other types: show content snippet -->
            <div v-else-if="s.suggested_content && s.suggestion_type !== 'extract_chain'" class="mt-2 text-[11px] text-text-secondary bg-surface rounded-[6px] p-2 max-h-[80px] overflow-y-auto whitespace-pre-wrap">
              {{ s.suggested_content.slice(0, 200) }}{{ s.suggested_content.length > 200 ? '…' : '' }}
            </div>
          </div>
        </div>
        <div class="flex gap-2 mt-2 justify-end">
          <button
            @click="$emit('reject', s)"
            class="px-3 py-1 rounded-[6px] border border-border bg-surface text-text-secondary text-[11px] cursor-pointer hover:bg-surface-hover"
          >拒绝</button>
          <button
            @click="$emit('confirm', s)"
            class="px-3 py-1 rounded-[6px] bg-accent text-white text-[11px] cursor-pointer border-none hover:opacity-90"
          >确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  suggestions: { type: Array, default: () => [] },
  analyzing: { type: Boolean, default: false },
  unmatchedCount: { type: Number, default: 0 },
})

defineEmits(['confirm', 'reject', 'analyze'])

const typeLabels = {
  new_block: '新环节',
  merge_into_block: '合并内容',
  insert_into_chain: '插入链路',
  enrich_block: '丰富环节',
  extract_chain: '提取流程',
}

function typeLabel(type) {
  return typeLabels[type] || type
}

function typeBadgeClass(type) {
  return {
    new_block: 'bg-green-500/15 text-green-400',
    merge_into_block: 'bg-blue-500/15 text-blue-400',
    insert_into_chain: 'bg-accent/15 text-accent',
    enrich_block: 'bg-yellow-500/15 text-yellow-400',
    extract_chain: 'bg-purple-500/15 text-purple-400',
  }[type] || 'bg-white/10 text-text-secondary'
}

// Parse extract_chain steps for preview
function parseSteps(s) {
  if (s.suggestion_type !== 'extract_chain') return null
  try {
    const data = JSON.parse(s.suggested_content)
    return data.steps || []
  } catch { return null }
}
</script>
