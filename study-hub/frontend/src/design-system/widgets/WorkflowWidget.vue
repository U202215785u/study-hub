<template>
  <DashboardModuleCard data-figma-node="349:459" title="快捷工作流" :loading="loading" :error="error" :empty="!steps.length && !loading && !error">
    <div class="workflow-widget">
      <UiCompactHeader title="快捷工作流-网页爬取" to="/workflow" size="md" />
      <ol><li v-for="(step, index) in visibleSteps" :key="step.id"><UiPillButton :data-run-id="step.id" :active="index === 0" @click="$emit('run', step.id)">{{ step.label }}</UiPillButton><b v-if="index < visibleSteps.length - 1">→</b></li></ol>
      <UiInsetSurface class="workflow-widget__field"><label><span>输入网址</span><input aria-label="输入网址" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" @keydown.enter="$emit('run', visibleSteps[0]?.id, $event.target.value)" /></label></UiInsetSurface>
    </div>
  </DashboardModuleCard>
</template>
<script setup>
import { computed } from 'vue'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import UiPillButton from '../components/general/UiPillButton.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'

const props = defineProps({ steps: { type: Array, default: () => [] }, modelValue: { type: String, default: '' }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['run', 'update:modelValue'])
const visibleSteps = computed(() => props.steps.slice(0, 3))
</script>

<style scoped>
.workflow-widget { display: grid; height: 100%; min-height: 0; box-sizing: border-box; grid-template-rows: 22px 29px minmax(0, 1fr); gap: 7px; }
.workflow-widget ol { display: flex; min-width: 0; align-items: center; margin: 0; padding: 0; list-style: none; }
.workflow-widget li { display: flex; min-width: 0; align-items: center; gap: 7px; }
.workflow-widget li b { margin-right: 7px; color: var(--ui-color-text-muted); font-size: 20px; }
.workflow-widget__field { padding: 0 10px; }
.workflow-widget__field :deep(.ui-inset-surface__content) { height: 100%; }
.workflow-widget label { position: relative; display: block; width: 100%; height: 100%; min-height: 0; overflow: hidden; }
.workflow-widget label span { position: absolute; top: 50%; transform: translateY(-50%); color: var(--ui-color-text-muted); font-size: 11px; white-space: nowrap; }
.workflow-widget input { width: 100%; height: 100%; box-sizing: border-box; border: 0; padding-left: 57px; background: transparent; color: var(--ui-color-text-strong); outline: none; }
</style>
