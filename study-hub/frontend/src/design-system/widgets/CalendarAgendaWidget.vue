<template>
  <DashboardModuleCard data-figma-node="349:516" title="日历日程" :loading="loading" :error="error" :empty="!days.length && !loading && !error">
    <div class="calendar-agenda">
      <UiCompactHeader class="calendar-agenda__header" title="日历日程" :meta="monthLabel" to="/ddl" size="md">
        <template #action><UiButton class="calendar-agenda__today" size="xs" shape="pill" @click="$emit('today')">今天</UiButton></template>
      </UiCompactHeader>
      <div class="calendar-agenda__week" role="group" aria-label="一周日期">
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
import UiCompactHeader from '../components/data-display/UiCompactHeader.vue'
import UiButton from '../components/general/UiButton.vue'
import DashboardModuleCard from '../patterns/DashboardModuleCard.vue'
const props = defineProps({ days: { type: Array, default: () => [] }, agenda: { type: Array, default: () => [] }, monthLabel: { type: String, default: '本月' }, loading: Boolean, error: { type: String, default: '' } })
defineEmits(['select', 'open', 'today'])
const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const visibleAgenda = computed(() => props.agenda.slice(0, 2))
</script>

<style scoped>
.calendar-agenda { display: grid; width: 100%; min-width: 0; height: 100%; min-height: 0; box-sizing: border-box; grid-template-rows: auto auto minmax(0, 1fr); }
.calendar-agenda__today { flex: 0 0 auto; }
.calendar-agenda__week { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-top: 17px; text-align: center; } .calendar-agenda__week b { color: #d9ddcf; font-size: 12px; } .calendar-agenda__week button { height: 38px; border: 0; border-radius: 50%; background: none; color: #f5f6ee; cursor: pointer; font-size: 16px; transition: background-color var(--ui-duration-fast) var(--ui-ease-standard), transform var(--ui-duration-fast) var(--ui-ease-standard); } .calendar-agenda__week button.selected { background: #f5f6ee; color: #11140f; font-weight: 800; transform: scale(1.06); }
.calendar-agenda__panel { display: grid; min-height: 0; box-sizing: border-box; margin-top: 12px; overflow: hidden; border-radius: 20px; padding: 11px 18px; background: #595959; } .calendar-agenda__panel button { display: grid; min-height: 0; grid-template-columns: 4px 1fr auto; align-items: center; gap: 12px; border: 0; border-bottom: 1px solid #e3e5df; padding: 8px 0; background: none; color: white; text-align: left; cursor: pointer; } .calendar-agenda__panel button:last-of-type { border-bottom: 0; } .calendar-agenda__panel i { width: 4px; height: 34px; border-radius: 2px; background: #d7ff63; } .calendar-agenda__panel i[data-tone='purple'] { background: #8b73ff; } .calendar-agenda__panel span { display: grid; min-width: 0; gap: 4px; } .calendar-agenda__panel strong, .calendar-agenda__panel small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } .calendar-agenda__panel strong { font-size: 14px; } .calendar-agenda__panel small, .calendar-agenda__panel p { color: #b8bcb5; font-size: 11px; }
@media (hover: hover) and (pointer: fine) { .calendar-agenda__week button:hover { transform: scale(1.04); } }
</style>
