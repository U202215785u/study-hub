# Study UI Design System 设计规格

**状态：** 已确认方向，待实施

**目标：** 从 Figma 的“改3——首页仪表盘 / 校对自适应版”提炼一套可复用、可测试、可文档化的 Vue 组件系统，并以首页作为第一轮迁移试点。

**设计来源：** Figma 文件 `Study Hub Design System Draft`，首页节点 `349:96`。

## 1. 背景与问题

当前 Study Hub 前端使用 Vue 3、Vite 5 和 Tailwind CSS 3。首页 `frontend/src/views/Home.vue` 同时承担业务请求、状态管理、页面布局和视觉实现，存在大量重复的按钮、卡片、输入框、标签和状态样式。`tailwind.config.js` 中的旧主题仍以蓝紫色为主，与 Figma 首页确定的深色工作台和黄绿色主行动信号不一致。

本次不直接复制 Figma 导出的绝对定位代码，也不把 Ant Design Vue 作为页面视觉来源。借鉴 Ant Design 的是组件产品化方法：稳定分类、明确用途、完整状态、公开 API、语义结构、组件令牌、可访问性、示例和变更记录。

## 2. 成功标准

第一阶段完成后，应满足以下条件：

1. 设计令牌只有一个代码来源，Tailwind、组件样式和 Storybook 共同消费该来源。
2. 首页不再直接重复基础按钮、输入框、标签、卡片和进度条的视觉规则。
3. 基础组件具备默认、悬停、按下、键盘聚焦、禁用、加载及错误等适用状态。
4. 组件文档按“何时使用、示例、API、语义结构、可访问性、组件令牌、设计指引”组织。
5. Storybook 可以独立浏览组件，并通过可访问性检查与交互测试验证关键状态。
6. 首页在 1440px、1024px、768px 和 390px 宽度下采用重排、折叠或隐藏策略，无横向溢出和文字遮挡。
7. 组件命名和 Figma 节点能够一一映射，为后续 Code Connect 留出稳定接口。

## 3. 设计原则

### 3.1 安静的工作底板

画布和表面使用低亮度中性色建立层级。装饰不能与任务、日程和进度争夺注意力。

### 3.2 鲜明的行动信号

荧光黄绿色只用于主要行动、当前选择、键盘焦点和关键进度。一个操作区域只出现一个主要行动。

### 3.3 模块即工作单元

每个 Widget 由标题区、内容区、状态区和可选操作区组成。Widget 的尺寸可以变化，但结构和状态契约保持一致。

### 3.4 状态始终可见

异步操作必须呈现空闲、排队、进行、成功、失败和空状态。颜色不是唯一信号，状态还需文字、图标或进度表达。

### 3.5 自适应是重新编排

小屏不等比缩放桌面画面。导航、Dock 和 Widget 网格在断点处重排；次要信息可以折叠，关键操作保持可达。

### 3.6 业务色与状态色分离

紫色、橙色和奶油色用于日程或任务分段等内容分类；成功、警告、危险和信息状态使用独立语义令牌。

## 4. 信息架构

### 4.1 面向使用者的功能分类

- **设计：** 原则、颜色语义、排版、间距、圆角、阴影、动效、响应式、可访问性。
- **通用：** Button、IconButton、Typography、Icon。
- **布局：** AppShell、DashboardGrid、Stack、Inline、Divider。
- **导航：** TopNavigation、Sidebar、SidebarItem、RightDock、Tabs。
- **数据录入：** Input、SearchInput、Select、Textarea、Checkbox、Toggle。
- **数据展示：** Surface、Card、WidgetFrame、Badge、Tag、Progress、Calendar、Timeline、Heatmap、Empty。
- **反馈：** Toast、Alert、Modal、Drawer、Skeleton、Spinner。
- **Study Hub：** TaskWidget、CalendarWidget、AutomationQueueWidget、KnowledgeWidget、CreationWidget、WorkflowWidget。

### 4.2 内部原子依赖层

```text
Foundations -> Primitives -> Composites -> Patterns -> Widgets -> Pages
```

- `Foundations`：令牌和全局视觉规则。
- `Primitives`：Button、Input、Tag、Progress 等不可再拆的公共组件。
- `Composites`：SearchInput、PanelHeader、ProgressRow 等组合组件。
- `Patterns`：AppShell、DashboardGrid、WidgetFrame 等稳定布局模式。
- `Widgets`：与 Study Hub 领域数据和操作相关的模块。
- `Pages`：只负责取数、编排 Widget 和路由级状态。

原子层级只表达依赖关系，不作为用户寻找组件的唯一导航。

## 5. 设计令牌

令牌分为三层，禁止组件直接依赖原始十六进制颜色：

1. **基础值：** `color.neutral.950`、`space.4`、`radius.lg`。
2. **语义值：** `color.canvas`、`color.surface.default`、`color.text.strong`、`color.action.primary`。
3. **组件值：** `button.primary.bg`、`widget.border`、`input.focus.ring`。

首版视觉基线来自目标 Figma 节点：

| 语义 | 基线值 | 用途 |
| --- | --- | --- |
| `color.canvas` | `#10140F` | 应用画布 |
| `color.surface.default` | `#1B1D1A` | 默认卡片和控件表面 |
| `color.text.strong` | `#F5F6EE` | 标题和主要数值 |
| `color.text.default` | `#D9DDCF` | 正文和常规标签 |
| `color.text.muted` | `#8B9186` | 辅助信息和时间 |
| `color.action.primary` | `#D7FF63` | 主要行动和当前选择 |
| `color.content.purple` | `#8B73FF` | 日程或知识分类 |
| `color.content.orange` | `#EA4E00` | 任务阶段或内容分类 |
| `color.content.peach` | `#FFB183` | 次级任务阶段 |
| `color.content.cream` | `#F4E6C5` | 低优先级分段 |

边框、阴影、状态色、字号、间距、圆角和动效由实现阶段根据 Figma 变量与组件属性补齐。若 Figma 没有可复用变量，则先创建代码令牌并回写 Figma，避免双重来源。

## 6. 首批组件范围

### 6.1 Foundations

Color、Typography、Spacing、Radius、Border、Shadow、Motion、Breakpoints、Focus Ring。

### 6.2 Primitives

- `UiButton`：`primary | secondary | quiet | text | danger`，`sm | md | lg`，支持图标、加载和全宽。
- `UiIconButton`：固定点击热区，要求可访问名称和 Tooltip。
- `UiInput`、`UiTextarea`、`UiSelect`：统一标签、说明、错误和禁用结构。
- `UiTag`、`UiBadge`：内容分类与状态表达分离。
- `UiProgress`：线性进度、未知进度和分段进度。
- `UiDivider`、`UiSpinner`、`UiSkeleton`、`UiEmpty`。

### 6.3 Composites 与 Patterns

- `UiSearchInput`：模式选择、输入框、分类选择与提交动作。
- `UiPanelHeader`：标题、辅助文字和操作插槽。
- `UiProgressRow`：名称、状态、数值和进度。
- `UiWidgetFrame`：统一 Widget 标题、内容、加载、错误和空状态。
- `UiAppShell`：顶部导航、侧栏、内容区和右侧 Dock。
- `UiDashboardGrid` 与 `UiDashboardItem`：网格负责响应式列数，条目负责 1x1、2x1、2x2、2x3 等逻辑跨度。

### 6.4 首页 Widgets

`TaskWidget`、`CalendarWidget`、`AutomationQueueWidget`、`KnowledgeWidget`、`CreationWidget`、`WorkflowWidget`。

Widget 可以访问领域数据和服务；Primitives、Composites 和 Patterns 不得直接请求 API 或读取 Pinia 业务状态。

## 7. 组件契约

每个公开组件必须提供：

1. 一句话定义，以及何时使用和不应何时使用。
2. Anatomy：根节点、内容区、状态区和操作区。
3. 类型、尺寸、状态及允许的组合。
4. Vue `props`、`emits`、`slots` 和公开类型。
5. 语义 DOM 与键盘交互说明。
6. WCAG AA 对比度、焦点可见性、Reduced Motion 和点击热区要求。
7. 组件级令牌表。
8. 默认、边界、加载、禁用、错误和响应式示例。
9. Figma Component Set 名称与节点映射。
10. 变更记录和废弃策略。

## 8. 文档与测试方式

Storybook 是组件目录和开发沙盒，不是第二套应用。文档导航使用第 4.1 节的功能分类；原子依赖层在每页的“依赖关系”中说明。

每个组件至少具备：

- Vue Test Utils + Vitest 的渲染和交互测试。
- Storybook 的默认、变体、状态和窄屏故事。
- addon-a11y 自动检查。
- 关键组件的键盘操作断言。

首页迁移后保留现有业务 API 行为，并增加桌面与移动端截图验证。测试只证明其覆盖的行为，不用单个构建成功替代组件、响应式和视觉验证。

## 9. 响应式策略

- `>= 1280px`：完整 AppShell，侧栏、主网格和 Dock 同时可见。
- `1024px - 1279px`：Dock 进入可切换抽屉，主网格保持多列。
- `768px - 1023px`：侧栏折叠为图标导航或抽屉，Widget 降低列跨度。
- `< 768px`：单列内容流，顶部保留核心导航，次要操作进入菜单。

组件使用容器宽度决定内部布局；页面断点只负责 AppShell 和 DashboardGrid。固定格式元素用 `minmax`、`aspect-ratio` 或明确尺寸约束，避免内容变化导致布局跳动。

## 10. 代码边界

组件源码位于 `frontend/src/design-system/`，Storybook stories 位于同目录组件旁或 `frontend/src/stories/`。通过 `frontend/src/design-system/index.js` 暴露公共 API，应用代码不直接跨目录引用组件内部文件。

第一阶段保持为仓库内模块，使用 `@study-ui` 别名。首页验证稳定后，再决定是否拆成 workspace package 或发布 npm 包。

## 11. 迁移策略

1. 建立令牌、Storybook 和测试基线。
2. 建立首批 Primitives。
3. 建立 Composites 和 Patterns。
4. 建立六个首页 Widgets。
5. 将首页业务逻辑拆成 composables，页面只负责编排。
6. 切换 AppShell 和首页，完成响应式及视觉校验。
7. 建立 Figma 映射和维护指南。

迁移采用逐组件替换，不一次性重写所有页面。未迁移页面继续使用旧样式，直到公共原语稳定后按页面推进。

## 12. 非目标

- 第一阶段不实现 Ant Design 的全部组件数量。
- 第一阶段不把 Study UI 发布到公共 npm。
- 第一阶段不重构首页之外的业务请求和后端接口。
- 第一阶段不自动生成 Figma 页面或覆盖用户现有设计节点。
- 第一阶段不将 Markdown 阅读主题强行改造成 Dashboard 主题。

## 13. 验收

验收必须同时包含：组件单元测试、Storybook 构建、应用构建、首页业务回归、四档响应式截图、键盘导航、对比度与无障碍检查，以及 Figma 对照审查。全部证据通过后，首页组件库试点才算完成。
