<template>
  <DashboardModuleCard data-figma-node="349:405" title="今日任务" :loading="loading" :error="error" :empty="!tasks.length && !loading && !error" empty-text="今天还没有任务">
    <div class="today-focus">
      <header><h2>今日任务</h2><span>{{ dateLabel }}</span></header>
      <div class="today-focus__timeline"><span/><span/><span/><span/><i/><small>06:00</small><small>12:00</small><small>18:00</small><small>24:00</small></div>
      <div class="today-focus__layers" aria-hidden="true"><i/><i/></div>
      <section class="today-focus__task">
        <header><h3>{{ currentTask?.title || 'Onboarding Task' }}</h3><b>{{ completedCount }}/{{ visibleTasks.length || 0 }}</b></header>
        <button v-for="task in visibleTasks" :key="task.id" type="button" :data-task-id="task.id" @click="$emit('select', task.id)"><span><strong>{{ task.title }}</strong><small>{{ task.time || '待安排' }}</small></span><i :data-status="task.status"/></button>
      </section>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed } from 'vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ tasks: { type: Array, default: () => [] }, dateLabel: { type: String, default: '' }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['select'])
const visibleTasks = computed(() => props.tasks.slice(0, 5))
const currentTask = computed(() => visibleTasks.value[0])
const completedCount = computed(() => visibleTasks.value.filter((task) => task.status === 'done').length)
</script>

<style scoped>
.today-focus { height: 100%; box-sizing: border-box; padding: 19px 18px; } .today-focus > header { display: flex; align-items: center; justify-content: space-between; } h2 { margin: 0; font-size: 18px; } .today-focus > header span { color: #8b9186; font-size: 11px; }
.today-focus__timeline { position: relative; display: grid; grid-template-columns: 1.4fr 1.2fr .8fr .8fr; gap: 2px; height: 49px; margin-top: 15px; padding-top: 18px; } .today-focus__timeline > span { height: 4px; border-radius: 2px; background: #ea4e00; } .today-focus__timeline > span:nth-child(2){background:#ffb183}.today-focus__timeline > span:nth-child(3){background:#d7ff63}.today-focus__timeline > span:nth-child(4){background:#f4e6c5}.today-focus__timeline small { color:#8b9186;font-size:9px}.today-focus__timeline i{position:absolute;left:59%;top:16px;width:7px;height:7px;transform:rotate(45deg);background:#d7ff63}
.today-focus__layers { position: absolute; top: 124px; left: 38px; right: 38px; height: 40px; } .today-focus__layers i { position:absolute;inset:0 20px;border-radius:28px;background:#494a49}.today-focus__layers i+ i{inset:12px 8px -12px;background:#383838}
.today-focus__task { position:absolute;left:19px;right:19px;bottom:20px;height:311px;box-sizing:border-box;border:1px solid rgb(245 246 238 / 12%);border-radius:28px;padding:15px;background:#10140f}.today-focus__task header{display:flex;align-items:center;justify-content:space-between}.today-focus__task h3{margin:0;font-size:18px}.today-focus__task header b{border-radius:11px;padding:3px 13px;background:#b97822;color:#fff3d0;font-size:10px}.today-focus__task button{display:flex;width:100%;align-items:center;justify-content:space-between;border:0;padding:11px 0;background:none;color:#f5f6ee;text-align:left;cursor:pointer}.today-focus__task button span{display:grid;gap:3px}.today-focus__task button strong{font-size:12px}.today-focus__task button small{color:#6f7770;font-size:9px}.today-focus__task button i{width:18px;height:18px;border-radius:50%;background:#242a22}.today-focus__task button i[data-status='running']{background:#d28b20}.today-focus__task button i[data-status='done']{background:#d7ff63}
</style>
