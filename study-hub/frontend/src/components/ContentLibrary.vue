<template>
  <section class="space-y-4">
    <div class="flex flex-wrap gap-2 items-center">
      <button v-for="item in states" :key="item.id" type="button" @click="state = item.id; load()" class="px-3 py-1.5 text-xs border rounded-[5px]" :class="state === item.id ? 'border-cyan-400 text-cyan-300' : 'border-border text-text-secondary'">{{ item.label }} {{ counts[item.id] || 0 }}</button>
      <select v-model="platform" @change="load" class="ml-auto bg-[#10171a] border border-border rounded-[5px] px-2 py-1.5 text-xs text-text"><option value="all">全部平台</option><option value="douyin">抖音</option><option value="bilibili">B站</option><option value="xiaohongshu">小红书</option></select>
      <input v-model="search" @keyup.enter="load" placeholder="搜索标题或内容" class="bg-[#10171a] border border-border rounded-[5px] px-3 py-1.5 text-xs text-text">
    </div>
    <div v-if="loading" class="text-sm text-text-secondary py-8">正在读取内容库...</div>
    <div v-else-if="!items.length" class="text-sm text-text-secondary py-12 text-center">暂无{{ stateLabel }}内容</div>
    <div v-else class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <article v-for="doc in items" :key="doc.id" class="border border-border bg-[#11191b] p-4 rounded-[6px] flex flex-col min-h-[160px]">
        <span class="text-xs text-cyan-300">{{ platformLabel(doc.source) }}</span><h3 class="mt-2 text-sm font-semibold line-clamp-2">{{ doc.title }}</h3>
        <p class="mt-auto pt-4 text-xs text-text-secondary">{{ doc.char_count || 0 }} 字 · {{ formatDate(doc.created_at) }}</p>
        <p v-if="doc.error" class="mt-2 text-xs text-danger">{{ doc.error }}</p>
        <div class="mt-3 flex gap-3 text-xs"><button v-if="doc.id.toString().startsWith('task:')" type="button" @click="retry(doc.task_id)" class="text-cyan-300">重试</button><button v-else type="button" @click="$emit('open', doc.id)" class="text-cyan-300">查看文章</button><button v-if="!doc.id.toString().startsWith('task:')" type="button" @click="remove(doc.id)" class="text-danger">删除</button></div>
      </article>
    </div>
  </section>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
const props = defineProps({ api: { type: Object, required: true } })
defineEmits(['open'])
const states = [{ id: 'pending', label: '待处理' }, { id: 'completed', label: '已完成' }, { id: 'error', label: '异常' }]
const state = ref('completed'), platform = ref('all'), search = ref(''), items = ref([]), counts = ref({}), loading = ref(false)
const stateLabel = computed(() => states.find(item => item.id === state.value)?.label || '')
const platformLabel = source => ({ 'douyin-summary': '抖音', 'bilibili-summary': 'B站', 'xiaohongshu-summary': '小红书' })[source] || '内容'
const formatDate = value => value ? String(value).slice(0, 16).replace('T', ' ') : ''
async function load() { loading.value = true; try { const data = await props.api.apiGet(`/content-parser/documents?platform=${platform.value}&state=${state.value}&search=${encodeURIComponent(search.value)}`); items.value = data.items || []; counts.value = data.counts || {} } finally { loading.value = false } }
async function retry(taskId) { await props.api.apiPost(`/automation/queue/retry/${taskId}`, {}); await load() }
async function remove(id) { if (!window.confirm('确定删除这篇文章吗？')) return; await props.api.apiDelete(`/documents/${id}`); await load() }
onMounted(load)
</script>
