<template>
  <div class="flex flex-col gap-3">
    <textarea v-model="input" rows="3" placeholder="粘贴抖音分享文本或链接，最多 10 个作品"
      class="w-full px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-sm outline-none resize-y focus:border-accent"></textarea>
    <div class="flex items-center gap-2">
      <button data-test="preflight" type="button" :disabled="loading || !input.trim()"
        class="px-4 py-2 rounded-[8px] bg-accent text-white text-[13px] disabled:opacity-40" @click="preflight">
        {{ loading ? '正在检查…' : '检查链接' }}
      </button>
      <span v-if="message" class="text-xs" :class="error ? 'text-danger' : 'text-text-secondary'">{{ message }}</span>
    </div>

    <div v-if="items.length" class="flex flex-col gap-2 max-h-[320px] overflow-y-auto">
      <div v-for="item in items" :key="item.item_id" class="border border-border rounded-[8px] p-3 flex gap-3 items-start">
        <input v-if="item.status === 'ready'" v-model="selected" type="checkbox" :value="item.item_id" class="mt-1">
        <span v-else class="w-4 mt-0.5 text-center text-xs text-text-secondary">{{ statusSymbol(item.status) }}</span>
        <div class="min-w-0 flex-1">
          <div class="text-sm truncate">{{ item.title || '未命名作品' }}</div>
          <div class="text-xs mt-1" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</div>
          <div v-if="item.error_message" class="text-xs text-text-secondary mt-1 break-words">{{ item.error_message }}</div>
          <label v-if="item.status === 'needs_local_file'" class="inline-flex mt-2 px-3 py-1.5 border border-border rounded-[6px] text-xs cursor-pointer">
            选择本地视频
            <input type="file" accept="video/mp4,video/quicktime,video/webm,video/x-matroska" class="hidden" @change="upload(item, $event)">
          </label>
        </div>
      </div>
    </div>

    <button v-if="items.length" data-test="confirm-ready" type="button" :disabled="!selected.length || confirming"
      class="self-start px-4 py-2 rounded-[8px] border border-border bg-bg text-[13px] disabled:opacity-40" @click="confirmReady">
      {{ confirming ? '正在提交…' : `确认识别 ${selected.length} 个` }}
    </button>
    <DouyinCookieControl :api="api" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DouyinCookieControl from './DouyinCookieControl.vue'

const props = defineProps({ api: { type: Object, required: true } })
const emit = defineEmits(['queued'])
const input = ref('')
const loading = ref(false)
const confirming = ref(false)
const message = ref('')
const error = ref(false)
const batchId = ref('')
const items = ref([])
const selected = ref([])

const labels = { ready: '可识别', duplicate: '重复', blocked: '暂时受限', needs_local_file: '需要本地视频', failed: '不可用', confirmed: '已提交' }
function statusLabel(status) { return labels[status] || status }
function statusSymbol(status) { return ({ duplicate: '=', blocked: '!', needs_local_file: '+', failed: '×', confirmed: '✓' })[status] || '·' }
function statusClass(status) { return status === 'ready' ? 'text-success' : status === 'failed' ? 'text-danger' : 'text-text-secondary' }

async function preflight() {
  loading.value = true; error.value = false; message.value = ''
  try {
    const data = await props.api.apiPost('/automation/douyin/preflight', { input: input.value.trim() })
    batchId.value = data.batch_id
    items.value = data.items || []
    selected.value = items.value.filter(i => i.status === 'ready').map(i => i.item_id)
    message.value = `已检查 ${items.value.length} 个作品`
  } catch { error.value = true; message.value = '链接检查失败' }
  finally { loading.value = false }
}
async function confirmReady() {
  confirming.value = true; error.value = false
  try {
    const data = await props.api.apiPost('/automation/douyin/confirm', { batch_id: batchId.value, item_ids: selected.value })
    message.value = `已提交 ${data.task_ids?.length || 0} 个任务`
    emit('queued', data.task_ids || [])
  } catch { error.value = true; message.value = '提交失败' }
  finally { confirming.value = false }
}
async function upload(item, event) {
  const file = event.target.files?.[0]
  if (!file) return
  const form = new FormData(); form.append('file', file)
  try {
    const updated = await props.api.apiUpload(`/automation/douyin/items/${item.item_id}/local-file`, form)
    const index = items.value.findIndex(i => i.item_id === item.item_id)
    if (index >= 0) items.value[index] = updated
    if (!selected.value.includes(item.item_id)) selected.value.push(item.item_id)
  } catch { error.value = true; message.value = '本地视频上传失败' }
}
</script>
