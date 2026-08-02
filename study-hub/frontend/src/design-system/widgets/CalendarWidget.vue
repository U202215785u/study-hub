<template>
  <UiWidgetFrame data-figma-node="349:516" title="学习日历" :meta="monthLabel" :loading="loading" :error="error" :empty="!days.length && !loading && !error" empty-title="暂无日历数据">
    <div class="calendar" role="grid" aria-label="学习日历">
      <span v-for="weekday in weekdays" :key="weekday" class="calendar__weekday" role="columnheader">{{ weekday }}</span>
      <button v-for="day in days" :key="day.date" class="calendar__day" :class="{ 'calendar__day--selected': day.selected }" :data-date="day.date" type="button" :aria-label="day.date" :aria-pressed="day.selected ? 'true' : 'false'" @click="selectDay(day.date)">
        <span>{{ day.label }}</span>
        <span v-if="day.eventTones?.length" class="calendar__events" aria-hidden="true"><i v-for="tone in day.eventTones" :key="tone" :data-tone="tone" /></span>
      </button>
    </div>
  </UiWidgetFrame>
</template>

<script setup>
import UiWidgetFrame from '../patterns/UiWidgetFrame.vue'
const props = defineProps({ days: { type: Array, default: () => [] }, monthLabel: { type: String, default: '本月' }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['select'])
const weekdays = ['一', '二', '三', '四', '五', '六', '日']
const selectDay = (date) => emit('select', date)
</script>

<style scoped>
.calendar { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: var(--ui-space-1); }
.calendar__weekday { padding-bottom: var(--ui-space-2); color: var(--ui-color-text-muted); font-size: 10px; text-align: center; }
.calendar__day { display: grid; min-width: 0; min-height: 44px; place-items: center; align-content: center; gap: 3px; border: 1px solid transparent; border-radius: var(--ui-radius-sm); background: transparent; color: var(--ui-color-text); font: 600 12px/1 var(--ui-font-sans); cursor: pointer; }
.calendar__day:hover, .calendar__day:focus-visible { outline: none; border-color: var(--ui-color-border-strong); background: var(--ui-color-surface-raised); }
.calendar__day--selected { background: var(--ui-color-action); color: var(--ui-color-action-text); }
.calendar__events { display: inline-flex; gap: 2px; }
.calendar__events i { width: 4px; height: 4px; border-radius: 50%; background: var(--ui-color-text-muted); }
.calendar__events i[data-tone='lime'] { background: var(--ui-color-action); }
.calendar__events i[data-tone='purple'] { background: var(--ui-color-content-purple); }
.calendar__events i[data-tone='orange'] { background: var(--ui-color-content-orange); }
.calendar__day--selected .calendar__events i { background: var(--ui-color-action-text); }
</style>
