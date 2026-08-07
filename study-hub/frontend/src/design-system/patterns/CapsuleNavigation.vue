<template>
  <header class="capsule-navigation" data-visual-anchor="nav">
    <RouterLink class="capsule-navigation__brand" to="/" aria-label="Study Hub 首页">
      <span class="capsule-navigation__mark" aria-hidden="true">S</span>
      <strong>Study Hub</strong>
    </RouterLink>
    <nav aria-label="主导航" class="capsule-navigation__links">
      <RouterLink v-for="item in items" :key="item.to" :to="item.to" :class="{ 'is-active': item.to === '/' }">{{ item.label }}</RouterLink>
    </nav>
    <form class="capsule-navigation__search" role="search" @submit.prevent="$emit('search', searchText)">
      <input v-model="searchText" aria-label="搜索工作站内容" placeholder="搜索功能、文章与工作记录" @focus="$emit('search-focus')" @keydown.esc="$emit('search-close')" />
    </form>
    <UiButton class="capsule-navigation__notice" variant="quiet" size="sm" @click="$emit('notify')">通知</UiButton>
    <UiIconButton label="编辑首页" variant="primary" size="md" @click="$emit('edit')">章</UiIconButton>
  </header>
</template>

<script setup>
import UiButton from '../components/general/UiButton.vue'
import UiIconButton from '../components/general/UiIconButton.vue'

defineEmits(['search', 'search-focus', 'search-close', 'notify', 'edit'])
const searchText = defineModel('searchText', { type: String, default: '' })
const items = [
  { to: '/', label: '首页' }, { to: '/wiki', label: 'Wiki' }, { to: '/kb', label: '文档库' },
  { to: '/workflow', label: '自动化' }, { to: '/ddl', label: 'DDL' }, { to: '/journal', label: '手账' },
  { to: '/workflow', label: '工作流' }, { to: '/brainstorm', label: 'AI 对话' },
]
</script>

<style scoped>
.capsule-navigation { display: flex; width: min(1320px, calc(100vw - 120px)); height: 72px; box-sizing: border-box; align-items: center; gap: 10px; margin: 33px auto 0; border: 1px solid rgb(245 246 238 / 12%); border-radius: 36px; padding: 0 17px; background: rgb(17 20 15 / 90%); }
.capsule-navigation__brand { display: inline-flex; flex: 0 0 auto; align-items: center; gap: 12px; color: #f5f6ee; text-decoration: none; }
.capsule-navigation__brand strong { font-size: 15px; }
.capsule-navigation__mark { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 12px; background: #d7ff63; color: #11140f; font-weight: 800; }
.capsule-navigation__links { display: flex; min-width: 0; align-items: center; gap: 8px; margin-left: 4px; }
.capsule-navigation__links a { display: inline-flex; height: 34px; box-sizing: border-box; align-items: center; border: 1px solid rgb(245 246 238 / 10%); border-radius: 18px; padding: 0 14px; background: #252824; color: #d9ddcf; font-size: 12px; text-decoration: none; white-space: nowrap; }
.capsule-navigation__links a:hover, .capsule-navigation__links a.is-active { background: #d7ff63; color: #11140f; }
.capsule-navigation__search { min-width: 180px; margin-left: auto; }
.capsule-navigation__search input { width: 100%; height: 40px; box-sizing: border-box; border: 0; border-radius: 22px; padding: 0 17px; background: #252824; color: #f5f6ee; outline: none; font: 12px var(--ui-font-sans); }
.capsule-navigation__search input:focus { box-shadow: var(--ui-focus-ring); }
.capsule-navigation__notice { flex: 0 0 auto; border-radius: 22px !important; }
@media (max-width: 1100px) { .capsule-navigation { width: calc(100vw - 48px); min-width: 1010px; margin-left: 24px; } .capsule-navigation__links { gap: 3px; } .capsule-navigation__links a { padding: 0 9px; } }
</style>
