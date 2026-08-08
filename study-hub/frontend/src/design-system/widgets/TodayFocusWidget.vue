<template>
  <DashboardModuleCard data-figma-node="349:405" title="今日任务" :loading="loading" :error="error">
    <div class="today-focus">
      <UiCompactHeader class="today-focus__header" title="今日任务" :meta="dateLabel" to="/ddl" size="md" />
      <div class="today-focus__timeline"><span/><span/><span/><span/><i/><small>06:00</small><small>12:00</small><small>18:00</small><small>24:00</small></div>
      <div class="today-focus__layers" aria-hidden="true"><i class="today-focus__layer"/><i class="today-focus__layer"/></div>
      <div class="today-focus__stack" data-testid="today-card-stack" tabindex="0" role="group" aria-label="今日任务分类" @pointerdown="startDrag" @pointermove="moveDrag" @pointerup="finishDrag" @pointercancel="cancelDrag" @keydown.left.prevent="rotate(-1)" @keydown.right.prevent="rotate(1)">
        <section v-for="(category, index) in stackedCategories" :key="category.id" class="today-focus__task" :class="`today-focus__task--${index}`" :data-category-id="category.id" :style="index === 0 ? { '--drag-x': `${dragOffset}px` } : undefined" @click="index && rotate(index)">
          <header><h3 data-testid="today-card-title">{{ category.name }}</h3><b><AnimatedNumber :value="completedFor(category)" />/<AnimatedNumber :value="category.tasks.length" /></b></header>
          <p v-if="!category.tasks.length" class="today-focus__empty">今天暂无任务</p>
          <button v-for="task in category.tasks.slice(0, 4)" :key="task.id" type="button" :data-task-id="task.id" @click.stop="$emit('select', task.id)"><span><strong>{{ task.title }}</strong><small>{{ task.time || '待安排' }}</small></span><i :data-status="task.status"/></button>
          <button v-if="index === 0" type="button" class="today-focus__create" @click.stop="$emit('create', category.id)">建立任务</button>
        </section>
      </div>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed, ref } from 'vue'
import AnimatedNumber from '../components/data-display/AnimatedNumber.vue'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ tasks: { type: Array, default: () => [] }, categories: { type: Array, default: () => [] }, totalTaskCount: { type: Number, default: null }, completedTaskCount: { type: Number, default: null }, dateLabel: { type: String, default: '' }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['select', 'create'])
const activeIndex = ref(0)
const dragStartX = ref(null)
const dragOffset = ref(0)
const categoryList = computed(() => props.categories.length ? props.categories.slice(0, 3).map((category) => ({ ...category, tasks: Array.isArray(category.tasks) ? category.tasks : [] })) : [{ id: 'all', name: '今日任务', tasks: props.tasks }])
const stackedCategories = computed(() => categoryList.value.map((_, index) => categoryList.value[(activeIndex.value + index) % categoryList.value.length]))
const visibleTasks = computed(() => props.tasks.slice(0, 4))
const currentTask = computed(() => visibleTasks.value[0])
const completedCount = computed(() => props.completedTaskCount ?? visibleTasks.value.filter((task) => task.status === 'done').length)
const totalCount = computed(() => props.totalTaskCount ?? visibleTasks.value.length)
function completedFor(category) { return category.tasks.filter((task) => task.status === 'done').length }
function rotate(offset) { const count = categoryList.value.length; if (count) activeIndex.value = (activeIndex.value + offset + count) % count }
function startDrag(event) { dragStartX.value = event.clientX; event.currentTarget.setPointerCapture?.(event.pointerId) }
function moveDrag(event) { if (dragStartX.value !== null) dragOffset.value = event.clientX - dragStartX.value }
function finishDrag(event) { if (dragStartX.value === null) return; const distance = event.clientX - dragStartX.value; if (distance <= -80) rotate(1); if (distance >= 80) rotate(-1); cancelDrag() }
function cancelDrag() { dragStartX.value = null; dragOffset.value = 0 }
</script>

<style scoped>
.today-focus { position: relative; height: 100%; box-sizing: border-box; }
.today-focus__header { position: relative; z-index: 3; }
.today-focus__timeline { position: relative; z-index: 3; display: grid; height: 47px; grid-template-columns: 1.4fr 1.2fr .8fr .8fr; gap: 2px; margin-top: 12px; padding-top: 15px; }
.today-focus__timeline > span { height: 4px; border-radius: 2px; background: #ea4e00; }
.today-focus__timeline > span:nth-child(2){background:#ffb183}.today-focus__timeline > span:nth-child(3){background:#d7ff63}.today-focus__timeline > span:nth-child(4){background:#f4e6c5}
.today-focus__timeline small { color:#8b9186;font-size:9px}
.today-focus__timeline i{position:absolute;left:59%;top:calc(50% - 2px);width:7px;height:7px;transform:rotate(45deg);background:#d7ff63}
.today-focus__layers { position: absolute; z-index: 1; inset: 0; }
.today-focus__layer { position:absolute;height:215px;border:1px solid rgb(245 246 238 / 8%);border-radius:28px; }
.today-focus__layer:first-child { top:108px;right:44px;left:44px;background:#494a49; }
.today-focus__layer:last-child { top:120px;right:22px;left:22px;background:#383838; }
.today-focus__stack{position:absolute;z-index:2;right:0;bottom:0;left:0;height:311px;outline:0}.today-focus__stack:focus-visible{outline:2px solid #d7ff63;outline-offset:3px;border-radius:28px}
.today-focus__task { position:absolute;z-index:3;right:0;bottom:0;left:0;height:311px;box-sizing:border-box;overflow:hidden;border:1px solid rgb(245 246 238 / 12%);border-radius:28px;padding:15px 16px;background:#10140f;transform:translateX(var(--drag-x, 0px));transition:transform .2s ease}.today-focus__task--1{z-index:2;transform:translate(-12px,-12px) scale(.94);background:#383838;cursor:pointer}.today-focus__task--2{z-index:1;transform:translate(8px,-24px) scale(.88);background:#494a49;cursor:pointer}
.today-focus__task header{display:flex;align-items:center;justify-content:space-between}
.today-focus__task h3{overflow:hidden;margin:0;font-size:18px;text-overflow:ellipsis;white-space:nowrap}
.today-focus__task header b{flex:0 0 auto;border-radius:11px;padding:3px 13px;background:#b97822;color:#fff3d0;font-size:10px}
.today-focus__task button{display:flex;width:100%;height:52px;align-items:center;justify-content:space-between;border:0;padding:7px 0;background:none;color:#f5f6ee;text-align:left;cursor:pointer}
.today-focus__task button span{display:grid;min-width:0;gap:3px}.today-focus__task button strong{overflow:hidden;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.today-focus__task button small{color:#6f7770;font-size:9px}
.today-focus__task button i{width:18px;height:18px;flex:0 0 auto;border-radius:50%;background:#242a22}.today-focus__task button i[data-status='running']{background:#d28b20}.today-focus__task button i[data-status='done']{background:#d7ff63}
.today-focus__empty{display:grid;height:70%;place-items:center;margin:0;color:#8b9186;font-size:11px}
.today-focus__create{position:absolute;right:16px;bottom:16px;left:16px;justify-content:center!important;border-radius:10px!important;background:#d7ff63!important;color:#10140f!important;font-weight:800}
@media (max-width: 767px) {
  .today-focus { height: 351px; }
}
</style>
