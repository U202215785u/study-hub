<template>
  <DashboardModuleCard data-figma-node="349:405" title="今日任务" :loading="loading" :error="error">
    <div class="today-focus">
      <UiCompactHeader class="today-focus__header" title="今日任务" :meta="dateLabel" to="/ddl" size="md" />
      <div class="today-focus__timeline"><span/><span/><span/><span/><i/><small>06:00</small><small>12:00</small><small>18:00</small><small>24:00</small></div>
      <div class="today-focus__layers" aria-hidden="true"><i class="today-focus__layer"/><i class="today-focus__layer"/></div>
      <section class="today-focus__task">
        <header><h3>{{ currentTask?.title || '今天暂无任务' }}</h3><b><AnimatedNumber :value="completedCount" />/<AnimatedNumber :value="totalCount" /></b></header>
        <p v-if="!visibleTasks.length" class="today-focus__empty">今天暂无任务</p>
        <button v-for="task in visibleTasks" :key="task.id" type="button" :data-task-id="task.id" @click="$emit('select', task.id)"><span><strong>{{ task.title }}</strong><small>{{ task.time || '待安排' }}</small></span><i :data-status="task.status"/></button>
      </section>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed } from 'vue'
import AnimatedNumber from '../components/data-display/AnimatedNumber.vue'
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ tasks: { type: Array, default: () => [] }, totalTaskCount: { type: Number, default: null }, completedTaskCount: { type: Number, default: null }, dateLabel: { type: String, default: '' }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['select'])
const visibleTasks = computed(() => props.tasks.slice(0, 4))
const currentTask = computed(() => visibleTasks.value[0])
const completedCount = computed(() => props.completedTaskCount ?? visibleTasks.value.filter((task) => task.status === 'done').length)
const totalCount = computed(() => props.totalTaskCount ?? visibleTasks.value.length)
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
.today-focus__task { position:absolute;z-index:2;right:0;bottom:0;left:0;height:311px;box-sizing:border-box;overflow:hidden;border:1px solid rgb(245 246 238 / 12%);border-radius:28px;padding:15px 16px;background:#10140f}
.today-focus__task header{display:flex;align-items:center;justify-content:space-between}
.today-focus__task h3{overflow:hidden;margin:0;font-size:18px;text-overflow:ellipsis;white-space:nowrap}
.today-focus__task header b{flex:0 0 auto;border-radius:11px;padding:3px 13px;background:#b97822;color:#fff3d0;font-size:10px}
.today-focus__task button{display:flex;width:100%;height:52px;align-items:center;justify-content:space-between;border:0;padding:7px 0;background:none;color:#f5f6ee;text-align:left;cursor:pointer}
.today-focus__task button span{display:grid;min-width:0;gap:3px}.today-focus__task button strong{overflow:hidden;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.today-focus__task button small{color:#6f7770;font-size:9px}
.today-focus__task button i{width:18px;height:18px;flex:0 0 auto;border-radius:50%;background:#242a22}.today-focus__task button i[data-status='running']{background:#d28b20}.today-focus__task button i[data-status='done']{background:#d7ff63}
.today-focus__empty{display:grid;height:70%;place-items:center;margin:0;color:#8b9186;font-size:11px}
@media (max-width: 767px) {
  .today-focus { height: 351px; }
}
</style>
