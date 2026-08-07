<template>
  <div class="min-h-screen bg-[#0b1012] text-text flex">
    <aside class="hidden md:flex w-60 shrink-0 border-r border-border p-6 flex-col">
      <div><div class="text-xl font-bold">Study Hub</div><div class="text-xs text-text-secondary mt-1">内容解析工作台</div></div>
      <nav class="mt-12 space-y-2"><button v-for="item in nav" :key="item.id" type="button" @click="tab = item.id" class="w-full text-left px-4 py-3 rounded-[6px]" :class="tab === item.id ? 'bg-cyan-400/10 border border-cyan-400 text-cyan-300' : 'text-text-secondary'">{{ item.label }}</button></nav>
      <router-link to="/" class="mt-auto text-xs text-text-secondary hover:text-cyan-300">返回 Study Hub</router-link>
    </aside>
    <main class="flex-1 min-w-0 p-5 md:p-10 max-w-[1440px]">
      <header class="flex flex-wrap gap-3 justify-between items-start mb-8"><div><div class="text-xs text-cyan-300 tracking-[1.5px]">LOCAL · USER INITIATED</div><h1 class="text-3xl font-bold mt-3">{{ tab === 'import' ? '内容链接导入' : '内容库' }}</h1></div><router-link to="/" class="md:hidden text-sm text-cyan-300">返回</router-link></header>
      <ContentImportWorkspace v-if="tab === 'import'" :parser="parser" />
      <ContentLibrary v-else :api="settings" @open="openDocument" />
      <div v-if="document" class="fixed inset-0 z-50 bg-black/70 p-4 md:p-12"><section class="h-full max-w-5xl mx-auto bg-[#11191b] border border-border rounded-[6px] p-6 overflow-y-auto"><button type="button" @click="document = null" class="float-right text-text-secondary">关闭</button><h2 class="text-xl font-bold mb-6">{{ document.title }}</h2><pre class="whitespace-pre-wrap text-sm leading-7">{{ document.content }}</pre></section></div>
    </main>
  </div>
</template>
<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useSettingsStore } from '../stores/settings.js'
import { useContentParser } from '../composables/useContentParser.js'
import ContentImportWorkspace from '../components/ContentImportWorkspace.vue'
import ContentLibrary from '../components/ContentLibrary.vue'
const settings = useSettingsStore(), parser = useContentParser(settings), tab = ref('import'), document = ref(null)
const nav = [{ id: 'import', label: '导入' }, { id: 'library', label: '内容库' }]
let timer
onMounted(() => { parser.refreshTasks().catch(() => {}); timer = window.setInterval(() => parser.refreshTasks().catch(() => {}), 3000) })
onUnmounted(() => window.clearInterval(timer))
async function openDocument(id) { const value = await settings.apiGet(`/documents/${id}`); if (!value.error) document.value = value }
</script>
