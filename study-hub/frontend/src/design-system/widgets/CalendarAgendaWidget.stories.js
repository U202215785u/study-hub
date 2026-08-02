import CalendarAgendaWidget from './CalendarAgendaWidget.vue'
const days = Array.from({ length: 7 }, (_, index) => ({ date: `2026-08-0${index + 2}`, label: `${index + 2}`, selected: index === 1 }))
const agenda = [{ id: 'a', title: '项目复盘', time: '10:00 - 11:00' }, { id: 'b', title: '午间整理', time: '12:00 - 12:30', tone: 'purple' }]
export default { title: 'Study Hub Widgets/日历日程 CalendarAgendaWidget', component: CalendarAgendaWidget, tags: ['autodocs'], args: { monthLabel: '2026年 8月', days, agenda }, parameters: { docs: { description: { component: '2×2 日历与日程模块，对应 Figma 349:516。' } } } }
export const Default = {}
export const Empty = { args: { days, agenda: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '日程加载失败' } }
export const Overflow = { args: { agenda: [...agenda, { id: 'c', title: '超出卡片容量的日程', time: '14:00 - 15:00' }] } }
