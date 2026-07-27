# Study Hub — 底层 Design Token 规范（设计师可改版）

> 本文档从现有原型 `study-hub-dashboard-style-refresh.html` 中提取了**所有硬编码的尺寸、间距、网格、字体、颜色、阴影、动效、Z-index 等参数**，整理为系统化的 Design Token。设计师可直接在此文档基础上修改数值，开发按新 Token 映射即可。
>
> **文档定位**：这不是"建议"，而是"现状的精确快照"。每个 Token 都标注了当前值、使用场景、出现次数。设计师改哪个，开发替换对应的 CSS Variable 即可。

---

## 目录

1. [网格系统 (Grid System)](#一网格系统-grid-system)
2. [间距体系 (Spacing Scale)](#二间距体系-spacing-scale)
3. [布局模板 (Layout Templates)](#三布局模板-layout-templates)
4. [字体层级 (Typography Scale)](#四字体层级-typography-scale)
5. [颜色 Token (Color Tokens)](#五颜色-token-color-tokens)
6. [圆角体系 (Border Radius)](#六圆角体系-border-radius)
7. [阴影体系 (Shadow System)](#七阴影体系-shadow-system)
8. [组件尺寸规范 (Component Sizing)](#八组件尺寸规范-component-sizing)
9. [边框规范 (Border System)](#九边框规范-border-system)
10. [动效规范 (Motion Tokens)](#十动效规范-motion-tokens)
11. [Z-index 层级 (Elevation)](#十一z-index-层级-elevation)
12. [响应式断点 (Breakpoints)](#十二响应式断点-breakpoints)
13. [设计师修改指南](#十三设计师修改指南)

---

## 一、网格系统 (Grid System)

### 1.1 Dashboard 8×4 网格（Home 页面核心）

```
┌─────────────────────────────────────────────────────────────┐
│  1×1  │  1×1  │  2×2  │  2×2  │  1×1  │  1×1  │  4×2  │
│       │       │       │       │       │       │       │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┤
│  1×1  │  1×1  │       │       │  1×1  │  1×1  │       │
│       │       │       │       │       │       │       │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┤
│  2×2  │  2×2  │  1×1  │  1×1  │  1×1  │  1×1  │       │
│       │       │       │       │       │       │       │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┤
│       │       │  1×1  │  1×1  │  1×1  │  1×1  │       │
│       │       │       │       │       │       │       │
└───────┴───────┴───────┴───────┴───────┴───────┴───────┘
```

| Token | 当前值 | 说明 | 出现位置 |
|-------|--------|------|----------|
| `grid-columns` | `8` | 列数 | `.dashboard-grid` |
| `grid-rows` | `4` | 行数 | `.dashboard-grid` |
| `grid-gap` | `12px` | 基础网格间距 | `.dashboard-grid`, `.grid-bg` |
| `grid-gap-override` | `14px` | 覆盖后的间距 | `.dashboard-grid` (dark skin) |

### 1.2 卡片尺寸类（基于网格跨度）

| 类名 | 列跨度 | 行跨度 | 当前使用场景 |
|------|--------|--------|-------------|
| `.card-1x1` | 1 | 1 | Queue Mini, DDL Mini, Wiki Recent, KB Stats |
| `.card-1x2` | 1 | 2 | （预留） |
| `.card-2x1` | 2 | 1 | （预留） |
| `.card-2x2` | 2 | 2 | Queue/Progress, Today Focus, Creator, Journal |
| `.card-4x2` | 4 | 2 | Work Activity 热力图 |
| `.card-1x4` | 1 | 4 | （预留） |
| `.card-2x3` | 2 | 3 | （预留） |
| `.card-1x3` | 1 | 3 | （预留） |

**设计师可改项**：
- [ ] 网格列数（当前 8 列是否太多/太少？）
- [ ] 网格间距（当前 12px/14px）
- [ ] 卡片圆角（当前 16px/28px 两种）
- [ ] 是否需要更多尺寸类（如 3×2, 4×4）

### 1.3 其他页面网格

| 页面 | 布局类型 | 列定义 | 间距 |
|------|---------|--------|------|
| Wiki / KB / Journal | 三栏 | `240px 1fr 280px` | `16px` |
| Second Self (Chat) | 三栏 | `260px 1fr 300px` | `16px` |
| DDL / Notifications / Search | 两栏 | `1fr 300px` | `16px` |
| Settings | 两栏 | `260px 1fr` | `16px` |
| Automation | 两栏 | `1fr 1.5fr` | `16px` |
| Workflow | 两栏 | `260px 1fr` | `16px` |
| Creator Hub | 三栏 | `240px 1fr 280px` | `16px` |
| Profile | 顶部 + 3列网格 + 2列 | `repeat(3, 1fr)` / `1fr 1fr` | `12px` / `16px` |
| Skill Market | 3列网格 | `repeat(3, 1fr)` | `12px` |
| Achievement | 4列网格 | `repeat(4, 1fr)` | `10px` |
| 日历 | 7列网格 | `repeat(7, 1fr)` | `8px` |
| 热力图单元格 | 12列网格 | `repeat(12, 1fr)` | `3px` |

**设计师可改项**：
- [ ] 侧边栏宽度（当前 240px / 260px 两种）
- [ ] 右侧 Dock 宽度（当前 280px / 300px 两种）
- [ ] 各页面间距统一为单一值还是保留差异

---

## 二、间距体系 (Spacing Scale)

### 2.1 当前所有间距值（去重后）

当前原型中使用了以下间距值，**未形成统一体系**：

| 值 | 使用场景 | 出现次数 |
|----|---------|---------|
| `1px` | 边框 | 多次 |
| `2px` | 滑块偏移、标签内边距 | 少量 |
| `3px` | 热力图单元格间距、时间线圆角 | 少量 |
| `4px` | 小间距、标签 margin、进度条间距 | 多次 |
| `5px` | 平台进度段间距、状态点阴影 | 少量 |
| `6px` | 导航链接间距、标签间距、Dock 项间距 | 多次 |
| `7px` | Logo 图标发光阴影 | 1 次 |
| `8px` | 通用小间距（最常用） | **非常频繁** |
| `9px` | 导航链接垂直内边距 | 1 次 |
| `10px` | 列表项内边距、标签内边距、Dock 标题间距 | 多次 |
| `12px` | 通用中间距（非常常用） | **非常频繁** |
| `14px` | 导航链接水平内边距、通知项内边距 | 多次 |
| `16px` | 通用大间距（最常用） | **非常频繁** |
| `18px` | 卡片内边距、页面边距 | 多次 |
| `20px` | 卡片内边距、Dock 标题间距 | 多次 |
| `22px` | 页面水平边距 | 2 次 |
| `24px` | 大内边距、统计间距 | 多次 |
| `28px` | 拖拽手柄尺寸 | 1 次 |
| `32px` | 搜索 Hero 内边距、Profile Header 内边距 | 少量 |
| `34px` | 页面外边框圆角 | 1 次 |
| `36px` | 通知图标尺寸 | 1 次 |
| `38px` | Logo 图标尺寸 | 1 次 |
| `40px` | Skill 图标尺寸 | 1 次 |
| `42px` | 搜索框/按钮/头像尺寸 | 多次 |
| `44px` | Toggle Switch 宽度 | 1 次 |
| `80px` | Profile 大头像 | 1 次 |

### 2.2 建议统一为 4px 基网格

当前间距混乱，**建议设计师统一为 4px 基网格**：

| Token | 值 | 使用场景 |
|-------|-----|---------|
| `space-1` | `4px` | 图标间隙、紧凑内边距 |
| `space-2` | `8px` | 列表项间距、小间隙 |
| `space-3` | `12px` | 卡片内部小间距、标签间距 |
| `space-4` | `16px` | 卡片内边距、模块间距（**基准单位**） |
| `space-5` | `20px` | 大卡片内边距 |
| `space-6` | `24px` | 面板内边距、大间距 |
| `space-8` | `32px` | Hero 区域、Header 内边距 |
| `space-10` | `40px` | 大头像、大图标 |

**设计师可改项**：
- [ ] 是否采用 4px 基网格？还是 8px 基网格？
- [ ] 间距层级数量（当前 4/6/8/12/16/20/24/32，建议精简）
- [ ] 页面边距统一值（当前 18/20/22/24 四种）

---

## 三、布局模板 (Layout Templates)

### 3.1 页面边距

| Token | 当前值 | 位置 |
|-------|--------|------|
| `page-margin-top` | `18px` | 导航栏上方 |
| `page-margin-x` | `22px` | 页面左右 |
| `page-margin-bottom` | `22px` | 页面底部 |
| `page-content-padding` | `20px 24px` | 页面内容区 |

### 3.2 导航栏

| Token | 当前值 | 说明 |
|-------|--------|------|
| `nav-height` | `72px` | 导航栏高度（override 后） |
| `nav-height-base` | `56px` | 基础导航栏高度 |
| `nav-margin-top` | `18px` | 距顶部距离 |
| `nav-margin-x` | `22px` | 左右边距 |
| `nav-padding-x` | `18px` | 内部水平内边距 |
| `nav-border-radius` | `26px` | 圆角 |
| `nav-gap` | `6px` | 导航链接间距 |
| `nav-link-padding` | `9px 14px` | 链接内边距 |

### 3.3 卡片内边距

| Token | 当前值 | 使用组件 |
|-------|--------|---------|
| `card-padding-sm` | `12px` | 热力图 2×2 |
| `card-padding` | `16px` | 基础卡片（大量） |
| `card-padding-md` | `18px` | Grid Card（dark skin） |
| `card-padding-lg` | `20px` | Skill Card, Profile Card |
| `card-padding-xl` | `24px` | Main Panel, Flow Canvas |
| `card-padding-2xl` | `32px` | Search Hero, Profile Header |

**设计师可改项**：
- [ ] 卡片内边距统一为几个层级？
- [ ] 是否需要 xs (8px) 或 3xl (40px) 层级？

---

## 四、字体层级 (Typography Scale)

### 4.1 当前所有字体尺寸（去重后）

| 尺寸 | 使用场景 | 字重 | 出现频率 |
|------|---------|------|---------|
| `9px` | 时间线标签、进度条标签、统计标签、状态文字 | 600 | 多次 |
| `10px` | 热力图标签、Dock 标题、统计标签 | 400/600 | 多次 |
| `11px` | 标签文字、描述文字、元信息、成就名 | 400 | **非常频繁** |
| `12px` | 小标题、列表项、Dock 项、日历数字 | 400/500/600 | **非常频繁** |
| `13px` | 正文、导航链接、卡片标题、通知标题 | 400/500/600/700 | **最频繁** |
| `14px` | 搜索结果标题、技能名称、对话标题 | 500/600 | 多次 |
| `15px` | Logo 文字 | 400 | 1 次 |
| `16px` | 搜索输入、模态标题、页面副标题 | 400/600 | 多次 |
| `18px` | 统计数字 | 700 | 少量 |
| `20px` | 页面标题、Profile 统计数字 | 600/700/bold | 多次 |
| `24px` | Profile 卡片数值、搜索 Hero 标题 | 700/bold | 少量 |
| `28px` | 页面大标题 | 750 | 1 次 |
| `32px` | Profile 头像文字 | 400 | 1 次 |

### 4.2 建议字体层级（设计师可调整）

当前字体尺寸过于细碎（9px~32px 共 13 级），建议精简：

| Token | 当前值 | 建议范围 | 使用场景 |
|-------|--------|---------|---------|
| `text-xs` | `11px` | 10-12px | 标签、元信息、辅助文字 |
| `text-sm` | `12px` | 12-13px | 列表项、Dock 内容、描述 |
| `text-base` | `13px` | 13-14px | 正文、导航、卡片标题 |
| `text-lg` | `14px` | 14-16px | 小标题、技能名称 |
| `text-xl` | `16px` | 16-18px | 面板标题、搜索框 |
| `text-2xl` | `20px` | 18-24px | 页面标题、统计数字 |
| `text-3xl` | `24px` | 24-32px | 大数值、Hero 标题 |
| `text-4xl` | `28px` | 28-36px | 页面大标题 |

**字重规范**：

| Token | 值 | 使用场景 |
|-------|-----|---------|
| `font-normal` | `400` | 正文、描述 |
| `font-medium` | `500` | 导航链接 Active、通知标题 |
| `font-semibold` | `600` | 卡片标题、页面标题、按钮 |
| `font-bold` | `700` | 强调文字、统计数字、Primary 按钮 |
| `font-extrabold` | `800` | Logo、Accent 按钮、安装按钮 |

**行高**：

| Token | 当前值 | 使用场景 |
|-------|--------|---------|
| `leading-tight` | `1.5` | 全局默认 |
| `leading-snug` | `1.6` | 消息气泡 |
| `leading-relaxed` | `1.8` | Markdown 正文、Wiki 内容 |

**设计师可改项**：
- [ ] 字体尺寸层级数量（建议 6-8 级）
- [ ] 中文字体栈（当前未指定中文字体）
- [ ] 字重使用规范（当前 400/500/600/700/800 混用）
- [ ] 是否使用 tabular-nums（等宽数字，当前统计数字已用）

---

## 五、颜色 Token (Color Tokens)

### 5.1 当前完整颜色变量

```css
:root {
  --app-bg: #090a08;                    /* 主背景 */
  --app-shell: #121311;                 /* 壳层背景 */
  --surface-1: #1b1d1a;                 /* 一级表面 */
  --surface-2: #242722;                 /* 二级表面 */
  --surface-3: #30342d;                 /* 三级表面 */
  --text-strong: #f5f6ee;               /* 强调文字 */
  --text: #d9dbd0;                      /* 正文 */
  --text-muted: #8f948a;                /* 弱化文字 */
  --line: rgba(245, 246, 238, 0.10);    /* 分割线 */
  --line-strong: rgba(211, 255, 93, 0.38); /* 强调分割线 */
  --accent: #d7ff63;                    /* 主强调色（荧光绿） */
  --accent-2: #8b73ff;                  /* 次强调色（紫） */
  --accent-3: #ff8655;                  /* 第三强调色（橙） */
  --success: #59f86d;                   /* 成功 */
  --warn: #f4e35c;                      /* 警告 */
  --danger: #ff6b6b;                    /* 危险/错误 */
}
```

### 5.2 颜色使用映射表

| Token | 使用场景 | 当前值 | 备注 |
|-------|---------|--------|------|
| `--app-bg` | 页面最底层背景 | `#090a08` | 带径向渐变覆盖 |
| `--app-shell` | 导航栏背景 | `#121311` | 88% 透明度 + blur |
| `--surface-1` | 卡片背景（底层） | `#1b1d1a` | 线性渐变终点 |
| `--surface-2` | 卡片背景（上层）、按钮背景 | `#242722` | 线性渐变起点 |
| `--surface-3` | Hover 状态背景 | `#30342d` | 按钮 Hover |
| `--text-strong` | 标题、重要文字 | `#f5f6ee` | 近白色 |
| `--text` | 正文、列表项 | `#d9dbd0` | 灰白色 |
| `--text-muted` | 辅助文字、标签、时间 | `#8f948a` | 灰绿色 |
| `--line` | 边框、分割线 | `rgba(245,246,238,0.10)` | 10% 白色 |
| `--line-strong` | 强调边框、Hover 边框 | `rgba(211,255,93,0.38)` | 38% 荧光绿 |
| `--accent` | Primary 按钮、Active 状态、高亮 | `#d7ff63` | 荧光绿 |
| `--accent-2` | 次强调、时间线下午段、进度条2 | `#8b73ff` | 紫色 |
| `--accent-3` | 第三强调、时间线晚上段、进度条3 | `#ff8655` | 橙色 |
| `--success` | 完成状态、成功提示 | `#59f86d` | 绿色 |
| `--warn` | 警告、等待中、超期 | `#f4e35c` | 黄色 |
| `--danger` | 错误、失败、危险操作 | `#ff6b6b` | 红色 |

### 5.3 渐变定义

| 渐变 | 定义 | 使用场景 |
|------|------|---------|
| `bg-gradient` | `radial-gradient(circle at 12% 0%, rgba(215,255,99,0.13), transparent 30%), radial-gradient(circle at 82% 14%, rgba(139,115,255,0.13), transparent 28%)` | 页面背景装饰 |
| `card-gradient` | `radial-gradient(circle at 0% 0%, rgba(255,255,255,0.055), transparent 34%), linear-gradient(145deg, var(--surface-2), var(--surface-1))` | 普通卡片背景 |
| `card-gradient-dark` | `radial-gradient(circle at 7% 12%, rgba(215,255,99,0.27), transparent 28%), linear-gradient(145deg, #20231e, #11130f)` | Queue 卡片 |
| `card-gradient-focus` | `radial-gradient(circle at 85% 20%, rgba(139,115,255,0.20), transparent 34%), linear-gradient(145deg, #242721, #141611)` | Focus 卡片 |
| `card-gradient-heatmap` | `radial-gradient(circle at 90% 12%, rgba(139,115,255,0.16), transparent 36%), linear-gradient(145deg, #262923, #151712)` | 热力图卡片 |
| `modal-gradient` | `radial-gradient(circle at 0 0, rgba(215,255,99,0.14), transparent 34%)` | 弹窗背景 |

**设计师可改项**：
- [ ] 品牌主色（当前荧光绿 `#d7ff63`，非常激进）
- [ ] 是否需要 Light Mode 颜色集？
- [ ] 表面色层级数量（当前 3 级是否足够？）
- [ ] 渐变装饰是否保留？（当前有 5 种卡片渐变）
- [ ] 颜色对比度是否符合 WCAG AA/AAA？

---

## 六、圆角体系 (Border Radius)

### 6.1 当前所有圆角值

| Token | 当前值 | 使用场景 | 出现频率 |
|-------|--------|---------|---------|
| `radius-sm` | `2px` | 搜索高亮、小标签 | 少量 |
| `radius-md` | `3px` | 时间线标签、时间线 | 少量 |
| `radius-base` | `4px` | 拖拽手柄、列表项、小元素 | 多次 |
| `radius-lg` | `6px` | 按钮、标签、日历日、Dock 项 | **非常频繁** |
| `radius-xl` | `8px` | 卡片 Tab、历史项、输入框、通知项 | **非常频繁** |
| `radius-2xl` | `10px` | Skill 图标、流程节点 | 少量 |
| `radius-3xl` | `12px` | 侧边栏、面板、消息气泡、下拉菜单 | **非常频繁** |
| `radius-4xl` | `15px` | Logo 图标 | 1 次 |
| `radius-5xl` | `16px` | 基础卡片、搜索 Hero、日历、模态框 | 多次 |
| `radius-6xl` | `18px` | 统计框 | 1 次 |
| `radius-7xl` | `20px` | 搜索筛选标签 | 1 次 |
| `radius-8xl` | `26px` | 导航栏 | 1 次 |
| `radius-card` | `28px` | 卡片（dark skin）、模态框 | **频繁** |
| `radius-page` | `34px` | 页面外边框 | 1 次 |
| `radius-full` | `999px` | 按钮、标签、输入框、开关、头像、进度条 | **非常频繁** |

### 6.2 建议精简为 5 级

当前圆角过于细碎（15 个不同值），建议精简：

| Token | 建议值 | 使用场景 |
|-------|--------|---------|
| `radius-none` | `0` | 表格、代码块 |
| `radius-sm` | `4px` | 小元素、标签、内部容器 |
| `radius-md` | `8px` | 按钮、输入框、列表项 |
| `radius-lg` | `12px` | 卡片、面板、弹窗 |
| `radius-xl` | `16px` | 大卡片、Hero 区域 |
| `radius-2xl` | `24px` | 导航栏、特殊容器 |
| `radius-full` | `9999px` | Pill 按钮、头像、开关 |

**设计师可改项**：
- [ ] 圆角层级数量（建议 5-7 级）
- [ ] 卡片圆角统一值（当前 12px/16px/28px 三种）
- [ ] 是否使用"全圆角"（999px）风格？还是统一为固定值？

---

## 七、阴影体系 (Shadow System)

### 7.1 当前所有阴影定义

| Token | 当前值 | 使用场景 |
|-------|--------|---------|
| `shadow-card` | `0 18px 50px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.04)` | 卡片默认阴影 |
| `shadow-card-hover` | `0 24px 70px rgba(0,0,0,0.44), inset 0 1px 0 rgba(255,255,255,0.06)` | 卡片 Hover 阴影 |
| `shadow-modal` | `0 40px 120px rgba(0,0,0,0.58)` | 模态框阴影 |
| `shadow-dropdown` | `0 4px 16px rgba(0,0,0,0.1)` | 下拉菜单阴影 |
| `shadow-skill` | `0 4px 12px rgba(0,0,0,0.08)` | Skill 卡片 Hover |
| `shadow-logo` | `0 0 0 7px rgba(215,255,99,0.10)` | Logo 发光 |
| `shadow-dot` | `0 0 0 5px rgba(255,255,255,0.04)` | 状态点发光 |

### 7.2 阴影参数拆解

| 参数 | 当前值 | 说明 |
|------|--------|------|
| 卡片阴影 X 偏移 | `0` | 垂直向下投影 |
| 卡片阴影 Y 偏移 | `18px` → `24px` (hover) | Hover 时加深 |
| 卡片阴影模糊 | `50px` → `70px` (hover) | Hover 时扩散 |
| 卡片阴影透明度 | `0.34` → `0.44` (hover) | Hover 时加深 |
| 内发光 | `inset 0 1px 0 rgba(255,255,255,0.04)` | 顶部 1px 高光 |
| 模态框 Y 偏移 | `40px` | 更大，营造悬浮感 |
| 模态框模糊 | `120px` | 极大模糊，聚焦注意力 |

**设计师可改项**：
- [ ] 阴影层级数量（建议 3-4 级：resting / hover / modal / dropdown）
- [ ] 是否保留内发光（inset highlight）？
- [ ] 阴影颜色（当前纯黑，是否带品牌色？）
- [ ] 是否使用彩色阴影（如 accent 色发光）？

---

## 八、组件尺寸规范 (Component Sizing)

### 8.1 导航栏组件

| 组件 | 宽度 | 高度 | 圆角 | 备注 |
|------|------|------|------|------|
| 导航栏 | `100% - 44px` | `72px` | `26px` | margin 18px 22px 0 |
| Logo 图标 | `38px` | `38px` | `15px` | 带 7px 发光阴影 |
| Logo 文字 | - | - | - | `15px`, weight 800 |
| 导航链接 | auto | auto | `999px` | padding `9px 14px` |
| 搜索框 | `268px` | `42px` | `999px` | - |
| 操作按钮 | `42px` | `42px` | `50%` | - |
| 头像 | `42px` | `42px` | `50%` | 背景 accent |

### 8.2 卡片组件

| 组件 | 内边距 | 圆角 | 阴影 | 备注 |
|------|--------|------|------|------|
| Grid Card | `18px` | `28px` | `shadow-card` | 可拖拽 |
| Sidebar | `16px` | `12px` | `shadow-card` | - |
| Main Panel | `24px` | `12px` | `shadow-card` | - |
| Dock Panel | `16px` | `12px` | `shadow-card` | - |
| Skill Card | `20px` | `12px` | `shadow-skill` (hover) | - |
| Profile Card | `20px` | `12px` | `shadow-card` | - |
| Search Result | `16px` | `12px` | - | border 2px |
| Notification | `14px 16px` | `12px` | - | border 2px |

### 8.3 按钮组件

| 类型 | 内边距 | 圆角 | 背景 | 文字 |
|------|--------|------|------|------|
| Primary | `8px 16px` | `999px` | `accent` | `#10120d`, weight 800 |
| Secondary | `8px 16px` | `8px` | `surface-2` | `text` |
| Ghost | `6px 16px` | `8px` | transparent | `text` |
| Icon Button | `0` | `50%` | `surface-2` | - |
| Toggle Switch | `44px × 24px` | `12px` | `surface` | 滑块 `20px` |

### 8.4 输入框组件

| 类型 | 宽度 | 高度 | 内边距 | 圆角 | 背景 |
|------|------|------|--------|------|------|
| 搜索框 | `268px` | `42px` | `0 12px` | `999px` | `rgba(255,255,255,0.07)` |
| 聊天输入 | `100%` | auto | `10px 14px` | `999px` | `rgba(255,255,255,0.07)` |
| 大搜索 | `100%` | auto | `14px 20px` | `12px` | `surface` |

### 8.5 列表项组件

| 类型 | 内边距 | 圆角 | 备注 |
|------|--------|------|------|
| Sidebar Item | `8px 10px` | `6px` | margin-bottom 2px |
| List Item | `9px 0` | - | border-bottom 1px |
| Dock Item | `8px` | `6px` | margin-bottom 6px |
| Chat History | `10px` | `8px` | margin-bottom 4px |
| Settings Row | `12px 0` | - | border-bottom 1px |

### 8.6 标签/Chip 组件

| 类型 | 内边距 | 圆角 | 背景 | 文字 |
|------|--------|------|------|------|
| Tag Chip | `4px 10px` | `12px` | `rgba(255,255,255,0.07)` | `text` |
| Filter Chip | `6px 14px` | `20px` | `rgba(255,255,255,0.07)` | `text` |
| Active Chip | `6px 14px` | `20px` | `accent` | `#10120d` |
| Card Tab | `4px 6px` | `4px` | `surface` | `text` |
| Active Tab | `4px 6px` | `4px` | `accent` | `#10120d` |

### 8.7 图标尺寸

| 类型 | 尺寸 | 圆角 | 背景 | 备注 |
|------|------|------|------|------|
| Card Icon | `20px` | `4px` | `ddd` | - |
| Skill Icon | `40px` | `10px` | `surface` | 文字 18px |
| Chat Avatar | `32px` | `50%` | accent/surface | 文字 14px |
| Profile Avatar | `80px` | `50%` | accent | 文字 32px |
| Nav Avatar | `42px` | `50%` | accent | 文字 14px |
| Notif Icon | `36px` | `8px` | `surface` | 文字 16px |
| Drag Handle | `28px` | `50%` | `surface` | 文字 12px |
| Achievement Icon | `24px` | - | - | 纯文字/emoji |

### 8.8 进度/状态组件

| 组件 | 尺寸 | 圆角 | 颜色 |
|------|------|------|------|
| Platform Segment | `30px × 8px` | `999px` | 空/填充 |
| Timeline Track | `100% × 10px` | `999px` | `rgba(255,255,255,0.08)` |
| Progress Bar | `flex × 26px` | `999px` | accent/accent-2/accent-3/success/warn |
| Item Dot | `8px × 8px` | `50%` | 绿/黄/红/灰 |
| Task Status | `16px × 16px` | `50%` | 绿/灰/红 |
| Heatmap Cell | auto | `8px` | 空/浅/中/深 |

**设计师可改项**：
- [ ] 按钮尺寸统一（当前内边距不统一：8px 16px / 6px 16px / 10px 20px）
- [ ] 输入框高度统一（当前 36px/42px/auto 三种）
- [ ] 图标尺寸体系（当前 20/32/36/40/42/80px，建议 4 级：sm/md/lg/xl）
- [ ] 进度条高度统一（当前 4px/8px/10px/20px/26px）

---

## 九、边框规范 (Border System)

### 9.1 边框宽度

| Token | 值 | 使用场景 |
|-------|-----|---------|
| `border-none` | `0` | 无边框元素 |
| `border-thin` | `1px` | 卡片边框、分割线、Hover 边框 |
| `border-base` | `2px` | 基础组件边框（旧版，大量存在） |

### 9.2 边框颜色

| Token | 值 | 使用场景 |
|-------|-----|---------|
| `border-line` | `var(--line)` | 默认分割线/边框 |
| `border-line-strong` | `var(--line-strong)` | 强调边框、Hover 边框 |
| `border-accent` | `rgba(215,255,99,0.34)` | 卡片 Hover 边框 |
| `border-transparent` | `transparent` | 导航链接默认边框 |

### 9.3 边框样式

| 样式 | 使用场景 |
|------|---------|
| `solid` | 所有组件边框 |
| `dashed` | 网格背景单元格 |

**设计师可改项**：
- [ ] 是否统一为 1px 边框？（当前 1px 和 2px 混用）
- [ ] 分割线是否使用背景色代替边框？

---

## 十、动效规范 (Motion Tokens)

### 10.1 过渡时长

| Token | 当前值 | 使用场景 | 出现频率 |
|-------|--------|---------|---------|
| `duration-fast` | `0.15s` | Skill 卡片 Hover | 1 次 |
| `duration-base` | `0.18s` | 卡片 Hover、按钮、导航链接 | **非常频繁** |
| `duration-normal` | `0.2s` | 拖拽手柄、导航链接（旧版）、开关 | 多次 |

### 10.2 缓动函数

| Token | 当前值 | 使用场景 |
|-------|--------|---------|
| `ease-default` | `ease` | 大多数过渡 |
| `ease-out` | `ease-out` | 按钮按下动画 |

### 10.3 变换效果

| 效果 | 值 | 触发条件 |
|------|-----|---------|
| `hover-lift` | `translateY(-3px)` | 卡片 Hover |
| `hover-lift-sm` | `translateY(-2px)` | 基础卡片 Hover |
| `hover-lift-xs` | `translateY(-1px)` | 按钮 Hover |
| `press-scale` | `translateY(1px) scale(0.98)` | 按钮按下 |
| `drag-scale` | `scale(0.985)` | 卡片拖拽中 |
| `drag-opacity` | `opacity: 0.66` | 卡片拖拽中 |

### 10.4 建议动效体系

当前动效过于简单，建议设计师定义完整动效系统：

| Token | 建议值 | 使用场景 |
|-------|--------|---------|
| `duration-instant` | `0ms` | 无动画 |
| `duration-fast` | `150ms` | 微交互（按钮、开关） |
| `duration-base` | `200ms` | 标准过渡（Hover、颜色变化） |
| `duration-slow` | `300ms` | 页面切换、弹窗 |
| `duration-slower` | `500ms` | 复杂动画（拖拽、展开） |
| `ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | 标准缓动 |
| `ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | 退出动画 |
| `ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | 进入动画 |
| `ease-bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 弹性效果 |

**设计师可改项**：
- [ ] 过渡时长统一（当前 0.15s/0.18s/0.2s 混用）
- [ ] 是否使用更丰富的缓动曲线？
- [ ] 是否需要页面切换动画？（当前瞬间切换）
- [ ] 是否需要 Skeleton Loading 动画？
- [ ] 是否需要 Toast 通知的进入/退出动画？

---

## 十一、Z-index 层级 (Elevation)

| 层级 | 当前值 | 使用场景 |
|------|--------|---------|
| `z-base` | `0` | 网格背景、页面底层 |
| `z-content` | `1` | 页面内容、卡片 |
| `z-sticky` | `10` | 粘性定位元素 |
| `z-dropdown` | `100` | 下拉菜单 |
| `z-drawer` | `200` | 抽屉面板 |
| `z-modal` | `1000` | 模态框遮罩 |
| `z-toast` | `2000` | Toast 通知 |
| `z-tooltip` | `3000` | 工具提示 |

**当前实际使用的值**：
- `0`：网格背景、body::before 装饰边框
- `1`：页面内容
- `100`：拖拽中的卡片
- `1000`：下拉菜单
- `2000`：模态框遮罩

**设计师可改项**：
- [ ] 层级数量是否足够？
- [ ] 是否需要添加 Toast/Tooltip 层级？

---

## 十二、响应式断点 (Breakpoints)

### 12.1 当前断点

当前原型**只有一个断点**：

| 断点 | 当前值 | 变化 |
|------|--------|------|
| `desktop` | `> 1180px` | 完整布局 |
| `tablet` | `≤ 1180px` | 隐藏搜索框、缩小导航链接内边距、缩小导航栏间距 |

### 12.2 建议完整断点体系

| Token | 建议值 | 布局变化 |
|-------|--------|---------|
| `xs` | `< 640px` | 移动端：单栏、底部导航、卡片堆叠 |
| `sm` | `640px - 768px` | 小平板：单栏/两栏、简化导航 |
| `md` | `768px - 1024px` | 平板：两栏、侧边栏可折叠 |
| `lg` | `1024px - 1280px` | 小桌面：三栏变两栏 |
| `xl` | `1280px - 1536px` | 标准桌面：完整三栏 |
| `2xl` | `> 1536px` | 大桌面：更宽间距、更大字体 |

**设计师可改项**：
- [ ] 断点数量和值
- [ ] 每个断点下的布局变化（当前未定义）
- [ ] 移动端导航方式（底部 Tab？汉堡菜单？）
- [ ] 卡片在移动端如何排列（当前 8×4 网格完全不适用移动端）

---

## 十三、设计师修改指南

### 如何修改这份文档

1. **直接修改 Token 值**：在上方表格中找到要改的 Token，修改"当前值"列
2. **添加新 Token**：在对应章节新增一行
3. **删除 Token**：标记为 `[已删除]` 并说明替代方案
4. **标注优先级**：用 `[P0]`/`[P1]`/`[P2]` 标注修改优先级

### 修改后如何同步给开发

修改完成后，开发需要：
1. 更新 CSS Variables（`:root` 中的值）
2. 更新组件样式（如果组件尺寸变化）
3. 检查响应式断点（如果布局变化）
4. 验证无障碍对比度（如果颜色变化）

### 关键决策清单（建议设计师先确定这些）

| # | 决策项 | 当前状态 | 建议决策期限 |
|---|--------|---------|------------|
| 1 | 品牌主色 | 荧光绿 `#d7ff63` | Phase 1 |
| 2 | 是否支持 Light Mode | 仅 Dark | Phase 1 |
| 3 | 间距基单位 | 混乱（4/6/8/12/16...） | Phase 1 |
| 4 | 字体层级数量 | 13 级（过细） | Phase 1 |
| 5 | 圆角风格 | 混合（固定+全圆角） | Phase 1 |
| 6 | 阴影层级 | 6 级 | Phase 1 |
| 7 | 移动端布局 | 未定义 | Phase 2 |
| 8 | 动效丰富度 | 极简 | Phase 3 |
| 9 | 图标方案 | Emoji + CSS | Phase 1 |
| 10 | 中文字体 | 未指定 | Phase 1 |

---

## 附录：原始 CSS 变量汇总（开发直接可用）

```css
:root {
  /* 颜色 */
  --app-bg: #090a08;
  --app-shell: #121311;
  --surface-1: #1b1d1a;
  --surface-2: #242722;
  --surface-3: #30342d;
  --text-strong: #f5f6ee;
  --text: #d9dbd0;
  --text-muted: #8f948a;
  --line: rgba(245, 246, 238, 0.10);
  --line-strong: rgba(211, 255, 93, 0.38);
  --accent: #d7ff63;
  --accent-2: #8b73ff;
  --accent-3: #ff8655;
  --success: #59f86d;
  --warn: #f4e35c;
  --danger: #ff6b6b;
  
  /* 圆角 */
  --radius-card: 28px;
  --radius-control: 999px;
  
  /* 阴影 */
  --shadow-card: 0 18px 50px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.04);
  
  /* 布局 */
  --nav-height: 72px;
  --page-margin: 22px;
  --grid-gap: 14px;
  --sidebar-width: 240px;
  --dock-width: 280px;
}
```

---

*文档版本：v2.0 — 底层 Token 版*
*生成日期：2026-06-07*
*基于原型：`study-hub-dashboard-style-refresh.html`*
