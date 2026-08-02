<template>
  <DashboardModuleCard data-figma-node="349:369" title="自动化队列" :loading="loading" :error="error">
    <div class="queue-widget">
      <button v-for="item in visibleItems" :key="item.id" type="button" :data-queue-id="item.id" @click="$emit('open', item.id)">
        <span><strong>{{ item.title }}</strong><b :data-status="item.status">{{ statusLabel(item.status) }}</b></span>
        <i><em :style="{ width: `${Math.max(8, item.progress || 0)}%` }" :data-status="item.status" /></i>
        <UiButton v-if="item.status === 'error'" :data-retry-id="item.id" size="sm" variant="text" @click.stop="$emit('retry', item.id)">重试</UiButton>
      </button>
      <div v-if="!visibleItems.length" class="queue-widget__empty">粘贴抖音分享链接...</div>
      <UiButton class="queue-widget__more" size="sm" variant="text" @click="$emit('open')">查看队列</UiButton>
      <UiButton class="queue-widget__start" size="sm" @click="$emit('create')">开始解析</UiButton>
    </div>
  </DashboardModuleCard>
</template>
<script setup>
import { computed } from 'vue'
import UiButton from '../components/general/UiButton.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ items: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['open', 'retry', 'create'])
const visibleItems = computed(() => props.items.slice(0, 3))
const statusLabel = (status) => ({ pending: '排队中', running: '处理中', done: '已完成', error: '失败' }[status] || '排队中')
</script>
<style scoped>
.queue-widget{display:grid;height:100%;box-sizing:border-box;align-content:start;gap:7px;padding:49px 13px 14px}.queue-widget>button:not(.queue-widget__more):not(.queue-widget__start){position:relative;display:grid;gap:7px;min-height:45px;border:1px solid rgb(245 246 238 / 20%);border-radius:6px;padding:7px;background:#171a16;color:#f5f6ee;text-align:left;cursor:pointer}.queue-widget>button>span{display:flex;align-items:center;justify-content:space-between;gap:8px}.queue-widget strong{overflow:hidden;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.queue-widget b{color:#d9ddcf;font-size:10px}.queue-widget b[data-status='done']{color:#d7ff63}.queue-widget b[data-status='error']{color:#ff6b78}.queue-widget i{display:block;height:5px;border-radius:4px;background:#29351d}.queue-widget em{display:block;height:100%;border-radius:4px;background:#d7ff63}.queue-widget em[data-status='error']{background:#ef5b65}.queue-widget__empty{position:absolute;right:13px;bottom:55px;left:13px;height:38px;box-sizing:border-box;border:1px dashed rgb(245 246 238 / 20%);border-radius:10px;padding:10px;color:#8b9186;font-size:11px}.queue-widget__more{position:absolute;right:13px;bottom:95px}.queue-widget__start{position:absolute;right:13px;bottom:14px;border-radius:18px!important}
</style>
