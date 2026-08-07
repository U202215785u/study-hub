<template>
  <section class="workbench-panel roadmap-panel" aria-labelledby="roadmap-title">
    <header class="panel-header">
      <div>
        <p class="eyebrow">只读信息</p>
        <h2 id="roadmap-title">项目规划</h2>
        <p class="panel-description">按 API 返回的规划分区、来源和文件时间展示 Markdown 内容。</p>
      </div>
      <span v-if="roadmap" class="status-badge" :class="roadmapStatusClass">
        {{ roadmapStatusLabel }}
      </span>
    </header>

    <div v-if="loading" class="panel-state" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      <span>正在加载项目规划</span>
    </div>

    <div v-else-if="error" class="panel-state panel-state-error" role="alert">
      <strong>项目规划加载失败</strong>
      <span>{{ error.message }}</span>
      <button type="button" class="retry-button" title="重试加载项目规划" @click="load">
        <span aria-hidden="true">↻</span>
        重试
      </button>
    </div>

    <div v-else-if="roadmap" class="panel-content">
      <div v-if="isMissing" class="empty-state" role="status">
        <strong>暂无项目规划文件</strong>
        <span>API 未返回可展示的规划文件，当前不会生成占位内容。</span>
      </div>

      <div v-else-if="roadmap.status === 'error'" class="health-notice status-error" role="alert">
        <strong>项目规划文件读取异常</strong>
        <span>来源文件存在，但 API 未能读取其内容。</span>
        <button type="button" class="retry-button" title="重试读取项目规划" @click="load">
          <span aria-hidden="true">↻</span>
          重试
        </button>
      </div>

      <template v-else>
        <dl class="source-grid">
          <div v-if="sectionName"><dt>规划分区</dt><dd>{{ sectionName }}</dd></div>
          <div><dt>来源</dt><dd>{{ displaySource }}</dd></div>
          <div><dt>最后更新时间（updated_at）</dt><dd>{{ displayUpdatedAt }}</dd></div>
          <div><dt>文件时间（mtime）</dt><dd>{{ displayMtime }}</dd></div>
        </dl>

        <div v-if="hasContent" class="markdown-shell">
          <MarkdownRenderer :content="roadmap.content" />
        </div>
        <div v-else class="empty-state compact" role="status">
          <strong>规划内容为空</strong>
          <span>API 已返回规划来源，但没有可渲染的 Markdown 内容。</span>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import MarkdownRenderer from '../../components/MarkdownRenderer.vue'
import { getRoadmap } from '../../services/workbenchEnvironment.js'

const roadmap = ref(null)
const loading = ref(true)
const error = ref(null)

const isMissing = computed(() => roadmap.value?.missing === true || roadmap.value?.status === 'missing')
const hasContent = computed(() => typeof roadmap.value?.content === 'string' && roadmap.value.content.trim().length > 0)
const displaySource = computed(() => roadmap.value?.source || roadmap.value?.relative_path || '未提供')
const sectionName = computed(() => {
  const source = typeof roadmap.value?.source === 'string' ? roadmap.value.source : ''
  const separator = source.indexOf('#')
  return separator >= 0 ? source.slice(separator + 1).trim() : ''
})
const displayUpdatedAt = computed(() => formatDate(roadmap.value?.updated_at))
const displayMtime = computed(() => formatDate(roadmap.value?.mtime, true))
const roadmapStatusLabel = computed(() => ({ available: '可用', missing: '缺失', error: '异常' }[roadmap.value?.status] || '未知'))
const roadmapStatusClass = computed(() => ({
  'status-ok': roadmap.value?.status === 'available',
  'status-degraded': roadmap.value?.status === 'missing',
  'status-error': roadmap.value?.status === 'error',
  'status-unknown': !['available', 'missing', 'error'].includes(roadmap.value?.status),
}))

function formatDate(value, numericSeconds = false) {
  if (value === null || value === undefined || value === '') return '未提供'
  const candidate = numericSeconds && typeof value === 'number' ? value * 1000 : value
  const date = new Date(candidate)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString()
}

async function load() {
  loading.value = true
  error.value = null
  try {
    roadmap.value = await getRoadmap()
  } catch (cause) {
    roadmap.value = null
    error.value = cause instanceof Error ? cause : new Error('无法读取项目规划')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.workbench-panel { min-width: 0; color: #e0e0e8; }
.panel-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding-bottom: 18px; border-bottom: 1px solid #2a2a3a; }
.eyebrow { margin: 0 0 4px; color: #8888a0; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; }
h2, p { margin-top: 0; }
h2 { margin-bottom: 6px; font-size: 22px; line-height: 1.25; }
.panel-description, .empty-state span { margin-bottom: 0; color: #8888a0; font-size: 13px; }
.status-badge { display: inline-flex; align-items: center; white-space: nowrap; border: 1px solid currentColor; border-radius: 999px; padding: 5px 10px; font-size: 12px; font-weight: 600; }
.status-ok { color: #34d399; }
.status-degraded { color: #fbbf24; }
.status-error { color: #fb7185; }
.status-unknown { color: #a0a0b0; }
.panel-state { display: grid; justify-items: center; gap: 10px; padding: 48px 16px; color: #a0a0b0; text-align: center; }
.panel-state-error { color: #fb7185; }
.panel-state-error span:not([aria-hidden]) { color: #a0a0b0; overflow-wrap: anywhere; }
.spinner { width: 22px; height: 22px; border: 2px solid #3b3b50; border-top-color: #7c8aff; border-radius: 50%; animation: spin .8s linear infinite; }
.retry-button { display: inline-flex; align-items: center; gap: 6px; border: 1px solid #4b5563; border-radius: 6px; padding: 7px 12px; background: #1a1a24; color: #e0e0e8; cursor: pointer; }
.retry-button:hover, .retry-button:focus-visible { border-color: #7c8aff; color: #fff; }
.panel-content { padding-top: 20px; }
.empty-state { display: grid; justify-items: center; gap: 7px; min-height: 180px; align-content: center; padding: 24px; border: 1px dashed #4b5563; text-align: center; }
.empty-state strong { color: #e0e0e8; }
.empty-state.compact { min-height: 100px; }
.health-notice { display: grid; gap: 8px; padding: 14px; border-left: 3px solid currentColor; background: rgba(251, 113, 133, .08); }
.health-notice span { color: #c4c4d0; font-size: 13px; }
.source-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 0 0 20px; }
.source-grid > div { min-width: 0; padding: 12px; border: 1px solid #2a2a3a; border-radius: 8px; background: #1a1a24; }
dt { margin-bottom: 4px; color: #8888a0; font-size: 12px; }
dd { margin: 0; color: #e0e0e8; font-size: 13px; overflow-wrap: anywhere; }
.markdown-shell { min-width: 0; overflow: hidden; }
.markdown-shell :deep(.markdown-content) { max-width: 100%; padding: 28px 30px; overflow-x: auto; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 880px) { .source-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) {
  .panel-header { display: grid; }
  .status-badge { justify-self: start; }
  .source-grid { grid-template-columns: minmax(0, 1fr); }
  .markdown-shell :deep(.markdown-content) { padding: 22px 18px; }
}
</style>

