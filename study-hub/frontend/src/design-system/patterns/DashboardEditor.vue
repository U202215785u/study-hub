<template>
  <aside class="dashboard-editor" role="dialog" aria-modal="true" aria-labelledby="dashboard-editor-title">
    <header><div><p>首页模块</p><h2 id="dashboard-editor-title">编辑首页</h2></div><UiIconButton label="取消编辑" variant="text" @click="$emit('cancel')">×</UiIconButton></header>
    <p class="dashboard-editor__hint">拖动调整顺序，隐藏的模块可以随时重新添加。</p>
    <Draggable :model-value="orderedWidgets" item-key="id" handle=".dashboard-editor__handle" @end="onDragEnd">
      <template #item="{ element }">
        <div class="dashboard-editor__row" :data-editor-module-id="element.id">
          <button class="dashboard-editor__handle" type="button" :aria-label="`拖动${labelFor(element.id)}`" title="拖动排序">⋮⋮</button>
          <span><strong>{{ labelFor(element.id) }}</strong><small>{{ element.size }}</small></span>
          <UiButton v-if="element.visible" :data-hide-id="element.id" size="sm" variant="text" @click="$emit('hide', element.id)">隐藏</UiButton>
          <UiButton v-else :data-show-id="element.id" size="sm" @click="$emit('show', element.id)">添加</UiButton>
        </div>
      </template>
    </Draggable>
    <footer><UiButton data-editor-restore variant="text" @click="$emit('restore')">恢复默认</UiButton><span/><UiButton data-editor-cancel variant="secondary" @click="$emit('cancel')">取消</UiButton><UiButton data-editor-save @click="$emit('save')">保存布局</UiButton></footer>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import Draggable from 'vuedraggable'
import { DASHBOARD_REGISTRY } from '../layout/dashboardRegistry.js'
import UiButton from '../components/general/UiButton.vue'
import UiIconButton from '../components/general/UiIconButton.vue'
const props = defineProps({ widgets: { type: Array, default: () => [] } })
const emit = defineEmits(['hide', 'show', 'reorder', 'save', 'cancel', 'restore'])
const orderedWidgets = computed(() => [...props.widgets].sort((a, b) => a.order - b.order))
const labelFor = (id) => DASHBOARD_REGISTRY[id]?.label || id
function onDragEnd(event) { if (event.oldIndex !== event.newIndex) emit('reorder', orderedWidgets.value[event.oldIndex]?.id, event.newIndex) }
</script>

<style scoped>
.dashboard-editor{position:fixed;z-index:90;top:24px;right:24px;bottom:24px;display:grid;width:370px;box-sizing:border-box;grid-template-rows:auto auto 1fr auto;gap:16px;overflow:hidden;border:1px solid rgb(245 246 238 / 20%);border-radius:18px;padding:20px;background:#1b1d1a;box-shadow:0 28px 80px rgb(0 0 0 / 55%);color:#f5f6ee}.dashboard-editor header{display:flex;align-items:center;justify-content:space-between}.dashboard-editor header p{margin:0 0 5px;color:#d7ff63;font-size:10px;font-weight:800}.dashboard-editor h2{margin:0;font-size:20px}.dashboard-editor__hint{margin:0;color:#8b9186;font-size:12px}.dashboard-editor :deep(.sortable-chosen){background:#252824}.dashboard-editor__row{display:grid;grid-template-columns:32px 1fr auto;align-items:center;gap:9px;border-bottom:1px solid rgb(245 246 238 / 10%);padding:9px 0}.dashboard-editor__handle{border:0;background:none;color:#8b9186;cursor:grab}.dashboard-editor__row>span{display:grid;gap:3px}.dashboard-editor__row strong{font-size:12px}.dashboard-editor__row small{color:#6f7770;font-size:10px}.dashboard-editor footer{display:flex;align-items:center;gap:8px}.dashboard-editor footer>span{flex:1}</style>
