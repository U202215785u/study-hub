<template>
  <UiWidgetFrame data-figma-node="349:493" title="继续创作" :meta="`${items.length} 个`" :loading="loading" :error="error" :empty="!items.length && !loading && !error" empty-title="还没有创作内容" empty-description="从一个模板开始，把想法变成作品。">
    <div class="creation-grid">
      <button v-for="item in items" :key="item.id" class="creation-card" :data-creation-id="item.id" type="button" @click="emit('open', item.id)">
        <span class="creation-card__preview"><img v-if="item.thumbnail" :src="item.thumbnail" :alt="item.title" /><span v-else aria-hidden="true">{{ kindLabel(item.kind) }}</span></span>
        <span class="creation-card__title">{{ item.title }}</span>
      </button>
    </div>
  </UiWidgetFrame>
</template>

<script setup>
import UiWidgetFrame from '../patterns/UiWidgetFrame.vue'
defineProps({ items: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['open'])
const kindLabel = (kind) => ({ article: '文章', video: '视频', note: '笔记', template: '模板' }[kind] || '创作')
</script>

<style scoped>
.creation-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ui-space-3); }
.creation-card { display: grid; min-width: 0; gap: var(--ui-space-2); border: 0; padding: 0; background: transparent; color: inherit; text-align: left; cursor: pointer; }
.creation-card:focus-visible { outline: 2px solid var(--ui-color-action); outline-offset: 3px; border-radius: var(--ui-radius-md); }
.creation-card__preview { display: grid; min-height: 96px; place-items: center; overflow: hidden; border-radius: var(--ui-radius-md); background: var(--ui-color-content-orange); color: var(--ui-color-content-cream); font-weight: 700; }
.creation-card:nth-child(2n) .creation-card__preview { background: var(--ui-color-content-purple); }
.creation-card__preview img { width: 100%; height: 100%; object-fit: cover; }
.creation-card__title { overflow: hidden; color: var(--ui-color-text-strong); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
</style>
