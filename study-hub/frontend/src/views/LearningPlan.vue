<template>
  <div>
    <div v-if="loading" class="text-center py-16 text-text-secondary">加载中…</div>
    <div v-else-if="error" class="text-center py-16 text-text-secondary">加载失败，请返回重试</div>
    <div v-else>
      <MarkdownRenderer :content="mdContent" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import { useSettingsStore } from '../stores/settings.js'

const route = useRoute()
const settings = useSettingsStore()
const loading = ref(true)
const error = ref(false)
const mdContent = ref('')

async function fetchModsPath(path) {
  const apiBase = settings.apiBase
  const res = await fetch(`${apiBase}${path}`)
  return res
}

onMounted(async () => {
  const planId = route.query.plan
  if (!planId) { error.value = true; loading.value = false; return }

  try {
    const plans = await settings.apiGet('/learning/plans')
    let plan = plans.find(p => p.id === planId)
    if (!plan) plan = plans.find(p => p.id.includes(planId) || planId.includes(p.id))
    if (!plan) throw new Error('not found')

    // /mods/learning 需要通过 apiBase 拼接 (不是 /api 前缀)
    const modsPath = `/mods/learning/${encodeURIComponent(plan.file)}`
    const mdRes = await fetchModsPath(modsPath)
    if (!mdRes.ok) throw new Error('404')
    const md = await mdRes.text()
    mdContent.value = md
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>
