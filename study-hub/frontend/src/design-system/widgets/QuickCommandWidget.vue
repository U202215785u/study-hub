<template>
  <DashboardModuleCard data-figma-node="349:510" title="快捷指令" :loading="loading" :error="error" :empty="!commands.length && !loading && !error">
    <div class="command-widget">
      <UiCompactHeader title="快捷指令" to="/settings" size="md" />
      <UiInsetSurface v-for="command in visibleCommands" :key="command.id" class="command-widget__row" interactive>
        <UiButton :data-command-id="command.id" class="command-widget__row-button" size="sm" variant="text" block @click="$emit('run', command.id)">{{ command.title }}</UiButton>
      </UiInsetSurface>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed } from 'vue'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import UiButton from '../components/general/UiButton.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'

const props = defineProps({ commands: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['run'])
const visibleCommands = computed(() => props.commands.slice(0, 2))
</script>

<style scoped>
.command-widget { display: grid; height: 100%; min-height: 0; box-sizing: border-box; grid-template-rows: 22px minmax(0, 1fr) minmax(0, 1fr); gap: 7px; }
.command-widget__row { padding: 0; }
.command-widget__row :deep(.ui-inset-surface__content) { height: 100%; }
.command-widget__row-button { height: 100%; min-height: 0; justify-content: flex-start; text-align: left; }
</style>
