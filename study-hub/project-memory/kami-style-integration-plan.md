# Kami 样式集成方案

## 需求理解

将 `tw93/kami` 的暖色纸质感文档排版设计系统引入 study-hub 项目，使所有 Markdown 渲染区域呈现 Kami 风格：
- 暖色羊皮纸画布 `#f5f4ed`
- 藏青色强调色 `#1B365D`
- 衬线字体（中文仓耳今楷 / 英文 Charter）
- 编辑式排版节奏与间距

## 现状分析

| 维度 | 当前状态 |
|------|----------|
| Markdown 渲染器 | `MarkdownRenderer.vue`（marked 解析） |
| 样式位置 | `frontend/src/assets/main.css` 中 `.markdown-content` |
| 当前风格 | 暗色主题（`#0f0f14` 背景 + `#7c8aff` 强调色） |
| 使用范围 | Wiki、知识库、头脑风暴、学习计划、首页等页面 |
| 基础框架 | Vue 3 + Vite + Tailwind CSS |

> 注：当前 `.markdown-content` 注释已标明 "Kami-inspired"，但色彩已完全适配为暗色主题。

## 方案选项

### 方案 A：全局主题切换（推荐）

将整个应用从暗色主题全面迁移到 Kami 暖色主题。

**改动范围：**
- `main.css` body 背景色 `#0f0f14` → `#f5f4ed`
- `main.css` body 文字色 `#e0e0e8` → `#141413`
- `.markdown-content` 完全替换为 Kami 约束系统样式
- 导航栏、侧边栏、卡片等全局组件适配暖色调

**优点：**
- 视觉统一，不会出现暗色外壳 + 暖色内容的不协调
- 完全还原 Kami 设计哲学 "Documents should read as composed pages"
- 一次到位，后续无需维护两套配色

**缺点：**
- 改动面大，需要检查所有 Vue 组件的硬编码颜色
- 需要引入中文字体文件（仓耳今楷 3.3MB）

---

### 方案 B：Markdown 区域独立暖色（纸面模式）

保持应用外壳暗色主题不变，仅 `.markdown-content` 内部渲染为 Kami 暖色风格，形成"深色桌面 + 一张纸"的视觉效果。

**改动范围：**
- 仅修改 `.markdown-content` 选择器下的样式
- 给 `.markdown-content` 容器添加暖色背景、圆角、阴影，模拟纸张
- 字体、间距、标题样式全部切为 Kami 规范

**优点：**
- 改动范围极小，风险低
- 视觉上形成强烈对比，Markdown 内容更突出
- 无需改动导航/侧边栏等大量组件

**缺点：**
- 暗色外壳 + 暖色内容可能造成视觉割裂
- 页面滚动时暖色块在暗色背景上跳动感明显

---

### 方案 C：双主题切换系统

保留当前暗色主题，同时实现一套 Kami 暖色主题，支持用户一键切换或自动跟随系统偏好。

**改动范围：**
- 将所有硬编码颜色提取为 CSS 变量
- 定义 `:root[data-theme="dark"]` 和 `:root[data-theme="kami"]` 两套变量
- `.markdown-content` 样式参数化，跟随主题变量
- 添加主题切换按钮（存入 localStorage）

**优点：**
- 用户选择权，满足不同场景偏好
- 扩展性好，后续可继续添加更多主题
- 不改当前暗色主题，零回归风险

**缺点：**
- 实现复杂度最高
- 需要全面梳理并变量化所有颜色
- 维护两套视觉系统长期成本较高

---

## 关键决策点（请确认）

1. **主题范围**
   - A. 全局切换为 Kami 暖色（推荐，最协调）
   - B. 仅 Markdown 内容区切换为暖色（快速实现）
   - C. 双主题系统（最灵活，成本最高）

2. **字体引入方式**
   - A. 引入仓耳今楷字体文件（体积 +3MB，效果最还原）
   - B. 使用系统衬线字体回退（`Source Han Serif SC` / `Noto Serif CJK SC`，零体积）
   - C. 通过 CDN 按需加载（`@chinese-fonts/tcjz` 等 npm 包）

3. **适用范围**
   - A. 所有使用 `MarkdownRenderer.vue` 的页面（Wiki、知识库、头脑风暴、学习计划、首页）
   - B. 仅 Wiki 和知识库等阅读场景，头脑风暴等保留原样

## 推荐实施路径（如选方案 A）

```
Step 1: 准备字体
  └── 安装 @chinese-fonts/tscjz 或配置 CDN 引入仓耳今楷

Step 2: 重构 CSS 变量系统
  └── 在 main.css 顶部定义 Kami 色彩变量
  └── 替换 body / 全局背景色和文字色

Step 3: 重写 .markdown-content
  └── 完全替换为 Kami 约束系统（色彩、字体、间距、标题、代码块、引用、表格、链接）

Step 4: 适配非 Markdown 组件
  └── 导航栏、卡片、按钮、侧边栏、输入框等适配暖色调
  └── 将硬编码暗色值替换为 CSS 变量

Step 5: 验证
  └── 逐个页面检查渲染效果
  └── 确认 WikiLink、任务列表、代码块等自定义功能正常
```

## 参考文件

- Kami 设计规范：`https://github.com/tw93/kami/blob/main/design.md`
- Kami 核心样式：`https://github.com/tw93/kami/blob/main/styles.css`
- 当前 Markdown 样式：`study-hub/frontend/src/assets/main.css`
