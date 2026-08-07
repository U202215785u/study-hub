<template>
  <DashboardModuleCard data-figma-node="349:471" title="知识库" :loading="loading" :error="error">
    <div class="knowledge-widget">
      <UiCompactHeader title="知识库" to="/kb" size="md">
        <template #action>
          <UiButton class="knowledge-widget__more" data-knowledge-more size="xs" shape="pill" variant="text" @click="$emit('open-all')">展开全部</UiButton>
        </template>
      </UiCompactHeader>
      <UiInsetSurface v-if="!visibleItems.length" class="knowledge-widget__empty"><p>知识库暂无文档</p></UiInsetSurface>
      <UiInsetSurface v-for="item in visibleItems" :key="item.id" class="knowledge-widget__row" interactive>
        <button type="button" class="knowledge-widget__title" :data-knowledge-id="item.id" @click="$emit('open', item.id)"><span>{{ item.title }}</span></button>
        <template #actions>
          <UiButton v-if="item.status === 'error'" class="knowledge-widget__delete" :data-remove-id="item.id" size="xs" shape="pill" variant="danger" @click="$emit('remove', item.id)">删除</UiButton>
          <UiButton :data-copy-id="item.id" size="xs" shape="pill" @click="$emit('copy', item.id)">复制</UiButton>
        </template>
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

const props = defineProps({ items: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['open', 'open-all', 'copy', 'remove'])
const visibleItems = computed(() => props.items.slice(0, 2))
</script>

<style scoped>
.knowledge-widget { display: grid; height: 100%; min-height: 0; box-sizing: border-box; grid-template-rows: 22px repeat(2, minmax(0, 1fr)); gap: 7px; }
.knowledge-widget__empty { grid-row: 2 / 4; }
.knowledge-widget__empty p { margin: 0; color: var(--ui-color-text-muted); font-size: 11px; }
.knowledge-widget__row { padding-right: 7px; padding-left: 10px; }
.knowledge-widget__more { min-height: 22px; padding-right: 4px; padding-left: 4px; }
.knowledge-widget__title { min-width: 0; width: 100%; overflow: hidden; border: 0; padding: 0; background: transparent; color: var(--ui-color-text); text-align: left; cursor: pointer; }
.knowledge-widget__title span { display: block; overflow: hidden; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.knowledge-widget__delete { pointer-events: none; opacity: 0; }
.knowledge-widget__row:hover .knowledge-widget__delete,
.knowledge-widget__row:focus-within .knowledge-widget__delete { pointer-events: auto; opacity: 1; }
</style>
