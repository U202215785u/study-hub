# Study Hub 横屏工作台 Dashboard UI 框架图

最后更新：2026-06-07  
用途：给设计同学同步方向，用于后续 UI 大改前的布局共识、信息架构和组件分区  
关联阶段：体验稳定化与产品化阶段

---

## 1. 设计目标

Study Hub 后续 UI 可以向“横屏工作台 Dashboard”演进。

目标不是做一个普通后台管理系统，而是做一个适合学习、创作、整理、自动化和个人工作流调度的横屏操作台。

关键词：

- 横屏优先
- 工作台感
- Bento Grid 模块化
- 左侧或顶部稳定导航
- 中央大画布
- 高信息密度但不拥挤
- 黑/浅灰底 + 高亮色块
- 每个模块都像一张可操作仪表卡，而不是普通列表页

参考图给出的方向可以提炼为：

- 大圆角外框或沉浸式画布
- 卡片分区明确
- 大数字、大标题、大状态
- 强对比色作为“行动点”
- 图表/时间线/卡片混排
- 横向空间充分利用
- 工具栏像设备系统的一部分，而不是网页导航

---

## 2. 总体布局建议

推荐采用“工作台壳 + 模块画布”的统一结构。

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ App Shell                                                                     │
│                                                                              │
│  ┌───────────────┐  ┌────────────────────────────────────────────────────┐   │
│  │ Left Rail     │  │ Top Command Bar                                    │   │
│  │               │  │ Search / Current Context / Quick Actions / Status  │   │
│  │ Home          │  └────────────────────────────────────────────────────┘   │
│  │ Wiki          │                                                           │
│  │ Automation    │  ┌────────────────────────────────────────────────────┐   │
│  │ Workflow      │  │ Main Workspace Canvas                              │   │
│  │ DDL           │  │                                                    │   │
│  │ Journal       │  │ Bento Cards / Timeline / Editor / Queue / Charts   │   │
│  │ Skills        │  │                                                    │   │
│  │ Settings      │  └────────────────────────────────────────────────────┘   │
│  │               │                                                           │
│  │ System        │  ┌────────────────────────────────────────────────────┐   │
│  │ Status        │  │ Bottom / Right Context Dock                        │   │
│  └───────────────┘  │ Recent / Queue / Details / Preview / AI Assistant   │   │
│                     └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 外层 App Shell

职责：

- 保持产品统一性。
- 承载全局导航、搜索、用户状态、系统状态。
- 为不同模块提供同一种空间秩序。

建议：

- 桌面端使用横屏固定画布。
- 页面主体使用 `min-height: 100vh`。
- 最大宽度可以限制在 `1440-1680px`，超宽屏居中。
- 工作台外框可以有轻微圆角和阴影，但不要每个 section 都做卡片。

### 2.2 导航结构

推荐两种可选方案。

#### 方案 A：左侧 Rail 导航，推荐

适合 Study Hub，因为模块多。

```text
┌──────────┬──────────────────────────────────────────────┐
│ Logo     │ Top Command Bar                              │
│ Home     ├──────────────────────────────────────────────┤
│ KB       │ Main Canvas                                  │
│ Wiki     │                                              │
│ Auto     │                                              │
│ Flow     │                                              │
│ DDL      │                                              │
│ Journal  │                                              │
│ Skills   │                                              │
│ Self     │                                              │
└──────────┴──────────────────────────────────────────────┘
```

优点：

- 模块切换清楚。
- 适合长期扩展。
- 和参考图里的工作台/团队/医疗 dashboard 接近。

#### 方案 B：顶部 Capsule 导航

适合更轻、更视觉化的模式。

```text
┌─────────────────────────────────────────────────────────┐
│ Logo     [Home] [Wiki] [Automation] [Workflow]   Search │
├─────────────────────────────────────────────────────────┤
│ Main Canvas                                             │
└─────────────────────────────────────────────────────────┘
```

优点：

- 更像视觉作品。
- 首屏更开阔。

缺点：

- Study Hub 模块多，顶部容易拥挤。

结论：

第一版 UI 大改建议用方案 A：左侧 Rail + 顶部 Command Bar。

---

## 3. Study Hub 首页框架图

首页应该是“总控制台”，不是普通导航页。

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Left Rail     │ Top Command Bar                                              │
│               │ ┌ Search all knowledge / actions ────────────────┐ Status   │
│               │ └────────────────────────────────────────────────┘          │
├───────────────┼──────────────────────────────────────────────────────────────┤
│               │ Hero Context Row                                             │
│               │ ┌──────────────────────────┐ ┌──────────┐ ┌──────────────┐  │
│               │ │ Today Focus              │ │ Queue    │ │ System       │  │
│               │ │ 学习/创作/待处理总览       │ │ 解析任务  │ │ Health       │  │
│               │ └──────────────────────────┘ └──────────┘ └──────────────┘  │
│               │                                                              │
│               │ Main Bento Grid                                               │
│               │ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│               │ │ Wiki Recent  │ │ Automation   │ │ DDL Timeline         │  │
│               │ │ 最近知识       │ │ 解析入口       │ │ 今日/本周计划          │  │
│               │ └──────────────┘ └──────────────┘ └──────────────────────┘  │
│               │ ┌─────────────────────────────┐ ┌────────────────────────┐  │
│               │ │ Creator / Workflow           │ │ Journal / Review       │  │
│               │ │ 创作流和自动化                 │ │ 手账和复盘              │  │
│               │ └─────────────────────────────┘ └────────────────────────┘  │
│               │                                                              │
│               │ Bottom Strip                                                  │
│               │ 最近打开 / 快捷网站 / AI 启动器 / Skill 推荐                    │
└───────────────┴──────────────────────────────────────────────────────────────┘
```

### 首页卡片建议

| 区块 | 作用 | 内容 |
|---|---|---|
| Today Focus | 当前工作焦点 | 今日任务、最近文档、继续学习 |
| Queue | 自动化任务 | 解析中、失败、完成、批量队列 |
| System | 系统状态 | 后端连接、扩展状态、API 状态 |
| Wiki Recent | 知识入口 | 最近 Wiki、最近文档、搜索 |
| Automation | 采集入口 | 抖音/B站/小红书、批量导入 |
| DDL Timeline | 时间规划 | 今日、周、月、超期 |
| Creator/Workflow | 创作与流程 | 工作流模板、Skill 快捷入口 |
| Journal/Review | 记录与复盘 | 今日手账、随机回顾、周报 |

---

## 4. 模块页统一框架

每个模块页不要完全重新发明布局，而是使用同一套三段结构。

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Module Header                                                                 │
│ Title / Subtitle / Primary Action / Filters / Status                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ Module Workspace                                                              │
│                                                                              │
│ ┌───────────────┐ ┌─────────────────────────────────────┐ ┌───────────────┐ │
│ │ Index / List  │ │ Main Content / Editor / Canvas       │ │ Detail Dock   │ │
│ │               │ │                                     │ │ Preview/AI    │ │
│ │ Categories    │ │ Markdown / Timeline / Workflow       │ │ Metadata      │ │
│ │ Search        │ │ Cards / Charts / Forms               │ │ Actions       │ │
│ └───────────────┘ └─────────────────────────────────────┘ └───────────────┘ │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ Context Bar / Queue / Recent / Shortcuts                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Header

必须包含：

- 模块名称
- 当前上下文
- 主要操作按钮
- 搜索/筛选/排序
- 状态反馈

示例：

```text
Wiki Knowledge
[Search pages...] [New Page] [Compile] [Theme] [More]
```

### 4.2 Workspace

不同模块可替换中间内容：

| 模块 | Main Content |
|---|---|
| Wiki | Markdown 阅读/编辑 |
| KnowledgeBase | 文档列表 + 预览 |
| Automation | 解析入口 + 队列 |
| Workflow | 模板编辑 + 执行记录 |
| DDL | 日/周/月/列表时间画布 |
| Journal | 日历 + 手账编辑 |
| Skill Market | Skill 卡片矩阵 |
| Creator Hub | Skill/工作流推荐面板 |
| SOP | 流程链编辑器 |
| Second Self | 对话 + 记忆/导入面板 |

### 4.3 Detail Dock

右侧 Dock 用于：

- 当前对象详情
- 预览
- AI 分析
- 元信息
- 任务状态
- 快捷操作

不要把所有弹窗都做成覆盖式 Modal。横屏工作台应优先使用 Dock/Drawer，让用户保持上下文。

---

## 5. Wiki 页面框架图

```text
┌──────────┬───────────────────────────────────────────────────────────────────┐
│ Rail     │ Wiki Header                                                       │
│          │ [Search pages] [New Page] [Edit] [Theme] [Open Tab]               │
├──────────┼───────────────┬──────────────────────────────────┬───────────────┤
│          │ Wiki Index    │ Reading / Editing Canvas          │ Preview Dock  │
│          │               │                                  │               │
│          │ Categories    │ # Page Title                      │ Wikilink      │
│          │ Page List     │ Metadata chips                    │ Preview       │
│          │ Tags          │ Cover Image                       │ Backlinks     │
│          │ Recent        │ Markdown Content                  │ Related       │
│          │               │                                  │ Actions       │
├──────────┴───────────────┴──────────────────────────────────┴───────────────┤
│ Context Bar: recent pages / compile status / unsaved state                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

设计重点：

- 搜索和新建必须是首屏可见。
- 编辑不建议只藏在文章右上角的小按钮里。
- 右侧预览保留横屏优势。
- 元信息用 chips，不挤在一行。
- 主题切换可以放 Header，不做漂浮孤岛。

---

## 6. Automation 页面框架图

```text
┌──────────┬───────────────────────────────────────────────────────────────────┐
│ Rail     │ Automation Header                                                 │
│          │ [Paste URL / Batch Input] [Platform] [Submit] [Queue]             │
├──────────┼────────────────────────────┬──────────────────────────────────────┤
│          │ Submit Panel               │ Queue / Progress Canvas              │
│          │                            │                                      │
│          │ Douyin / Bilibili / XHS    │ Running Task                          │
│          │ Batch Links                │ Step Progress                          │
│          │ Dependency Check           │ Completed / Failed                     │
│          │                            │ Diagnostics                            │
├──────────┼────────────────────────────┴──────────────────────────────────────┤
│          │ Result Cards: generated docs / summaries / retry actions           │
└──────────┴───────────────────────────────────────────────────────────────────┘
```

设计重点：

- 长任务必须主视觉化，不要只靠小 toast。
- 队列要能解释“现在卡在哪一步”。
- 失败要给用户下一步：重试、复制诊断、查看依赖。
- 批量任务要显示部分成功/部分失败。

---

## 7. DDL 时间规划框架图

```text
┌──────────┬───────────────────────────────────────────────────────────────────┐
│ Rail     │ DDL Header                                                        │
│          │ [Today] [Day] [Week] [Month] [List] [New Task]                    │
├──────────┼──────────────────────────────────────────────┬────────────────────┤
│          │ Calendar / Timeline Canvas                   │ Detail Panel       │
│          │                                              │                    │
│          │ Day Time Grid / Week Columns / Month Grid     │ Selected Task      │
│          │ Milestones / Todo List                        │ Status            │
│          │                                              │ Related Docs       │
├──────────┴──────────────────────────────────────────────┴────────────────────┤
│ Bottom Strip: overdue / this week / completed / upcoming                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

设计重点：

- DDL 是时间画布，不只是待办列表。
- 日/周/月切换要像 dashboard tab。
- 新建任务可以从时间格直接触发。
- 超期/临近状态要明显，但不要满屏警告色。

---

## 8. Journal 手账框架图

```text
┌──────────┬───────────────────────────────────────────────────────────────────┐
│ Rail     │ Journal Header                                                    │
│          │ [Date] [Mood] [Weather] [Location] [Random Review]                │
├──────────┼───────────────┬──────────────────────────────────┬───────────────┤
│          │ Month Rail    │ Writing Canvas                    │ Reflection    │
│          │ Calendar      │                                  │ Mood Stats    │
│          │ Timeline      │ Date as title                     │ Tags          │
│          │ Past Entries  │ Free writing area                 │ Random        │
│          │               │ Stickers / tags                   │ Memories      │
└──────────┴───────────────┴──────────────────────────────────┴───────────────┘
```

设计重点：

- Journal 可以比其他模块更柔和，但仍使用同一工作台壳。
- 写作区要有“纸面感”，但不破坏整体 dashboard。
- 保存反馈要温和，不做强打卡压迫感。

---

## 9. Workflow / SOP 框架图

```text
┌──────────┬───────────────────────────────────────────────────────────────────┐
│ Rail     │ Flow Header                                                       │
│          │ [Create from text] [Templates] [Run] [Archive]                    │
├──────────┼──────────────────────────────┬────────────────────────────────────┤
│          │ Template / Block List         │ Flow Canvas                         │
│          │                              │                                    │
│          │ Templates / SOP Blocks        │ Steps / Gates / Connections         │
│          │ Search / Filters              │ Drag / Configure / Run              │
├──────────┼──────────────────────────────┴────────────────────────────────────┤
│          │ Run Output Dock: status / files / logs / errors                    │
└──────────┴───────────────────────────────────────────────────────────────────┘
```

设计重点：

- 工作流和 SOP 都是“流程画布”。
- 左侧是素材，中央是编排，右侧/底部是运行结果。
- 错误要绑定步骤，而不是只在页面顶部报错。

---

## 10. Skill Market / Creator Hub 框架图

```text
┌──────────┬───────────────────────────────────────────────────────────────────┐
│ Rail     │ Skills Header                                                     │
│          │ [Search skills] [Category] [Installed] [Sync]                     │
├──────────┼──────────────────────────────────────────────┬────────────────────┤
│          │ Skill Grid                                   │ Detail / Install   │
│          │                                              │                    │
│          │ Community Skills / Local Skills               │ Description        │
│          │ Platform Skills / Creator Workflows           │ Install Status     │
│          │                                              │ Related Flow       │
└──────────┴──────────────────────────────────────────────┴────────────────────┘
```

设计重点：

- Skill 不只是列表，要像“能力卡片市场”。
- Creator Hub 可复用 Skill Market 的卡片系统。
- 安装状态、启用状态、来源、风险提示要标准化。

---

## 11. 色彩与质感方向

参考图里有三类方向：

### 11.1 Dark Neon 工作台

适合：

- Home
- Automation
- Workflow
- Skill Market

建议：

```text
Background: graphite / near black
Cards: dark gray with soft border
Accent: acid lime or electric green
Secondary Accent: violet / cyan / warm yellow, 少量使用
Text: off-white + muted gray
```

注意：

- 不要整个产品都变成单一荧光绿。
- 高亮色只用于状态、主行动、关键数字。

### 11.2 Light Frost 工作台

适合：

- Journal
- Wiki 阅读
- DDL

建议：

```text
Background: warm gray / off-white
Cards: translucent white / pale gray
Accent: lime / soft blue / muted violet
Text: near black
```

注意：

- 保留信息密度，不要做成空洞的清新页面。

### 11.3 Hybrid 模式

推荐 Study Hub 最终采用混合策略：

- App Shell 可暗色。
- 阅读/写作内容区可浅色。
- 数据和任务卡片使用高亮色。
- 每个模块允许局部情绪差异，但导航、按钮、反馈保持一致。

---

## 12. 设计 Token 初稿

这些不是最终值，是给设计同学定方向。

```text
Canvas
  app-bg-dark: #0b0c0d
  app-bg-light: #eef0eb
  surface-dark: #1b1c1d
  surface-light: #f7f7f2

Accent
  accent-lime: #dfff2f
  accent-green: #5cff5c
  accent-violet: #8b5cf6
  accent-coral: #ed765b
  accent-blue: #8fb4ff

Text
  text-primary-dark: #f5f5f0
  text-secondary-dark: #a8aaa5
  text-primary-light: #111111
  text-secondary-light: #62645f

Shape
  radius-card: 24px
  radius-panel: 32px
  radius-pill: 999px
  border-strong: 2px
  border-soft: 1px
```

实际落地时，卡片圆角可以根据组件层级调整：

- 小按钮：999px pill
- 普通卡片：16-24px
- 大面板：28-36px
- 外层工作台：32-48px

---

## 13. 组件地图

第一批必须统一：

```text
AppShell
LeftRail
TopCommandBar
WorkspaceHeader
BentoCard
MetricCard
ActionCard
StatusBadge
ProgressStrip
DetailDock
PreviewDrawer
CommandButton
IconButton
SearchInput
SegmentedTabs
EmptyState
ErrorState
Toast
Modal
```

模块映射：

| 组件 | 主要使用模块 |
|---|---|
| AppShell | 全部模块 |
| LeftRail | 全部模块 |
| TopCommandBar | 全部模块 |
| BentoCard | Home、Skill Market、Creator Hub |
| MetricCard | Home、DDL、Automation |
| DetailDock | Wiki、KnowledgeBase、Skill Market、Workflow |
| ProgressStrip | Automation、Workflow、DDL |
| PreviewDrawer | Wiki、KnowledgeBase、Queue |
| Modal | Wiki、DDL、Journal、SOP |
| EmptyState | 全部模块 |
| ErrorState | 全部模块 |

---

## 14. 响应式规则

桌面优先，但不能完全放弃窄屏。

### 14.1 Desktop：1280px 以上

```text
Left Rail 固定
Top Command Bar 固定
Main Canvas 2-4 列 bento
Right Dock 可常驻
```

### 14.2 Tablet：768px - 1279px

```text
Left Rail 收缩为 icon rail
Main Canvas 2 列
Right Dock 变 Drawer
```

### 14.3 Mobile：390px - 767px

```text
Left Rail 变底部导航或顶部菜单
Main Canvas 单列
Detail Dock 变全屏抽屉
图表和时间线降级为列表/横向滚动
```

移动端不是主设计目标，但核心路径必须可用。

---

## 15. 给设计同学的交付建议

第一轮设计不要直接做所有页面高保真。

建议先做 4 张图：

1. App Shell 总框架
   - 左侧 Rail
   - 顶部 Command Bar
   - 主画布
   - 右侧 Dock

2. Home 总控制台
   - Today Focus
   - Queue
   - Wiki Recent
   - Automation
   - DDL
   - Journal

3. Wiki 横屏工作台
   - 左侧索引
   - 中央阅读/编辑
   - 右侧预览

4. Automation 长任务工作台
   - 提交区
   - 队列区
   - 进度区
   - 结果区

第二轮再扩展：

- DDL
- Journal
- Workflow
- Skill Market / Creator Hub

---

## 16. 与当前体验测试的关系

UI 大改后，之前的测试不会全部作废。

长期保留：

- 核心路径
- 数据一致性
- 后端/API 稳定性
- 边界场景
- 历史 P1/P2 问题

需要重测：

- 入口可发现性
- 视觉层级
- 布局
- 移动端
- 截图基线
- 美观评分

因此，后续每张任务卡都要拆成：

```text
功能路径测试：长期复用
视觉体验测试：UI 大改后重测
```

---

## 17. 第一轮设计验收标准

设计同学第一轮交付时，至少回答：

- 全局导航放哪里？
- 搜索和命令入口放哪里？
- 每个模块怎么回到总工作台？
- 长任务状态如何展示？
- 详情/预览是弹窗、抽屉还是右侧 Dock？
- 新建/编辑/保存这类主操作在哪里？
- 空状态和错误状态长什么样？
- 390px、768px、1280px 三档如何降级？

不需要第一轮就确定：

- 所有最终色值
- 所有动效
- 所有图表细节
- 所有模块高保真

