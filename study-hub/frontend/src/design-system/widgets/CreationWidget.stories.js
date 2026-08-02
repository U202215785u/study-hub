import CreationWidget from './CreationWidget.vue'

const items = [
  { id: 'c1', title: '文章模板', thumbnail: '', kind: 'article' },
  { id: 'c2', title: '学习视频脚本', thumbnail: '', kind: 'video' },
  { id: 'c3', title: '读书笔记', thumbnail: '', kind: 'note' },
  { id: 'c4', title: '课程介绍页', thumbnail: '', kind: 'template' },
]
const longTitle = '这是一个用于验证创作卡片标题在极端内容长度下仍然稳定截断并且不会改变缩略图比例和网格尺寸的六十字中文标题示例'

export default { title: 'Study Hub Widgets/创作入口 CreationWidget', component: CreationWidget, tags: ['autodocs'], parameters: { docs: { description: { component: '首页继续创作组件，对应 Figma 349:493。打开作品只抛出作品 id。' } } }, args: { items } }
export const Default = {}
export const Empty = { args: { items: [] } }
export const Loading = { args: { loading: true } }
export const Error = { args: { error: '创作内容暂时无法加载' } }
export const LongContent = { args: { items: [{ ...items[0], title: longTitle }] } }
export const Mobile = { parameters: { viewport: { defaultViewport: 'mobile' } } }
