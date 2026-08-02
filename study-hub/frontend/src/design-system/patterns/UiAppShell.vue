<template>
  <div class="ui-app-shell" :data-dock-open="dockOpen ? 'true' : undefined">
    <header class="ui-app-shell__topbar">
      <div v-if="$slots.brand" class="ui-app-shell__brand"><slot name="brand" /></div>
      <nav class="ui-app-shell__nav" aria-label="主导航"><slot name="topNavigation" /></nav>
      <button v-if="$slots.dock" class="ui-app-shell__dock-trigger" type="button" :aria-expanded="dockOpen" aria-controls="study-ui-dock" @click="dockOpen = !dockOpen">
        快捷工具
      </button>
    </header>
    <div class="ui-app-shell__layout">
      <aside v-if="$slots.sidebar" class="ui-app-shell__sidebar" aria-label="辅助导航"><slot name="sidebar" /></aside>
      <main class="ui-app-shell__main"><slot /></main>
      <aside v-if="$slots.dock" id="study-ui-dock" class="ui-app-shell__dock" aria-label="快捷工具"><slot name="dock" /></aside>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const dockOpen = ref(false)
</script>

<style scoped>
.ui-app-shell { min-height: 100vh; background: var(--ui-color-canvas); color: var(--ui-color-text); }
.ui-app-shell__topbar { position: sticky; z-index: 20; top: 0; display: flex; min-height: 64px; align-items: center; gap: var(--ui-space-5); border-bottom: 1px solid var(--ui-color-border); padding: 0 var(--ui-space-6); background: color-mix(in srgb, var(--ui-color-shell) 94%, transparent); backdrop-filter: blur(16px); }
.ui-app-shell__brand { flex: 0 0 auto; }
.ui-app-shell__nav { min-width: 0; flex: 1 1 auto; }
.ui-app-shell__layout { display: grid; min-height: calc(100vh - 64px); grid-template-columns: minmax(0, 1fr); }
.ui-app-shell__sidebar { min-width: 0; border-right: 1px solid var(--ui-color-border); background: var(--ui-color-shell); }
.ui-app-shell__main { min-width: 0; padding: var(--ui-space-6); }
.ui-app-shell__dock { min-width: 0; border-left: 1px solid var(--ui-color-border); background: var(--ui-color-shell); }
.ui-app-shell__dock-trigger { display: none; min-height: 36px; border: 1px solid var(--ui-color-border-strong); border-radius: var(--ui-radius-md); padding: 0 var(--ui-space-3); background: var(--ui-color-surface); color: var(--ui-color-text-strong); font: 700 12px/1 var(--ui-font-sans); cursor: pointer; }
.ui-app-shell__dock-trigger:focus-visible { outline: none; box-shadow: var(--ui-focus-ring); }
@media (min-width: 768px) { .ui-app-shell__layout:has(.ui-app-shell__sidebar) { grid-template-columns: 224px minmax(0, 1fr); } }
@media (min-width: 1024px) and (max-width: 1279px) {
  .ui-app-shell__dock-trigger { display: inline-flex; align-items: center; }
  .ui-app-shell__dock { position: fixed; z-index: 30; top: 64px; right: 0; bottom: 0; display: none; width: min(360px, 90vw); box-shadow: var(--ui-shadow-overlay); }
  .ui-app-shell[data-dock-open='true'] .ui-app-shell__dock { display: block; }
}
@media (max-width: 1023px) { .ui-app-shell__dock { display: none; } }
@media (min-width: 1280px) { .ui-app-shell__layout:has(.ui-app-shell__dock) { grid-template-columns: minmax(0, 1fr) 320px; } .ui-app-shell__layout:has(.ui-app-shell__sidebar):has(.ui-app-shell__dock) { grid-template-columns: 224px minmax(0, 1fr) 320px; } }
@media (max-width: 767px) { .ui-app-shell__topbar { min-height: 56px; padding: 0 var(--ui-space-4); } .ui-app-shell__main { padding: var(--ui-space-4); } .ui-app-shell__layout { min-height: calc(100vh - 56px); } }
</style>
