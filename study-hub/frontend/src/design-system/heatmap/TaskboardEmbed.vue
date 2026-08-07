<template>
  <section v-if="compact" class="taskboard-compact" data-taskboard-compact><strong>Codex Taskboard</strong><span>study-hub 项目任务版</span><RouterLink to="/heatmap?view=taskboard">进入详情</RouterLink></section>
  <section v-else class="taskboard-full"><header :data-status="status"><span>{{ label }}</span><a :href="url" target="_blank" rel="noopener noreferrer">打开完整任务版</a></header><iframe :key="key" :src="url" title="Codex Taskboard study-hub" @load="loaded" @error="offline" /><button v-if="status === 'offline'" type="button" @click="retry">重试</button></section>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
const props = defineProps({ compact: Boolean })
const url = 'http://127.0.0.1:47823/?project=study-hub'; const status = ref('idle'); const key = ref(0); let timer
const label = computed(() => status.value === 'offline' ? 'Codex Taskboard 当前不可用' : status.value === 'loading' ? '正在连接 Codex Taskboard…' : 'Codex Taskboard · study-hub')
function clear() { clearTimeout(timer); timer = null }
function begin() { clear(); status.value = 'loading'; timer = setTimeout(offline, 8000) }
function loaded() { clear(); status.value = 'available' }
function offline() { clear(); status.value = 'offline' }
function retry() { key.value += 1; begin() }
onMounted(() => { if (!props.compact) begin() }); onBeforeUnmount(clear)
</script>
<style scoped>.taskboard-compact{display:flex;gap:10px;align-items:center;padding:18px}.taskboard-compact span{color:#8b9186;font-size:12px}.taskboard-compact a,header a,button{margin-left:auto;color:inherit}.taskboard-full{min-height:620px}.taskboard-full header{display:flex;gap:12px;align-items:center;margin-bottom:10px}.taskboard-full iframe{width:100%;min-height:560px;border:1px solid #3a4038;border-radius:8px;background:#10140f}header[data-status='offline']{color:#ff6b78}</style>
