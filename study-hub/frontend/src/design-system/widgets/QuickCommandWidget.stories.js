import QuickCommandWidget from './QuickCommandWidget.vue'
export default { title: 'Study Hub Widgets/快捷指令 QuickCommandWidget', component: QuickCommandWidget, tags: ['autodocs'], args: { commands: [{ id: 'a', title: '更新日志' }, { id: 'b', title: '编译Wiki' }] }, parameters: { docs: { description: { component: '1×1 快捷指令模块，对应 Figma 349:510；最多显示两项。' } } } }
export const Default = {}
export const Empty = { args: { commands: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '指令加载失败' } }
