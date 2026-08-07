# Study UI

Study UI 是 Study Hub 的内部 Vue 3 设计系统。它把 Figma 首页的视觉语言整理为稳定组件、交互约定、自适应布局和可复用的仪表盘模块。我们参考 Ant Design 的组件产品化与文档深度，但保留 Study Hub 自己的视觉语言，不复制 Ant Design 的外观。

## 设计语言

Study UI 是安静、紧凑的工作界面。中性色负责画布和表面层级，青柠色只用于主要操作和进行中状态；紫色与橙色区分内容类型，成功、警告、危险和信息色保持独立语义。

运行时的唯一视觉来源是 `src/design-system/foundations/tokens.css`。组件只使用语义化 `--ui-*` 变量，不在组件内部另建一套颜色、间距或圆角。

## Storybook 分类

| 分类 | 用途 | 当前内容 |
| --- | --- | --- |
| 设计语言 | 颜色、状态、字体密度、间距、圆角、阴影和动效 | `DesignLanguage` 五个文档视图 |
| 通用 | 通用命令和胶囊操作 | `UiButton`、`UiIconButton`、`UiPillButton` |
| 导航 | 主导航、搜索入口和实时问候 | `CapsuleNavigation`、`GreetingBar` |
| 数据录入 | 带标签的原生表单控制 | `UiInput`、`UiSelect` |
| 数据展示 | 标签、状态、进度、紧凑标题和内嵌表面 | `UiTag`、`UiBadge`、`UiProgress`、`UiCompactHeader`、`UiInsetSurface` |
| 反馈 | 加载、空状态和错误状态 | `UiSpinner`、`UiEmpty` |
| 布局 | 应用外壳、固定八列网格、模块容器和编辑布局 | `WorkbenchFrame`、`BentoDashboardGrid`、`DashboardModuleCard`、`DashboardEditor` 等 |
| 仪表盘组件 | 首页九张可复用业务卡片 | 工作热力、日历日程、今日任务、自动化队列、知识库、手账、快捷指令、创作入口、快捷工作流 |
| 完整范例 | 公共组件与静态数据组成的整页验收视图 | `HomeDashboardExample` |

## 原子层级

```text
Foundations -> Atoms -> Molecules -> Organisms -> Widgets -> Pages
```

- Foundations：颜色、字体、间距、圆角、阴影、动效等视觉决定。
- Atoms：按钮、标签、状态、输入框等最小交互单元。
- Molecules：胶囊按钮、紧凑标题、内嵌表面等小型组合。
- Organisms：导航、网格、模块卡片等页面级结构。
- Widgets：接收可序列化数据并抛出标识的九张首页业务卡片。
- Pages：负责接口、状态、路由、弹窗和业务流程。

依赖只能从右向左。底层组件不能导入业务卡片，也不能读取页面状态。Storybook 按“使用功能”分类；每个组件文档再注明其原子层级，两种分类同时保留。

## 使用与验证

应用只从稳定入口导入公共组件：

```js
import { UiButton, UiCompactHeader, KnowledgeWidget } from '@study-ui'
```

在 `frontend` 目录运行组件目录和验证：

```powershell
npm run storybook
npm run verify:study-ui
node tests/home-responsive.mjs
```

每个公共组件都有独立 Storybook 页面，只呈现适用的默认、加载、禁用、错误、空数据、长文本或超量状态。仪表盘组件还保留对应的 Figma 节点说明。完整首页范例只用于组合验收，不访问接口、路由、存储或真实页面状态。

## 2026-08-03 验证基线

- 正式首页保持 `1440×980` 基准舞台、固定 `8×4` 网格、九张卡片和 `16px` 卡片内容边距。
- PC 与 16:9 浏览优先；超宽屏保持设计比例并居中留白。
- 九张正式首页 Widget 已真实复用公共组件；页面仍负责 API、路由、存储、弹窗和业务副作用。
- `npm run test:unit`：43 个测试文件、92 项测试全部通过。
- `npm run build:storybook` 与 `npm run build`：均通过。
- 首页卡片合同、响应式、Figma 几何叠合和布局持久化四组回归：全部通过。
- Storybook 设计语言总览与完整首页范例已目视检查；完整范例为 0 项无障碍违规、0 条浏览器控制台错误。

本基线只覆盖正式首页及其九张模块卡片，不代表其他页面的 Toast、Modal/Drawer、表单和历史按钮已经迁移完成。

## 文档约定

每个公共组件必须说明：

1. 组件定义与适用场景。
2. Props、事件和插槽。
3. 适用的默认、加载、禁用、错误、空数据、长内容和容量溢出状态。
4. 键盘、焦点和可访问名称行为。
5. 组件使用的语义 Token。
6. 已有设计稿时标记准确 Figma 节点，否则明确标记为未映射。

当前覆盖情况见 [component-status.md](./component-status.md)，维护规则见 [contributing.md](./contributing.md)。
