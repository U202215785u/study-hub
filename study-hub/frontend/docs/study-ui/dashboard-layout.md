# 首页可编排网格（STUDYHUB-7）

首页桌面端采用 8 列显式网格。模块尺寸由 `SIZE_RULES` 唯一派生；本地布局只持久化 `{ id, visible, x, y, order }`，不持久化尺寸。

`order` 是阅读顺序：按 `(y, x, previousOrder)` 排序。存储键保持 `study-hub:dashboard-layout:v1`，旧版 `version: 1` 的列表布局会在读取时原地迁移至 `version: 2` 的坐标布局。

拖拽模块优先占用目标格。与其重叠的模块先保持原列并向下寻找首个可用位置；若原列没有可用位置，则按行优先扫描 8 列网格。网格允许增加新行。隐藏模块重新加入时同样采用首个行优先合法位置。

编辑模式使用 Pointer Events 的手柄拖拽，窗口级事件保证指针离开手柄后仍能完成操作。编辑器的空白区域不拦截画布指针事件，避免遮挡右侧模块。保存、取消、恢复默认与撤销全部针对草稿布局。

小于 768px 时，固定设计舞台改为原生单列页面：卡片自然高度、页面纵向滚动、禁止横向溢出。响应式验证覆盖 390px、942px 和桌面视口。

## 验证

```powershell
npm run test:unit
npm run build
node tests/home-layout-persistence.mjs
node tests/home-responsive.mjs
node tests/home-visual-overlay.mjs
```
