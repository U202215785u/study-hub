<template>
  <section class="space-y-5">
    <div class="flex flex-wrap gap-2" role="group" aria-label="平台选择">
      <button v-for="option in modes" :key="option.id" type="button" @click="mode = option.id"
        class="px-3 py-2 text-sm border rounded-[6px]" :class="mode === option.id ? 'border-cyan-400 text-cyan-300 bg-cyan-400/10' : 'border-border text-text-secondary'">
        {{ option.label }}
      </button>
    </div>
    <textarea v-model="input" rows="7" placeholder="粘贴抖音、B站或小红书分享文本和链接"
      class="w-full bg-[#10171a] border border-border rounded-[6px] p-4 text-text outline-none focus:border-cyan-400" />
    <div class="flex items-center justify-between gap-3">
      <span class="text-xs text-text-secondary">{{ input.length }} 字符，最多 10 个链接</span>
      <button data-test="preflight" type="button" :disabled="loading || !input.trim()" @click="check"
        class="px-4 py-2 bg-cyan-400 text-black font-medium rounded-[6px] disabled:opacity-40">
        {{ loading ? '检查中...' : '检查链接' }}
      </button>
    </div>
    <p v-if="message" class="text-sm" :class="error ? 'text-danger' : 'text-cyan-300'">{{ message }}</p>
    <div v-if="items.length" class="border border-border rounded-[6px] divide-y divide-border">
      <label v-for="item in items" :key="item.item_id" class="flex gap-3 p-3 items-start">
        <input v-if="item.status === 'ready'" v-model="selected" type="checkbox" :value="item.item_id" class="mt-1">
        <span v-else class="w-4 mt-0.5 text-text-secondary">!</span>
        <span class="flex-1 min-w-0">
          <b class="text-sm">{{ platformLabel(item.platform) }}</b>
          <span class="block text-xs text-text-secondary break-all">{{ item.title || item.input_url }}</span>
          <span v-if="item.error_message" class="block text-xs text-danger mt-1">{{ item.error_message }}</span>
        </span>
        <span class="text-xs" :class="item.status === 'ready' ? 'text-cyan-300' : 'text-danger'">{{ statusLabel(item.status) }}</span>
      </label>
    </div>
    <button v-if="items.length" data-test="confirm" type="button" :disabled="!selected.length || confirming" @click="submit"
      class="px-4 py-2 border border-cyan-400 text-cyan-300 rounded-[6px] disabled:opacity-40">
      {{ confirming ? '提交中...' : `确认识别 ${selected.length} 个` }}
    </button>
    <div v-if="parser.tasks.value.length" class="border-t border-border pt-4 space-y-2">
      <h3 class="text-sm font-semibold">解析进度</h3>
      <div v-for="task in parser.tasks.value" :key="task.task_id" class="space-y-2 text-xs" :data-testid="`parser-task-${task.task_id}`">
        <span class="min-w-0 flex-1">
          <span class="block truncate">{{ task.title || task.input }}</span>
          <span v-if="task.status === 'error'" class="block text-danger mt-1 break-words">
            <code v-if="task.error_code" class="font-mono">{{ task.error_code }}</code>
            <span v-if="task.error_code && task.error">: </span>
            <span>{{ task.error || '解析失败，暂未提供详细原因' }}</span>
          </span>
        </span>
        <span class="block text-text-secondary">{{ task.progress_text || statusLabel(task.status) }} <span class="ml-1 text-text">{{ progressValue(task) }}%</span></span>
        <div class="h-2 w-full overflow-hidden rounded-full bg-white/10" role="progressbar" :aria-label="`${task.title || task.input} parser progress`" aria-valuemin="0" aria-valuemax="100" :aria-valuenow="progressValue(task)">
          <div class="h-full rounded-full bg-cyan-400 transition-[width] duration-300" :style="{ width: `${progressValue(task)}%` }" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({ parser: { type: Object, required: true } })
const input = ref('')
const mode = ref('auto')
const loading = ref(false)
const confirming = ref(false)
const message = ref('')
const error = ref(false)
const selected = ref([])
const modes = [{ id: 'auto', label: '自动识别' }, { id: 'douyin', label: '抖音' }, { id: 'bilibili', label: 'B站' }, { id: 'xiaohongshu', label: '小红书' }]
const items = computed(() => props.parser.batch.value?.items || [])
const platformLabel = (platform) => ({ douyin: '抖音', bilibili: 'B站', xiaohongshu: '小红书' })[platform] || platform
const statusLabel = (status) => ({ ready: '可处理', duplicate: '重复', needs_local_file: '需要本地视频', blocked: '暂时受限', failed: '不可用' })[status] || status
function progressValue(task) {
  if (task.status === 'done') return 100
  const value = Number(task.progress)
  return Number.isFinite(value) ? Math.min(100, Math.max(0, Math.round(value))) : 0
}

async function check() {
  loading.value = true; error.value = false; message.value = ''
  try {
    await props.parser.preflight(input.value.trim(), mode.value)
    selected.value = items.value.filter(item => item.status === 'ready').map(item => item.item_id)
    message.value = `已检查 ${items.value.length} 个链接`
  } catch (err) { error.value = true; message.value = err?.message || '链接检查失败' }
  finally { loading.value = false }
}
async function submit() {
  confirming.value = true; error.value = false
  try { const result = await props.parser.confirm(selected.value); message.value = `已提交 ${result.task_ids?.length || 0} 个任务` }
  catch (err) { error.value = true; message.value = err?.message || '提交失败' }
  finally { confirming.value = false }
}
</script>
