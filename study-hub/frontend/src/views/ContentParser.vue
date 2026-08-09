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
      <div v-if="document" class="fixed inset-0 z-50 bg-black/70 p-4 md:p-12"><section class="h-full max-w-5xl mx-auto bg-[#11191b] border border-border rounded-[6px] p-6 overflow-y-auto"><button type="button" @click="document = null" class="float-right text-text-secondary">关闭</button><h2 class="text-xl font-bold mb-6">{{ document.title }}</h2><section v-if="documentFailure" class="mb-6 border border-danger/60 bg-danger/10 p-4 rounded-[6px] text-sm" role="alert"><div class="font-semibold text-danger">解析未完成</div><code class="block mt-2 font-mono text-danger">{{ documentFailure.code }}</code><p class="mt-2 text-text-secondary">{{ documentFailure.reason }}</p></section><MarkdownRenderer :content="document.content" /></section></div>
    </main>
  </div>
</template>
<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useSettingsStore } from '../stores/settings.js'
import { useContentParser } from '../composables/useContentParser.js'
import ContentImportWorkspace from '../components/ContentImportWorkspace.vue'
import ContentLibrary from '../components/ContentLibrary.vue'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
const settings = useSettingsStore(), parser = useContentParser(settings), tab = ref('import'), document = ref(null)
const nav = [{ id: 'import', label: '导入' }, { id: 'library', label: '内容库' }]
const documentFailure = computed(() => {
  const value = document.value
  if (!value) return null
  const embedded = String(value.content || '').match(/(?:火山引擎\s*)?ASR\s*失败[：:]\s*([^\n]+)/i)
  const reason = value.asr_error || (embedded ? `火山引擎 ASR 失败: ${embedded[1].trim()}` : '')
  if (!reason && !['fallback', 'failed'].includes(value.asr_status)) return null
  return { code: value.asr_error_code || asrErrorCode(reason), reason: reason || '语音转写未完成，文档仅包含已提取的元数据。' }
})
let timer
onMounted(() => { parser.refreshTasks().catch(() => {}); timer = window.setInterval(() => parser.refreshTasks().catch(() => {}), 3000) })
onUnmounted(() => window.clearInterval(timer))
async function openDocument(id) { const value = await settings.apiGet(`/documents/${id}`); if (!value.error) document.value = value }
function asrErrorCode(reason) {
  const text = String(reason || '').toLowerCase()
  if (text.includes('未配置') || text.includes('not configured')) return 'PARSER-ASR-1001'
  if (text.includes('火山引擎 asr 失败') || text.includes('volc')) return 'PARSER-ASR-2001'
  if (text.includes('视频下载失败') || text.includes('链接已过期')) return 'PARSER-ASR-2002'
  if (text.includes('ffmpeg') || text.includes('语音提取失败')) return 'PARSER-ASR-2003'
  if (text.includes('无语音') || text.includes('语音过短')) return 'PARSER-ASR-2004'
  return 'PARSER-ASR-9000'
}
</script>
