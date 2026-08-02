<template>
  <UiWidgetFrame data-figma-node="349:459" title="学习流程" :meta="progressLabel" :loading="loading" :error="error" :empty="!steps.length && !loading && !error" empty-title="还没有流程步骤" empty-description="把重复的学习动作串成一条流程。">
    <ol class="workflow" aria-label="学习流程">
      <li v-for="(step, index) in steps" :key="step.id" class="workflow__step" :data-status="step.status">
        <span class="workflow__connector" v-if="index < steps.length - 1" aria-hidden="true" />
        <button class="workflow__node" :data-run-id="step.id" type="button" :aria-label="`运行${step.label}`" @click="emit('run', step.id)">{{ index + 1 }}</button>
        <span class="workflow__label">{{ step.label }}</span>
      </li>
    </ol>
  </UiWidgetFrame>
</template>

<script setup>
import { computed } from 'vue'
import UiWidgetFrame from '../patterns/UiWidgetFrame.vue'

const props = defineProps({ steps: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['run'])
const progressLabel = computed(() => `${props.steps.filter((step) => step.status === 'done').length}/${props.steps.length || 0}`)
</script>

<style scoped>
.workflow { display: flex; min-width: 0; margin: 0; padding: var(--ui-space-4) 0; list-style: none; }
.workflow__step { position: relative; display: grid; min-width: 0; flex: 1 1 0; justify-items: center; gap: var(--ui-space-2); }
.workflow__connector { position: absolute; z-index: 0; top: 15px; right: 50%; width: 100%; height: 2px; background: var(--ui-color-surface-muted); }
.workflow__step[data-status='done'] .workflow__connector { background: var(--ui-color-success); }
.workflow__node { position: relative; z-index: 1; display: grid; width: 30px; height: 30px; place-items: center; border: 2px solid var(--ui-color-border-strong); border-radius: 50%; background: var(--ui-color-surface); color: var(--ui-color-text-muted); font: 700 12px/1 var(--ui-font-sans); cursor: pointer; }
.workflow__node:hover, .workflow__node:focus-visible { outline: none; border-color: var(--ui-color-action); box-shadow: var(--ui-focus-ring); }
.workflow__step[data-status='done'] .workflow__node { border-color: var(--ui-color-success); background: var(--ui-color-success); color: var(--ui-color-canvas); }
.workflow__step[data-status='running'] .workflow__node { border-color: var(--ui-color-action); color: var(--ui-color-action); }
.workflow__label { max-width: 100%; overflow: hidden; color: var(--ui-color-text-muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.workflow__step[data-status='done'] .workflow__label, .workflow__step[data-status='running'] .workflow__label { color: var(--ui-color-text-strong); }
</style>
