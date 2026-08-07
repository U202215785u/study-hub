<template>
  <section v-if="open" class="workstation-search-panel" role="dialog" aria-label="工作站搜索结果" @keydown.esc="$emit('close')">
    <p v-if="loading" class="workstation-search-panel__muted">正在搜索…</p>
    <div v-else-if="error" class="workstation-search-panel__error">
      <span>{{ error }}</span><button type="button" @click="$emit('retry')">重试</button>
    </div>
    <template v-else>
      <section v-for="group in groups" :key="group.id" class="workstation-search-panel__group">
        <h2>{{ group.label }}</h2>
        <div v-if="group.status === 'unavailable'" class="workstation-search-panel__error">
          <span>{{ group.message }}</span><button type="button" @click="$emit('retry')">重试</button>
        </div>
        <p v-else-if="!group.items?.length" class="workstation-search-panel__muted">暂无匹配结果</p>
        <button v-for="item in group.items" v-else :key="item.id" class="workstation-search-panel__item" type="button" @click="select(item)">
          <strong>{{ item.title }}</strong><span>{{ item.summary }}</span>
        </button>
      </section>
      <button class="workstation-search-panel__assistant" type="button" disabled :aria-label="assistant.label">
        <strong>{{ assistant.label }}</strong><span>{{ assistant.status }}</span>
      </button>
    </template>
  </section>
</template>

<script setup>
const props = defineProps({
  open: Boolean,
  groups: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
  assistant: { type: Object, default: () => ({ enabled: false, label: '问一问 AI 助手', status: '暂未开放' }) },
})
const emit = defineEmits(['navigate', 'open-document', 'retry', 'close'])

function select(item) {
  if (item.navigation?.kind === 'document') emit('open-document', item.navigation.document_id)
  else emit('navigate', item.navigation)
}
</script>

<style scoped>
.workstation-search-panel { position: absolute; z-index: 90; top: calc(100% + 8px); right: 0; display: grid; width: min(520px, calc(100vw - 32px)); max-height: min(640px, 70vh); gap: 12px; overflow: auto; border: 1px solid rgb(245 246 238 / 18%); border-radius: 16px; padding: 14px; background: #1b1d1a; box-shadow: var(--ui-shadow-overlay); color: #f5f6ee; }
.workstation-search-panel__group { display: grid; gap: 6px; }.workstation-search-panel h2 { margin: 0; color: #d7ff63; font-size: 12px; }.workstation-search-panel__item { display: grid; gap: 3px; border: 0; border-radius: 10px; padding: 10px; background: #252824; color: #f5f6ee; text-align: left; cursor: pointer; }.workstation-search-panel__item:hover { background: #343832; }.workstation-search-panel__item span, .workstation-search-panel__muted, .workstation-search-panel__assistant span { color: #aeb4a7; font-size: 12px; }.workstation-search-panel__error { display: flex; justify-content: space-between; gap: 8px; color: #ff9da5; font-size: 12px; }.workstation-search-panel__error button { border: 0; background: transparent; color: #d7ff63; cursor: pointer; }.workstation-search-panel__assistant { display: flex; align-items: center; justify-content: space-between; border: 1px solid rgb(245 246 238 / 10%); border-radius: 10px; padding: 10px; background: transparent; color: #8b9186; text-align: left; }
</style>
