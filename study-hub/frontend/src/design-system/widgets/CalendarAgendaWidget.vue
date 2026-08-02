<template>
  <DashboardModuleCard data-figma-node="349:516" title="日历日程" :loading="loading" :error="error" :empty="!days.length && !loading && !error">
    <div class="calendar-agenda">
      <header><h2>{{ monthLabel }}</h2><span>今天</span></header>
      <div class="calendar-agenda__week" role="grid">
        <b v-for="weekday in weekdays" :key="weekday">{{ weekday }}</b>
        <button v-for="day in days.slice(0, 7)" :key="day.date" type="button" :data-date="day.date" :class="{ selected: day.selected }" @click="$emit('select', day.date)">{{ day.label }}</button>
      </div>
      <div class="calendar-agenda__panel">
        <button v-for="(item, index) in visibleAgenda" :key="item.id ?? index" type="button" @click="$emit('open', item.id)"><i :data-tone="item.tone || (index ? 'purple' : 'lime')"/><span><strong>{{ item.title }}</strong><small>{{ item.time }}</small></span><b>›</b></button>
        <p v-if="!visibleAgenda.length">今天暂无日程</p>
      </div>
    </div>
  </DashboardModuleCard>
</template>

<script setup>
import { computed } from 'vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ days: { type: Array, default: () => [] }, agenda: { type: Array, default: () => [] }, monthLabel: { type: String, default: '本月' }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['select', 'open'])
const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const visibleAgenda = computed(() => props.agenda.slice(0, 2))
</script>

<style scoped>
.calendar-agenda { height: 100%; box-sizing: border-box; padding: 20px 15px 18px; }
header { display: flex; align-items: center; justify-content: space-between; padding: 0 7px; } h2 { margin: 0; font-size: 20px; } header > span { display: inline-flex; height: 26px; align-items: center; border-radius: 14px; padding: 0 24px; background: #d7ff63; color: #11140f; font-size: 12px; font-weight: 800; }
.calendar-agenda__week { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-top: 17px; text-align: center; } .calendar-agenda__week b { color: #d9ddcf; font-size: 12px; } .calendar-agenda__week button { height: 38px; border: 0; border-radius: 50%; background: none; color: #f5f6ee; cursor: pointer; font-size: 16px; } .calendar-agenda__week button.selected { background: #f5f6ee; color: #11140f; font-weight: 800; }
.calendar-agenda__panel { display: grid; height: 145px; box-sizing: border-box; margin-top: 12px; overflow: hidden; border-radius: 20px; padding: 11px 18px; background: #595959; } .calendar-agenda__panel button { display: grid; grid-template-columns: 4px 1fr auto; align-items: center; gap: 12px; border: 0; border-bottom: 1px solid #e3e5df; padding: 8px 0; background: none; color: white; text-align: left; cursor: pointer; } .calendar-agenda__panel button:last-of-type { border-bottom: 0; } .calendar-agenda__panel i { width: 4px; height: 34px; border-radius: 2px; background: #d7ff63; } .calendar-agenda__panel i[data-tone='purple'] { background: #8b73ff; } .calendar-agenda__panel span { display: grid; gap: 4px; } .calendar-agenda__panel strong { font-size: 14px; } .calendar-agenda__panel small, .calendar-agenda__panel p { color: #b8bcb5; font-size: 11px; }
</style>
