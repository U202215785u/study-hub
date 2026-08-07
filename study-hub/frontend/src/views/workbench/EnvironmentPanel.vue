<template>
  <section class="workbench-panel environment-panel" aria-labelledby="environment-title">
    <header class="panel-header">
      <div>
        <p class="eyebrow">只读信息</p>
        <h2 id="environment-title">环境信息</h2>
        <p class="panel-description">展示后端返回的脱敏运行环境与健康检查结果。</p>
      </div>
      <span v-if="environment" class="status-badge" :class="statusClass(environment.status)">
        {{ statusLabel(environment.status) }}
      </span>
    </header>

    <div v-if="loading" class="panel-state" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      <span>正在加载环境信息</span>
    </div>

    <div v-else-if="error" class="panel-state panel-state-error" role="alert">
      <strong>环境信息加载失败</strong>
      <span>{{ error.message }}</span>
      <button type="button" class="retry-button" title="重试加载环境信息" @click="load">
        <span aria-hidden="true">↻</span>
        重试
      </button>
    </div>

    <div v-else-if="environment" class="panel-content">
      <div
        v-if="environment.status === 'degraded' || environment.status === 'error'"
        class="health-notice"
        :class="statusClass(environment.status)"
        role="status"
      >
        <strong>健康状态：{{ statusLabel(environment.status) }}</strong>
        <span>{{ environment.status === 'error' ? '当前环境存在异常，请查看下方检查项。' : '部分检查项需要关注。' }}</span>
      </div>

      <div class="data-grid">
        <section class="data-section" aria-labelledby="runtime-title">
          <h3 id="runtime-title">运行时</h3>
          <dl class="field-list">
            <div><dt>Python 版本</dt><dd>{{ value(environment.runtime?.python_version) }}</dd></div>
            <div><dt>平台</dt><dd>{{ value(environment.runtime?.platform) }}</dd></div>
            <div><dt>实现</dt><dd>{{ value(environment.runtime?.implementation) }}</dd></div>
          </dl>
        </section>

        <section class="data-section" aria-labelledby="health-title">
          <h3 id="health-title">健康检查</h3>
          <dl class="field-list">
            <div><dt>总体状态</dt><dd><span class="inline-status" :class="statusClass(environment.health?.status)">{{ statusLabel(environment.health?.status) }}</span></dd></div>
            <div v-for="check in healthChecks" :key="check.name">
              <dt>{{ check.name }}</dt>
              <dd><span class="inline-status" :class="statusClass(check.status)">{{ statusLabel(check.status) }}</span></dd>
            </div>
          </dl>
          <p v-if="!healthChecks.length" class="muted">暂无检查项</p>
        </section>

        <section class="data-section" aria-labelledby="paths-title">
          <h3 id="paths-title">项目路径</h3>
          <dl class="field-list">
            <div><dt>项目根目录</dt><dd>{{ value(environment.paths?.project_root) }}</dd></div>
            <div><dt>后端目录</dt><dd>{{ value(environment.paths?.backend) }}</dd></div>
          </dl>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getEnvironment } from '../../services/workbenchEnvironment.js'

const environment = ref(null)
const loading = ref(true)
const error = ref(null)

const healthChecks = computed(() => {
  const checks = environment.value?.health?.checks
  if (!checks || typeof checks !== 'object' || Array.isArray(checks)) return []
  return Object.entries(checks)
    .filter(([, check]) => check && typeof check === 'object')
    .map(([name, check]) => ({ name, status: check.status }))
})

function statusLabel(status) {
  return { ok: '正常', degraded: '降级', error: '异常' }[status] || '未知'
}

function statusClass(status) {
  return {
    'status-ok': status === 'ok',
    'status-degraded': status === 'degraded',
    'status-error': status === 'error',
    'status-unknown': !['ok', 'degraded', 'error'].includes(status),
  }
}

function value(field) {
  return field === null || field === undefined || field === '' ? '未提供' : field
}

async function load() {
  loading.value = true
  error.value = null
  try {
    environment.value = await getEnvironment()
  } catch (cause) {
    environment.value = null
    error.value = cause instanceof Error ? cause : new Error('无法读取环境信息')
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
h2, h3, p { margin-top: 0; }
h2 { margin-bottom: 6px; font-size: 22px; line-height: 1.25; }
h3 { margin-bottom: 14px; font-size: 14px; }
.panel-description, .muted { margin-bottom: 0; color: #8888a0; font-size: 13px; }
.status-badge, .inline-status { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; border: 1px solid currentColor; font-size: 12px; font-weight: 600; }
.status-badge { border-radius: 999px; padding: 5px 10px; }
.inline-status { border-radius: 999px; padding: 2px 7px; }
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
.health-notice { display: grid; gap: 3px; margin-bottom: 20px; padding: 12px 14px; border-left: 3px solid currentColor; background: rgba(251, 191, 36, .08); }
.health-notice span { color: #c4c4d0; font-size: 13px; }
.health-notice.status-error { background: rgba(251, 113, 133, .08); }
.data-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.data-section { min-width: 0; padding: 16px; border: 1px solid #2a2a3a; border-radius: 8px; background: #1a1a24; }
.field-list { display: grid; gap: 12px; margin: 0; }
.field-list > div { min-width: 0; display: grid; gap: 3px; }
dt { color: #8888a0; font-size: 12px; }
dd { margin: 0; color: #e0e0e8; font-size: 13px; overflow-wrap: anywhere; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 720px) {
  .panel-header { display: grid; }
  .status-badge { justify-self: start; }
  .data-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>

