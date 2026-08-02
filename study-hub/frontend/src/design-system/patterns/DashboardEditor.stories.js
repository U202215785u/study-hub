import { DEFAULT_DASHBOARD_LAYOUT } from '../layout/dashboardLayout.js'
import DashboardEditor from './DashboardEditor.vue'
export default { title: '布局/DashboardEditor 首页编辑器', component: DashboardEditor, tags: ['autodocs'], parameters: { layout: 'fullscreen', docs: { description: { component: '管理模块显示、隐藏和拖动顺序；保存、取消和恢复默认具有独立事件。' } } } }
export const Default = { args: { widgets: DEFAULT_DASHBOARD_LAYOUT.widgets } }
