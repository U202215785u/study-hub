# Study Hub Figma MCP 交接报告

生成时间：2026-06-07  
工作目录：`C:\Users\Administrator\Documents\Codex\2026-06-07\files-mentioned-by-the-user-designer`

## 1. 用户目标

用户想确认并推进一种工作流：

- 将开发给的 HTML 原型提取成 Figma 页面。
- 将页面中的 UI 元素提取为 Figma 组件库。
- 后续在 Figma 修改组件库，页面实例跟着变化，实现所见即所得的设计工作流。
- 进一步希望安装并使用 Figma MCP 工具执行该流程，同时检查当前 HTML 是否结构干净、是否适合 MCP 转换。

## 2. 相关源文件

用户提到并已检查的文件：

- `F:\360MoveData\Users\Administrator\Desktop\study web\study-hub\project-memory\ui\study-hub-dashboard-style-refresh.html`
- `F:\360MoveData\Users\Administrator\Desktop\study web\study-hub\project-memory\ui\designer-handoff.md`
- `F:\360MoveData\Users\Administrator\Desktop\study web\study-hub\project-memory\ui\designer-handoff-tokens.md`
- `F:\360MoveData\Users\Administrator\Desktop\study web\study-hub\project-memory\ui\figma-setup-guide.md`

其中 HTML 是一个单文件高保真原型，包含 14 个页面。

## 3. 已完成事项

### 3.1 Figma 插件安装

已通过 Codex 插件安装流程安装：

- 插件：`figma@openai-curated`
- 状态：安装成功，用户已确认。

本地配置中可见：

```toml
[plugins."figma@openai-curated"]
enabled = true
```

---

# 2026-06-07 最新补充：用户手改首页卡片已按名称规范化

## 本次处理对象

- Figma 文件：`https://www.figma.com/design/PNtsihFRjK18x3SpFFWBjX`
- fileKey：`PNtsihFRjK18x3SpFFWBjX`
- 页面：`Study Hub 设计系统草稿`
- 目标画板：`改——首页仪表盘 / 修复版样板`
- 目标画板节点：`69:416`

## 本次用户要求

用户更新了 `改——首页仪表盘 / 修复版样板` 的视觉样式，并手动改过卡片。要求：

- 不重建整块首页。
- 保留用户手改的位置、尺寸、内容和布局。
- 根据卡片名字生成并规范化卡片样式。

## 已执行结果

已在 Figma 中对目标画板 `69:416` 下所有 `小组件 / ...` 卡片做局部规范化，共 10 张。

本次只调整：

- 卡片背景色。
- 卡片描边色。
- 卡片阴影。
- 卡片圆角。
- 卡片内边距和间距。
- 卡片内部文字层级。
- 部分小元素的轻量标签式视觉。
- 节点 shared plugin data 中的样式追踪信息。

本次没有调整：

- 画板位置。
- 卡片位置。
- 卡片尺寸。
- 用户手写文案。
- 用户手动排布关系。

## 卡片名称到样式规则

| 卡片节点 | 卡片名称 | 生成样式 | 强调色 | 圆角 |
|---|---|---|---|---|
| `69:520` | `小组件 / 工作热力` | 数据图表卡 | `#ff8655` | `24` |
| `69:590` | `小组件 / 最近知识` | 知识列表卡 | `#68d8ff` | `22` |
| `69:595` | `小组件 / 创作入口` | 快捷入口卡 | `#d7ff63` | `24` |
| `79:92` | `小组件 / 创作入口` | 快捷入口卡 | `#d7ff63` | `24` |
| `69:604` | `小组件 / 今日手账` | 手账记录卡 | `#b9a7ff` | `20` |
| `69:607` | `小组件 / 文档统计` | 统计指令卡 | `#59f86d` | `20` |
| `79:88` | `小组件 / 文档统计` | 统计指令卡 | `#59f86d` | `20` |
| `69:484` | `小组件 / 自动化队列` | 队列状态卡 | `#d7ff63` | `24` |
| `69:499` | `小组件 / 今日重点` | 重点任务卡 | `#8b73ff` | `24` |
| `69:512` | `小组件 / 队列概览` | 小型指标卡 | `#d7ff63` | `18` |

## 验证结果

复查目标画板 `69:416` 后确认：

- 共找到 10 张 `小组件 / ...` 卡片。
- 10 张卡片都已经写入 `card_variant`、`accent`、`style_rule` 追踪信息。
- `missingCount = 0`，没有遗漏未规范化卡片。
- 规范化后的卡片仍保留用户手改的位置与尺寸。

## 后续注意

- 继续遵守“先 inspect，再局部 patch”的方式，不要整块重建覆盖用户手改版本。
- 当前规则是“卡片节点名称优先”。例如节点名是 `小组件 / 今日重点`，即使卡片内部标题文字被用户改成了“时间规划”，仍按“重点任务卡”样式处理。
- 下一步建议把这批已稳定的卡片规则抽成正式 `Widget Card` Component Set，再逐步把首页中的假卡片替换为真实实例。

### 3.2 Figma MCP 配置

已通过 Codex CLI 添加官方 Figma MCP：

```text
codex mcp add figma --url https://mcp.figma.com/mcp
```

添加结果：

- MCP 名称：`figma`
- URL：`https://mcp.figma.com/mcp`
- 状态：`enabled`
- Auth：`OAuth`

本地配置中可见：

```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
```

### 3.3 Figma OAuth 登录

OAuth 流程已成功完成。

烟雾测试中确认 Figma 身份：

- 用户名：`章业态`
- 邮箱：`z2794425301@gmail.com`

### 3.4 Figma MCP 可用性测试

通过新启动的 Codex CLI 子任务验证，Figma MCP 工具可用。

已确认可用工具包括：

- `whoami`
- `create_new_file`
- `use_figma`
- `get_metadata`
- `get_design_context`
- `get_screenshot`
- `generate_diagram`
- `generate_figma_design`
- `upload_assets`
- `search_design_system`
- `get_libraries`
- Code Connect 相关工具

### 3.5 已创建测试 Figma 文件

已成功创建一个空白测试文件：

- 文件名：`Study Hub MCP Smoke Test`
- 链接：https://www.figma.com/design/cISxJj0PDVOw6IHvNeTCtt

说明：这是 smoke test 文件，只用于验证 MCP 能创建 Figma 文件，不是正式设计系统文件。

## 4. 当前卡点

正式创建 `Study Hub Design System Draft` 时，Figma MCP 的 `whoami` 返回多个可用团队/plan，需要选择创建在哪个团队：

- `zhang力's team`，full seat
- `翘课小分队`，full seat
- `a`，full seat
- `咸鱼`，view seat，不建议用于创建文件

第一次正式执行时，子任务停在“请选择团队”。

第二次已指定使用 `zhang力's team` 继续执行，但用户中途主动中断了该任务，因此：

- 无法确认正式 `Study Hub Design System Draft` 是否创建成功。
- 当前没有拿到正式 Draft 文件 URL。
- 后续应重新执行正式创建任务，建议直接指定 `zhang力's team`，避免再次卡在选择团队。

## 5. HTML 结构体检结果

已对 `study-hub-dashboard-style-refresh.html` 做了结构统计。

关键结果：

```json
{
  "lines": 4370,
  "topNavs": 14,
  "navLinks": 152,
  "buttons": 247,
  "inputs": 1,
  "inlineStyles": 360,
  "inlineOnclick": 207,
  "draggable": 9,
  "important": 178,
  "uniqueCssVariables": 19
}
```

语义标签统计：

```json
{
  "header": 0,
  "nav": 0,
  "main": 0,
  "aside": 0,
  "section": 0,
  "article": 0,
  "footer": 0
}
```

已识别 14 个页面：

- `home`
- `wiki`
- `kb`
- `auto`
- `ddl`
- `journal`
- `flow`
- `creator`
- `search`
- `notifications`
- `profile`
- `settings`
- `secondself`
- `skillmarket`

每个页面都重复包含一套顶部导航，`top-nav-bar` 共 14 处。

## 6. 对 HTML 是否适合 MCP 的判断

结论：**适合做视觉捕获，不适合直接一键生成干净组件库。**

原因：

- HTML 是高保真单文件演示稿，不是组件化源码。
- 顶部导航等公共组件重复写了 14 次，没有抽象成复用结构。
- 有大量内联样式，自动转换后容易生成大量不可维护的图层样式。
- 有大量内联 `onclick`，更像原型交互，不利于设计系统提取。
- 使用 `!important` 较多，说明样式层叠已经比较重。
- 语义结构弱，几乎全靠 `div` 和 class，MCP 很难自动理解哪些是页面、区块、组件、实例关系。
- 当前 CSS token 只有 19 个，足够做 v0 foundations，但不足以直接形成完整专业组件库。

更准确的定位：

- 可以用 `generate_figma_design` 或浏览器捕获方式做“视觉参考稿”。
- 不能指望它自动变成干净的 Figma Auto Layout + Components + Variants。
- 应先建立 Figma 变量和组件库，再用组件实例重建页面。

## 7. 推荐下一步

建议不要一次性导完整 14 页。先做 v0：

1. 创建正式 Figma 文件：`Study Hub Design System Draft`
2. 指定团队：`zhang力's team`
3. 创建 4 个页面：
   - `Cover`
   - `Foundations`
   - `Component Inventory`
   - `Screen Map`
4. 在 `Foundations` 放入：
   - 颜色 token swatches
   - 字号层级
   - spacing/radius/shadow/motion 摘要
5. 在 `Component Inventory` 放入组件规格卡：
   - Top Nav
   - Button
   - Card / Widget
   - Sidebar
   - Dock Panel
   - Tag / Chip
   - Input / Search
   - Toggle
   - Modal
   - Progress / Status
   - Skill Card
   - Chat Bubble
6. 在 `Screen Map` 放入 14 个页面卡片，并标记：
   - Home / Dashboard 为最高优先级
   - Wiki、Second Self、Settings 为下一批
7. v0 验收后，再逐个做真正的 Figma 组件和页面实例。

## 8. 给下一个会话的可直接使用提示词

可以直接复制给新的 Codex 会话：

```text
继续 Study Hub 的 Figma MCP 工作。

已完成：
- Figma 插件 figma@openai-curated 已安装。
- Figma MCP 已配置：figma -> https://mcp.figma.com/mcp。
- OAuth 已登录成功，账号是 章业态 / z2794425301@gmail.com。
- 已创建 smoke test 文件：https://www.figma.com/design/cISxJj0PDVOw6IHvNeTCtt。

请使用 Figma MCP，指定团队/plan 为 `zhang力's team`，创建正式文件：
Study Hub Design System Draft

源文件：
- F:/360MoveData/Users/Administrator/Desktop/study web/study-hub/project-memory/ui/study-hub-dashboard-style-refresh.html
- F:/360MoveData/Users/Administrator/Desktop/study web/study-hub/project-memory/ui/designer-handoff.md
- F:/360MoveData/Users/Administrator/Desktop/study web/study-hub/project-memory/ui/designer-handoff-tokens.md

先不要导完整 14 页。
只做 v0 Figma 设计系统草稿：
- Cover
- Foundations
- Component Inventory
- Screen Map

Foundations：加入 :root 的颜色 token swatches、字体层级、spacing/radius/shadow 摘要。
Component Inventory：加入 Top Nav、Button、Card/Widget、Sidebar、Dock Panel、Tag/Chip、Input/Search、Toggle、Modal、Progress/Status、Skill Card、Chat Bubble 的规格卡。
Screen Map：加入 14 个页面卡片，标记 Home/Dashboard 为最高优先级。

完成后返回 Figma 文件 URL、创建的页面列表、限制说明。
```

## 9. 注意事项

- 当前主会话工具面板没有直接暴露 `use_figma` 等 Figma MCP 工具，但新启动的 `codex exec` 子任务可以使用这些工具。
- 正式执行时不要再让模型询问团队，直接指定 `zhang力's team`。
- 若要完整可维护组件库，需要分阶段做，不建议一次性自动导入全部 HTML。
- HTML 可以作为视觉参考和 token 来源，但组件库应从 token + 组件规格重建。
# 2026-06-07 最新交接：Study Hub Figma MCP 设计系统草稿

> 这一节是当前最新状态。上方旧内容有编码乱码，后续会话优先读本节。

## 当前 Figma 文件

- 正式文件：`Study Hub Design System Draft`
- URL：https://www.figma.com/design/PNtsihFRjK18x3SpFFWBjX
- fileKey：`PNtsihFRjK18x3SpFFWBjX`
- Figma 账号：`章业态 / z2794425301@gmail.com`
- 团队：`zhang力's team`
- 当前页面：只保留 1 个页面，页面名为 `Study Hub 设计系统草稿`
- 主画布/frame 名称：`Study Hub 设计系统草稿 / 单页总览——改`

## 已完成内容

### 1. 单页中文化

用户要求所有内容在同一个 Figma page 内完成，不再拆成 Cover / Foundations / Component Inventory / Screen Map 多页。

已完成：
- 删除多余页面，只保留单页。
- 展示文案改为中文。
- 代码变量名如 `--accent`、`--surface-1` 仅作为开发对照保留。
- 中文字体使用 `Noto Sans SC`。

### 2. 可调用基础资产

已在 Figma 本地创建真正可调用资产，不只是说明卡：

- 颜色变量集合：`Study Hub / 颜色`
  - 14 个颜色变量，例如 `color/bg/app`、`color/surface/1`、`color/text/strong`、`color/accent/primary`。
- 尺寸变量集合：`Study Hub / 尺寸`
  - 间距变量：`space/1` 到 `space/10`
  - 圆角变量：`radius/sm`、`radius/md`、`radius/lg`、`radius/xl`、`radius/2xl`、`radius/full`
- 文字样式：
  - `文字/极小文字`
  - `文字/小号文字`
  - `文字/正文文字`
  - `文字/小标题`
  - `文字/面板标题`
  - `文字/页面标题`
  - `文字/大数值`
  - `文字/超大标题`
- 阴影样式：
  - `阴影/卡片默认`
  - `阴影/卡片悬停`
  - `阴影/弹窗`

同一页面中已新增 `四、可调用基础资产` 区块，放了真实字号、真实间距、真实圆角、真实阴影样张。

### 3. 方法决策

已和用户确认：采用 **页面逻辑先行，原子资产跟随抽取**。

理由：
- Study Hub 当前还不是成熟设计系统。
- 先纯原子化容易做出一堆漂亮但不知道服务哪个页面的零件。
- 应先用首页样板验证信息架构、信息密度、导航关系、卡片关系，再抽取稳定模式。

### 4. 首页仪表盘样板

已新增并多次修复 `五、首页仪表盘样板`。

当前重点：
- 样板屏宽：`1440`
- 工作区按 8 栏网格居中。
- 8 栏内容区宽度公式：`8 * 155 + 7 * 14 = 1338`
- 左右边距：`51 / 51`
- 顶部导航、标题、副文、状态标签、网格和卡片应对齐同一条内容边界。

当前首页样板相关节点曾有多个副本：
- `首页仪表盘 / 居中修复版`
- `首页仪表盘 / 修复版样板`
- 用户后续手动调整过其中一版，并将主画布命名为 `Study Hub 设计系统草稿 / 单页总览——改`

后续不要盲目覆盖用户手改内容。应先 inspect 当前节点，再局部修正。

### 5. 组件系统 v0

已新增 `六、组件系统 v0` 区块。

目的：修复“只是画得像组件，但不是真组件规则”的问题。

已放入：
- 按钮 v0
  - 使用 Auto Layout。
  - 宽度由文字宽度 + 左右内边距决定。
  - 小 / 中 / 大高度规则分别约为 34 / 40 / 48。
- 标签 v0
  - 使用 Auto Layout。
  - 宽度由内容自适应。
  - 文字作为子节点居中。
- 小组件卡片 v0
  - 基础格：`180 x 160`
  - 间距：`14`
  - 1x1、2x2、4x2 有明确尺寸公式。
  - 1x1 圆角建议 `16`，跨格卡片圆角建议 `22`。

注意：这些目前主要是 v0 规格样张，还没有全部转成正式 Component Set。下一步可以做真正组件化。

## 已发现并修复的问题

用户指出的问题：
1. 中文字符有明显偏移。
2. 网格系统和卡片圆角不匹配。
3. 组件系统没有建立，按钮长度、按钮文字绑定、卡片规则都不可追踪。
4. 工作区主要区域没有居中。
5. 用户手改版导航中，红框区域（搜索、通知、头像）未在目标容器中右对齐。

已采取的修复：
- 首页样板重建为 Auto Layout 驱动版本。
- 导航项、按钮、标签改为 Auto Layout，文字作为子节点居中。
- 工作区内容区居中：内容宽 `1338`，左右边距 `51`。
- 增加 `组件系统 v0` 区块，记录按钮 / 标签 / 卡片规则。
- 对用户手改版本的导航做了局部修正：将搜索、通知、头像包成 `右侧操作区 / 右对齐`。

## 最近一次精确操作：导航右侧操作区右对齐

用户截图要求：红框内 `搜索框 + 通知 + 头像` 在导航目标容器内右对齐。

已定位并修改的节点：
- 目标导航：`69:418`，名称 `顶部导航 / Auto Layout`
- 父级：`首页仪表盘 / 修复版样板`
- 搜索框：`69:440`
- 通知按钮：`69:442`
- 头像按钮：`69:444`
- 新增右侧组：`74:2`，名称 `右侧操作区 / 右对齐`

修改结果：
- `右侧操作区 / 右对齐` 是导航内的独立 Auto Layout 组。
- 搜索框、通知按钮、头像按钮已放入该组。
- 该组在导航中使用 absolute 定位。
- 目标右边距：`18px`
- 导航宽度：`1320`
- 右侧操作区尺寸：`410 x 42`
- 右侧操作区位置：`x = 892, y = 15`
- 计算后右边距：`18`

注意：
- 第一次设置 `layoutPositioning = ABSOLUTE` 时失败，原因是节点还未放进 Auto Layout 父级。
- 第二次已按正确顺序成功：先 append 到导航，再设置 absolute。

## 下一步建议

### P0：规范化用户手改版，而不是重建覆盖

接下来应继续使用用户手改后的版本作为主版本，避免重新生成导致用户修改丢失。

建议流程：
1. 用 `use_figma` inspect 当前页面结构。
2. 找到用户正在编辑的主样板节点。
3. 对局部问题做 patch，而不是整块重建。

### P1：把组件系统 v0 转为正式 Component Set

建议先做 3 个正式组件：
1. `Button`
   - Variant：`Type=Primary/Secondary/Ghost/Danger`
   - Variant：`Size=Small/Medium/Large`
   - State：`Default/Hover/Disabled`
   - 文字作为 TEXT property 或子文本。
2. `Chip`
   - Variant：`State=Default/Active/Disabled`
   - 自适应宽度。
3. `Widget Card`
   - Variant：`Size=1x1/2x2/4x2`
   - 绑定颜色、圆角、阴影样式。

### P2：替换首页样板中的伪组件

正式组件建好后，将首页样板里的按钮、标签、小组件卡片替换为实例。

目标：
- 页面由 Component Instance 构成。
- 局部调整通过组件属性完成。
- 避免手动文字偏移、圆角漂移、尺寸不可追踪。

## 下一窗口启动提示词

```text
继续 Study Hub Figma MCP 设计系统工作。

请先读取交接文件：
F:/360MoveData/Users/Administrator/Desktop/study web/study-hub/project-memory/ui/figma-mcp-study-hub-handoff.md

当前 Figma 文件：
https://www.figma.com/design/PNtsihFRjK18x3SpFFWBjX
fileKey: PNtsihFRjK18x3SpFFWBjX

重要状态：
- 页面已收敛为单页中文草稿。
- 主画布名：Study Hub 设计系统草稿 / 单页总览——改
- 已有可调用基础资产：颜色变量、尺寸变量、文字样式、阴影样式。
- 已有首页仪表盘样板、组件系统 v0。
- 用户手改过首页样板，不要整块重建覆盖。
- 最近一次修改：把节点 69:418 中的搜索框 69:440、通知 69:442、头像 69:444 包进 74:2「右侧操作区 / 右对齐」，并在导航容器内右对齐，右边距 18px。

下一步建议：
先 inspect 当前 Figma 结构，确认用户手改主版本；然后把 Button / Chip / Widget Card 从 v0 规格样张转成正式 Component Set，再逐步替换首页样板中的伪组件。
```
