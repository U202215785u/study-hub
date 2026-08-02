<template>
  <nav class="app-nav" aria-label="主导航">
    <div class="app-nav__primary">
      <RouterLink v-for="item in primaryItems" :key="item.to" :to="item.to">{{ item.label }}</RouterLink>
    </div>
    <div class="app-nav__overflow-links">
      <RouterLink v-for="item in overflowItems" :key="item.to" :to="item.to">{{ item.label }}</RouterLink>
    </div>
    <details class="app-nav__menu">
      <summary aria-label="更多导航">更多</summary>
      <div class="app-nav__menu-panel" role="menu">
        <RouterLink v-for="item in overflowItems" :key="item.to" :to="item.to" role="menuitem">{{ item.label }}</RouterLink>
        <a href="/second-self/index.html" role="menuitem">自我</a>
      </div>
    </details>
  </nav>
</template>

<script setup>
const primaryItems = [
  { to: '/', label: '首页' },
  { to: '/kb', label: '知识库' },
  { to: '/learning', label: '学习' },
  { to: '/workflow', label: '工作流' },
  { to: '/creator', label: '创作' },
]
const overflowItems = [
  { to: '/memory', label: '记忆' },
  { to: '/ddl', label: 'DDL' },
  { to: '/sop', label: 'SOP' },
  { to: '/skills', label: 'Skill' },
  { to: '/journal', label: '手账' },
  { to: '/workbench', label: '工作台' },
  { to: '/settings', label: '设置' },
]
</script>

<style scoped>
.app-nav { display: flex; min-width: 0; align-items: center; justify-content: flex-end; gap: var(--ui-space-4); }
.app-nav__primary, .app-nav__overflow-links { display: flex; min-width: 0; align-items: center; gap: var(--ui-space-1); }
.app-nav a, .app-nav__menu summary { display: inline-flex; min-height: 36px; box-sizing: border-box; align-items: center; border-radius: var(--ui-radius-sm); padding: 0 var(--ui-space-3); color: var(--ui-color-text-muted); font: 700 12px/1 var(--ui-font-sans); text-decoration: none; cursor: pointer; white-space: nowrap; }
.app-nav a:hover, .app-nav a:focus-visible, .app-nav__menu summary:hover, .app-nav__menu summary:focus-visible { outline: none; background: var(--ui-color-surface-raised); color: var(--ui-color-text-strong); }
.app-nav a.router-link-active { background: color-mix(in srgb, var(--ui-color-action) 14%, transparent); color: var(--ui-color-action); }
.app-nav__menu { position: relative; display: none; }
.app-nav__menu summary { list-style: none; }
.app-nav__menu summary::-webkit-details-marker { display: none; }
.app-nav__menu-panel { position: absolute; z-index: 40; top: calc(100% + var(--ui-space-2)); right: 0; display: grid; width: 180px; border: 1px solid var(--ui-color-border-strong); border-radius: var(--ui-radius-md); padding: var(--ui-space-2); background: var(--ui-color-surface); box-shadow: var(--ui-shadow-overlay); }
@media (max-width: 1279px) { .app-nav__overflow-links { display: none; } .app-nav__menu { display: block; } }
@media (max-width: 767px) { .app-nav__primary a:nth-child(n + 4) { display: none; } .app-nav { gap: var(--ui-space-1); } .app-nav a, .app-nav__menu summary { padding: 0 var(--ui-space-2); font-size: 11px; } }
</style>
