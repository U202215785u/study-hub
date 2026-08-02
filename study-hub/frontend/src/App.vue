<template>
  <RouterView v-if="isFullScreenRoute" />
  <UiAppShell v-else>
    <template #brand>
      <RouterLink class="app-brand" to="/" aria-label="Study Hub 首页">
        <span class="app-brand__mark" aria-hidden="true">S</span>
        <span>Study Hub</span>
      </RouterLink>
    </template>
    <template #topNavigation><NavBar /></template>
    <RouterView />
    <template #dock>
      <section class="app-dock" aria-label="系统状态">
        <p>WORKSPACE STATUS</p>
        <SystemStatus />
      </section>
    </template>
  </UiAppShell>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { UiAppShell } from '@study-ui'
import NavBar from './components/NavBar.vue'
import SystemStatus from './components/SystemStatus.vue'

const route = useRoute()
const isFullScreenRoute = computed(() => route.path === '/' || route.path.startsWith('/wiki') || route.path.startsWith('/kb'))
</script>

<style scoped>
.app-brand { display: inline-flex; align-items: center; gap: var(--ui-space-2); color: var(--ui-color-text-strong); font: 800 14px/1 var(--ui-font-sans); text-decoration: none; white-space: nowrap; }
.app-brand__mark { display: grid; width: 28px; height: 28px; place-items: center; border-radius: var(--ui-radius-sm); background: var(--ui-color-action); color: var(--ui-color-action-text); }
.app-dock { display: grid; gap: var(--ui-space-4); padding: var(--ui-space-5); }
.app-dock > p { margin: 0; color: var(--ui-color-text-muted); font: 700 10px/1 var(--ui-font-mono); letter-spacing: 0; }
</style>
