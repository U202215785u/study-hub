<template>
  <div class="fixed bottom-4 right-4 z-40">
    <div class="bg-surface border border-border rounded-[12px] p-3 text-[12px] shadow-lg transition-all"
         :class="expanded ? 'w-48' : 'w-auto'"
         @mouseenter="expanded = true" @mouseleave="expanded = false">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full" :class="connected ? 'bg-success' : 'bg-danger'"></span>
        <span class="text-text-secondary">{{ connected ? '已连接' : '未连接' }}</span>
      </div>
      <div v-if="expanded" class="mt-2 pt-2 border-t border-border space-y-1 text-text-secondary">
        <div>文档: <span class="text-text">{{ stats.docs }}</span></div>
        <div>Wiki: <span class="text-text">{{ stats.wiki }}</span></div>
        <div>分类: <span class="text-text">{{ stats.cats }}</span></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'

const settings = useSettingsStore()
const connected = ref(false)
const expanded = ref(false)
const stats = ref({ docs: 0, wiki: 0, cats: 0 })
let interval = null

async function check() {
  try {
    const health = await settings.apiGet('/health')
    connected.value = health.status === 'ok'
    if (connected.value) {
      const docs = await settings.apiGet('/documents')
      const wiki = await settings.apiGet('/wiki/pages')
      const cats = await settings.apiGet('/categories')
      stats.value = { docs: docs.length || 0, wiki: wiki.length || 0, cats: cats.length || 0 }
    }
  } catch {
    connected.value = false
  }
}

onMounted(() => { check(); interval = setInterval(check, 30000) })
onUnmounted(() => clearInterval(interval))
</script>
