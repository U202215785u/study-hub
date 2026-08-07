import WorkHeatmapWidget from '../widgets/WorkHeatmapWidget.vue'
import CalendarAgendaWidget from '../widgets/CalendarAgendaWidget.vue'
import TodayFocusWidget from '../widgets/TodayFocusWidget.vue'
import AutomationQueueWidget from '../widgets/AutomationQueueWidget.vue'
import KnowledgeWidget from '../widgets/KnowledgeWidget.vue'
import DailyMemoryWidget from '../widgets/DailyMemoryWidget.vue'
import QuickCommandWidget from '../widgets/QuickCommandWidget.vue'
import CreationWidget from '../widgets/CreationWidget.vue'
import WorkflowWidget from '../widgets/WorkflowWidget.vue'
import { normalizeDashboardLayout } from './dashboardLayout.js'

export const DASHBOARD_REGISTRY = Object.freeze({
  'work-heatmap': { id: 'work-heatmap', label: '工作热力', nodeId: '349:169', component: WorkHeatmapWidget, defaultSize: '4x2' },
  'calendar-agenda': { id: 'calendar-agenda', label: '日历日程', nodeId: '349:516', component: CalendarAgendaWidget, defaultSize: '2x2' },
  'today-focus': { id: 'today-focus', label: '今日任务', nodeId: '349:405', component: TodayFocusWidget, defaultSize: '2x3' },
  'automation-queue': { id: 'automation-queue', label: '自动化队列', nodeId: '349:369', component: AutomationQueueWidget, defaultSize: '2x2' },
  knowledge: { id: 'knowledge', label: '知识库', nodeId: '349:471', component: KnowledgeWidget, defaultSize: '2x1' },
  'daily-memory': { id: 'daily-memory', label: '今日手账', nodeId: '349:484', component: DailyMemoryWidget, defaultSize: '1x1' },
  'quick-command': { id: 'quick-command', label: '快捷指令', nodeId: '349:510', component: QuickCommandWidget, defaultSize: '1x1' },
  'creation-entry': { id: 'creation-entry', label: '创作入口', nodeId: '349:493', component: CreationWidget, defaultSize: '2x2' },
  'quick-workflow': { id: 'quick-workflow', label: '快捷工作流', nodeId: '349:459', component: WorkflowWidget, defaultSize: '2x1' },
})

export { normalizeDashboardLayout }
