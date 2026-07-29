<template>
  <div class="border-t border-border pt-3 flex flex-col gap-2">
    <div class="flex items-center justify-between gap-3">
      <span class="text-xs text-text-secondary">Cookie {{ status.configured ? '已保存' : '未保存' }}</span>
      <button v-if="status.configured" type="button" class="text-xs text-danger" @click="clear">清除</button>
    </div>
    <div class="flex gap-2">
      <input v-model="cookie" type="password" autocomplete="off" placeholder="手动粘贴可选 Cookie"
        class="min-w-0 flex-1 px-3 py-2 bg-bg border border-border rounded-[6px] text-xs outline-none focus:border-accent">
      <button data-test="save-cookie" type="button" :disabled="!cookie.trim() || loading"
        class="px-3 py-2 bg-bg border border-border rounded-[6px] text-xs disabled:opacity-40" @click="save">保存</button>
    </div>
    <span v-if="message" class="text-xs" :class="error ? 'text-danger' : 'text-success'">{{ message }}</span>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const props = defineProps({ api: { type: Object, required: true } })
const status = ref({ configured: false, updated_at: null })
const cookie = ref('')
const loading = ref(false)
const message = ref('')
const error = ref(false)

async function refresh() {
  try { status.value = await props.api.apiGet('/automation/douyin/cookie/status') } catch {}
}
async function save() {
  loading.value = true; message.value = ''; error.value = false
  try {
    status.value = await props.api.apiPut('/automation/douyin/cookie', { cookie: cookie.value })
    cookie.value = ''
    message.value = '已保存'
  } catch { error.value = true; message.value = '保存失败' }
  finally { loading.value = false }
}
async function clear() {
  try { status.value = await props.api.apiDelete('/automation/douyin/cookie'); message.value = '已清除' }
  catch { error.value = true; message.value = '清除失败' }
}
onMounted(refresh)
</script>
