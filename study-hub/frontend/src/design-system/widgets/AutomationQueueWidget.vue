<template>
  <DashboardModuleCard data-figma-node="349:369" title="文章解析" :loading="loading" :error="error">
    <div class="queue-widget">
      <UiCompactHeader class="queue-widget__title" title="文章解析" to="/content-parser" size="md" />
      <UiInsetSurface v-for="(item, index) in rowItems" :key="item?.id || `empty-${index}`" class="queue-widget__row" :data-queue-row="index" :data-empty="item ? undefined : true" :interactive="Boolean(item)">
        <div v-if="item" class="queue-widget__item">
          <button type="button" :data-queue-id="item.id" @click="$emit('open', item.id)">
            <span><strong>{{ item.title }}</strong><b :data-status="item.status">{{ statusLabel(item.status) }}</b></span>
          </button>
          <UiProgress :value="item.progress" size="compact" :status="progressStatus(item.status)" :aria-label="item.progressText" />
        </div>
        <div v-else class="queue-widget__placeholder" aria-hidden="true"><span/><i/></div>
        <template #actions>
          <UiButton v-if="item?.status === 'error'" :data-retry-id="item.id" size="xs" shape="pill" variant="text" @click="$emit('retry', item.id)">Retry</UiButton>
        </template>
      </UiInsetSurface>
      <UiButton class="queue-widget__more" size="xs" shape="pill" variant="text" @click="$emit('open')">View queue</UiButton>
      <label class="queue-widget__input" data-queue-input>
        <span class="sr-only">Automation URL</span>
        <input v-model="inputValue" type="url" data-queue-input placeholder="Paste a video URL" @keyup.enter="submit" />
      </label>
      <UiButton class="queue-widget__start" data-queue-create size="xs" shape="pill" @click="$emit('create', inputValue.trim())">开始解析</UiButton>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { normalizeAutomationTask } from '../../composables/home/automationQueueContract'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import UiProgress from '../components/data-display/UiProgress.vue'
import UiButton from '../components/general/UiButton.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
  loading: Boolean,
  error: { type: String, default: '' },
})
const emit = defineEmits(['open', 'retry', 'create', 'update:modelValue', 'submit'])
const localInputValue = ref(props.modelValue)
watch(() => props.modelValue, (value) => { localInputValue.value = value })
const inputValue = computed({
  get: () => localInputValue.value,
  set: (value) => {
    localInputValue.value = value
    emit('update:modelValue', value)
  },
})
const visibleItems = computed(() => props.items.slice(0, 3).map(normalizeAutomationTask))
const rowItems = computed(() => Array.from({ length: 3 }, (_, index) => visibleItems.value[index] || null))
const statusLabel = (status) => ({
  pending: 'Pending',
  extracting: 'Extracting',
  summarizing: 'Summarizing',
  importing: 'Importing',
  running: 'Running',
  done: 'Done',
  error: 'Error',
}[status] || 'Pending')
const progressStatus = (status) => status === 'error' ? 'danger' : status === 'done' ? 'success' : 'active'
const submit = () => emit('submit', inputValue.value.trim())
</script>

<style scoped>
.queue-widget{display:grid;height:100%;min-height:0;grid-template-rows:25px repeat(3,43px) 24px 42px 30px;gap:6px}.queue-widget__title{align-self:center;margin:0}.queue-widget__row{position:relative;min-width:0;box-sizing:border-box}.queue-widget__row :deep(.ui-inset-surface__content){display:grid;height:100%;min-height:0;grid-template-rows:1fr 5px;gap:5px}.queue-widget__item{display:contents}.queue-widget__row button{display:block;width:100%;height:100%;min-width:0;border:0;padding:0;background:none;color:#f5f6ee;text-align:left;cursor:pointer}.queue-widget__row button>span{display:flex;min-width:0;align-items:center;justify-content:space-between;gap:8px}.queue-widget strong{overflow:hidden;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.queue-widget b{flex:0 0 auto;color:#d9ddcf;font-size:10px}.queue-widget b[data-status='done']{color:#d7ff63}.queue-widget b[data-status='error']{color:#ff6b78}.queue-widget__placeholder{display:grid;height:100%;box-sizing:border-box;align-content:center;gap:7px;padding:7px 9px}.queue-widget__placeholder span{display:block;width:52%;height:6px;border-radius:3px;background:#242824}.queue-widget__placeholder i{display:block;width:72%;height:5px;border-radius:3px;background:#29351d}.queue-widget__more{justify-self:end}.queue-widget__input{display:flex;min-width:0;align-items:center;border:1px dashed #585858;border-radius:5px;padding:0 11px;color:var(--ui-color-text-muted);font-size:11px}.queue-widget__input input{width:100%;min-width:0;border:0;outline:0;background:transparent;color:inherit;font:inherit}.queue-widget__input input::placeholder{color:inherit}.queue-widget__start{justify-self:end}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
</style>
