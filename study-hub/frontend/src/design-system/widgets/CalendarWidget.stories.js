import CalendarWidget from './CalendarWidget.vue'

const days = Array.from({ length: 28 }, (_, index) => ({ date: `2026-06-${String(index + 1).padStart(2, '0')}`, label: String(index + 1), selected: index === 6, eventTones: index % 5 === 0 ? ['lime', 'purple'] : [] }))
const longTitle = '这是一个用于验证月份标题在极端内容长度下仍然保持稳定布局并且不会挤压日历网格内容区域的六十字中文标题示例'

export default { title: 'Study Hub Widgets/CalendarWidget 学习日历', component: CalendarWidget, tags: ['autodocs'], parameters: { docs: { description: { component: '学习日历组件，对应 Figma 349:516。日期选择只抛出 ISO 日期字符串。' } } }, args: { days, monthLabel: '2026 年 6 月' } }
export const Default = {}
export const Empty = { args: { days: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '日历暂时无法加载' } }
export const LongContent = { args: { monthLabel: longTitle } }
export const Mobile = { parameters: { viewport: { defaultViewport: 'mobile' } } }
