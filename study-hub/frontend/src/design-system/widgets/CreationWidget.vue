<template>
  <DashboardModuleCard data-figma-node="349:493" title="创作入口" :loading="loading" :error="error" :empty="!items.length && !loading && !error">
    <div class="creation-widget">
      <UiCompactHeader title="创作入口" to="/creator" size="md" />
      <nav><UiPillButton data-creation-action="drafts" @click="emit('open', 'drafts')">草稿箱</UiPillButton><UiPillButton data-creation-action="publish" active @click="emit('open', 'publish')">一键发布</UiPillButton></nav>
      <button v-for="item in visibleItems" :key="item.id" type="button" :data-creation-id="item.id" @click="$emit('open', item.id)">
        <UiInsetSurface class="creation-widget__title-surface">{{ item.title }}</UiInsetSurface>
        <i><b v-for="n in 3" :key="n">创</b></i>
      </button>
    </div>
  </DashboardModuleCard>
</template>
<script setup>
import { computed } from 'vue'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiInsetSurface from '../components/data-display/UiInsetSurface.vue'
import UiPillButton from '../components/general/UiPillButton.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'

const props = defineProps({ items: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['open'])
const visibleItems = computed(() => props.items.slice(0, 2))
</script>

<style scoped>
.creation-widget { display: grid; height: 100%; min-height: 0; box-sizing: border-box; grid-template-rows: 23px 29px repeat(2, minmax(0, 1fr)); gap: 9px; }
.creation-widget nav { display: flex; min-width: 0; align-items: stretch; gap: 8px; }
.creation-widget > button { display: grid; min-height: 0; grid-template-rows: 36px 40px; gap: 8px; border: 0; padding: 0; background: none; color: var(--ui-color-text); text-align: left; cursor: pointer; transition: transform var(--ui-duration-fast) var(--ui-ease-standard); }
.creation-widget__title-surface { font-size: 11px; }
.creation-widget i { display: flex; min-height: 0; align-items: center; gap: 6px; }
.creation-widget b { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 8px; background: linear-gradient(145deg, #fa6b8d, #ed2457); color: white; font-size: 10px; }
@media (hover: hover) and (pointer: fine) { .creation-widget > button:hover { transform: translateY(-2px); } }
</style>
