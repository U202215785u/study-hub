<template>
  <span class="text-[10px] px-1.5 py-0.5 rounded-full border"
    :class="badgeClass">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: String })

const map = {
  pending:   { label: '排队中', cls: 'bg-surface border-border text-text-secondary' },
  extracting:{ label: '提取中', cls: 'bg-accent/10 border-accent/30 text-accent' },
  summarizing:{ label: '总结中', cls: 'bg-accent/10 border-accent/30 text-accent' },
  importing: { label: '入库中', cls: 'bg-accent/10 border-accent/30 text-accent' },
  done:      { label: '完成',   cls: 'bg-success/10 border-success/30 text-success' },
  error:     { label: '失败',   cls: 'bg-danger/10 border-danger/30 text-danger' },
}

const runningSteps = ['extract_meta','download_audio','asr','summarize','import']

const badgeClass = computed(() => {
  if (map[props.status]) return map[props.status].cls
  if (runningSteps.includes(props.status)) return map.extracting.cls
  return map.pending.cls
})
const label = computed(() => {
  if (map[props.status]) return map[props.status].label
  if (runningSteps.includes(props.status)) return '处理中'
  return props.status
})
</script>
