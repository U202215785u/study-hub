# Round 01 · 主题域调研：CSS 前沿渲染（零依赖 / 纯 CSS 首页炫酷化）

> 目标项目：Study-Hub（Vue 3.5 + Vite 5 + Tailwind 3.4 + ECharts + Storybook 8.6，首页为 Bento 网格仪表盘，含热力图/日历/任务等 widget）
> 调研日期：2026-08（浏览器支持均经 caniuse.com 联网验证；Electron 版本经 releases.electronjs.org 联网验证；案例 URL 已验证/已标注）
> 结论诉求：每个候选技术落到「首页 Bento 仪表盘怎么用」（背景层 / widget 层 / 交互层 / 入场动效）

---

## 0. 关键前提：本项目运行环境 = Electron 28 = Chromium 120

已联网验证 `study-hub/electron/package.json` 声明 `electron: ^28.0.0`，而 Electron 28.0.0 官方 release 页（https://releases.electronjs.org/release/v28.0.0）确认其内置 **Chromium 120.0.6099.56**。这决定了「Electron 内可用」的下限：

| 特性 | Chromium 120 内 | 2026 最新浏览器（Chrome 151 / Safari 26.4 / FF 153） |
|---|---|---|
| backdrop-filter | ✅（76+） | ✅ |
| Container Queries | ✅（106+） | ✅ |
| subgrid | ✅（117+） | ✅ |
| color-mix() | ✅（111+） | ✅ |
| :has() | ✅（105+） | ✅ |
| CSS Nesting（原生） | ✅（120 起默认） | ✅ |
| mask 简写 | ✅（120 起完整支持） | ✅ |
| clip-path（HTML） | ✅（55+，部分） | ✅ |
| mix-blend-mode | ✅（41+） | ✅ |
| View Transitions（同文档） | ✅（111+） | ✅ |
| scroll-driven animations（scroll()/view()） | ✅（115+） | ✅（Safari 26+，FF 需 flag） |
| @starting-style / transition-behavior: allow-discrete | ✅（117+） | ✅ |
| text-wrap: balance | ✅（114+） | ✅ |
| @property（注册自定义属性） | ✅（85+） | ✅ |
| **light-dark()** | ❌（需 123+） | ✅ |
| **CSS anchor positioning** | ❌（需 125+） | ✅ |
| **CSS if()** | ❌（需 137+） | Chrome 137+，Safari/FF 未支持 |
| **View Transitions（跨文档）** | ❌（需 126+） | Chrome 126+ / Safari 18.2+ |

**结论**：除 light-dark()、anchor、if()、跨文档 VT 外，本报告所有候选在 Electron 28 桌面端**全部可用**——CSS 前沿特性选型不受 Electron 版本拖累，这本身就是纯 CSS 路线相对 WebGL 路线的巨大优势。

**项目现状摸底**（grep 全 src 已验证）：项目**已经**在原生使用 `color-mix(in srgb, var(--...) x%, transparent)`（UiTag / UiButton / UiAppShell / NavBar 等 8 处）、`backdrop-filter: blur(16px)`（UiAppShell topbar）、`--ui-*` CSS 变量体系 + `@media (prefers-reduced-motion: reduce)` 归零动效时长（tokens.css）。→ 说明「纯 CSS 炫酷化」与现有设计系统**完全同轨**，落地无阻力。

---

## 1. 候选技术详情

### 1.1 backdrop-filter 玻璃拟态（Glassmorphism）—— widget 层头号方案 ⭐⭐⭐⭐⭐
- **类别**：widget 层 / 质感
- **参考**：caniuse https://caniuse.com/css-backdrop-filter（全局 94.63%，Chrome 76+，Electron 28 ✅）
- **社区热度**：Glassmorphism 在 2020–2021 爆发后已沉淀为 **2024–2026 仪表盘/桌面级应用的默认质感**（Linear、Notion、Apple 系统 UI 的行业通行做法）；Awwwards 设有专门筛选分类（https://www.awwwards.com/websites/glassmorphism/ 已抓取，含 Decimal Chain 获奖案例）。
- **代表性案例**：
  - https://decimalchain.com（Awwwards「Glassmorphism」筛选在列案例，已验证）
  - https://www.awwwards.com/websites/glassmorphism/（案例集合页，已验证）
  - 项目自身 UiAppShell topbar 已在用（内部先例）
- **Vue 3 + Tailwind 写法**：Tailwind 3.4 原生有 `backdrop-blur-*`、`bg-white/5`、`border-white/10` 工具类，卡片直接：
  ```
  class="rounded-[22px] border border-white/10 bg-white/[0.06] backdrop-blur-xl shadow-[0_18px_34px_-8px_rgb(0_0_0/0.22)]"
  ```
  需要自定义的只有「hover 玻璃加深」，用 `hover:bg-white/[0.09]` 即可；若想给整个 Bento 容器做玻璃，则 `@layer` 里给 `.home-dashboard-grid` 加一行 `backdrop-filter`。
- **性能**：`backdrop-filter` 会为该元素创建合成层；**全屏大区域玻璃 + 常驻动画是开销重灾区**，但 widget 卡片（几百 px）通常没问题；关键纪律 = 玻璃层只用于静态/低更新区域，避免玻璃层本身做高频 transform 动画。
- **可访问性/降级**：不支持或 `prefers-reduced-transparency` 时退化为纯半透明（`background: color-mix(...)` 兜底，天然存在）；玻璃下面内容对比度要用 `color-mix` 提暗衬底；焦点环 `--ui-focus-ring` 不受影响。
- **评级 ★★★★★**：与现有设计系统零摩擦、Electron 100% 支持、一上手 Bento 卡片立刻「高级」。

### 1.2 conic/radial 渐变 + SVG feTurbulence 噪点/网格纹理 —— 背景层最优解 ⭐⭐⭐⭐⭐
- **类别**：背景层（纯装饰，零 DOM）
- **参考**：MDN feTurbulence（https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feTurbulence，未联网验证，知名文档）；noise-grain 用法为 2022–2024「Grainy Gradient」社区潮流（Dribbble/CodePen 大量 "noise texture" 资产）
- **浏览器支持**：`background-image` + data-URI SVG 滤镜为全平台基础能力，**Electron 28 与全部现代浏览器 100%**（无任何门槛）。
- **社区热度**：这是目前顶级站点（尤其 3D/暗色仪表盘站）**去除渐变 banding（色带）的事实标准**——在渐变上叠一层 3–8% 不透明度的 SVG 噪点，质感立刻从"扁平渐变"变"磨砂布面"；Conic 色环 + 极坐标扫描网格在 2024–2026 数据后台很流行。
- **代表性案例**：Awwwards 获奖站点的背景层几乎全部有噪点（如 decimalchain.com 的背景，已验证）；CodePen 上 "noise texture css" 为常青搜索（未联网验证具体 pen URL）。
- **Vue 3 + Tailwind 写法**：两个内置背景工具类即可，或 `@layer utilities` 注册：
  ```
  .bg-noise { background-image: url("data:image/svg+xml,...feTurbulence baseFrequency='0.8' numOctaves='2'..."); }
  .bg-aurora { background: conic-gradient(from 180deg at 50% -20%, #8b73ff33, #d7ff631a, transparent 60%), radial-gradient(120% 90% at 20% 10%, #6cb8ff22, transparent 50%); }
  ```
  注意：`conic-gradient` 完全受 CSS 变量驱动，可直接引用 `--ui-color-*`。
- **性能**：`feTurbulence` 经 SVG data-URI 作为背景图**一次性栅格化**，运行时零 CPU/GPU 成本；比任何 JS 粒子背景都便宜一个量级。若做 `background-position` 缓慢漂移动画，GPU 合成即可。
- **可访问性**：纯装饰层放 `Home.vue` 根下 `position:fixed; z-index:-1; pointer-events:none; aria-hidden`（参考 WebGL 域同款降级约定）；注意噪点叠加在纯色背景上可能被色域压缩，控制在 3–6% 透明度内。
- **评级 ★★★★★**：零依赖、零门槛、全兼容，是「纯 CSS 背景炫酷」的性价比之王。

### 1.3 clip-path / mask 异形卡片 —— Bento 卡片个性化 ⭐⭐⭐⭐
- **类别**：widget 层 / 形状
- **参考**：caniuse clip-path https://caniuse.com/css-clip-path（全局 96.71%，Electron 28 ✅）、caniuse mask https://caniuse.com/css-masks（Chrome 120 起完整支持 mask 简写，Electron 28 恰好达标）
- **社区热度**：CSS-Tricks/CodePen 上 clip-path 多边形卡片与斜切 header 是 2023–2025 高频技法（caniuse 页面引用的示例 pen：https://codepen.io/dubrod/details/myNNyW/）；mask 淡出（linear-gradient 掩膜）用于「内容溢出卡片边缘渐变消失」在 dashboard 很常见。
- **代表性案例**：
  - https://codepen.io/dubrod/details/myNNyW/（clip-path polygon 剪裁图例，caniuse 官方引用）
  - Awwwards 上大量斜切/圆角异形面板（未联网验证具体站，作为已知趋势）
- **Vue 3 + Tailwind 写法**：Tailwind arbitrary 值直接可用：
  ```
  class="[clip-path:polygon(0_0,100%_0,100%_calc(100%-18px),calc(100%-18px)_100%,0_100%)]"
  ```
  或 `@layer components` 注册 `.ui-widget--bevel`；mask 用 `[mask-image:linear-gradient(...)]`（Chrome 120 后可无前缀）。
- **性能**：clip-path/mask 均为合成时一次性计算，动画 clip-path 属可合成属性（GPU 友好）；注意**clip-path 会打断 border-radius**（二者互斥），设计时要么全剪要么全圆角。
- **可访问性/降级**：剪裁只影响视觉，阅读顺序/焦点不受影响；但剪掉的区域不可见，务必保证内容在可见多边形内 + `focus-visible` 外环仍清晰；降级 = 不加剪裁即方形卡片，无功能损失。
- **评级 ★★★★**：给 2–3 个重点 widget（创建入口、任务卡）做「切角/斜切」差异化最划算，全卡统一用则腻。

### 1.4 mix-blend-mode 混合 —— 背景与前景的光影融合 ⭐⭐⭐⭐
- **类别**：背景层 / 交互层
- **参考**：caniuse https://caniuse.com/css-mixblendmode（全局 96%+，Chrome 41+，Electron 28 ✅）
- **社区热度**：Screen/Overlay/Soft-Light 混合是「霓虹光斑背景 + 浅色文字」站点的标配；`mix-blend-mode: screen` 让渐变光斑在任意色相背景上都「发光」而不盖字，2024–2026 暗色仪表盘/落地页高频出现。
- **代表性案例**：Awwwards 暗色霓虹站点普遍使用（如 decimalchain.com 的背景光晕，已验证）；CodePen "mix-blend-mode gradient glow" 为常青主题（未联网验证具体 pen）。
- **Vue 3 + Tailwind 写法**：`mix-blend-screen`、`mix-blend-overlay` 是 Tailwind 内置类；背景光斑：
  ```
  <div class="pointer-events-none fixed inset-0 -z-10">
    <div class="absolute -top-40 left-1/4 h-[500px] w-[500px] rounded-full bg-[#d7ff63]/20 mix-blend-screen blur-[120px]" />
  </div>
  ```
- **性能/注意事项**：混合模式会在元素上创建合成层；**大尺寸（全屏）blur + blend 区域是 GPU 开销点**——用静态光斑（无动画）或降低 opacity 缓解；需要 `isolation: isolate` 隔离避免把整个应用都混进去。
- **可访问性**：blend 只作用于装饰层，文字层无需依赖 blend 即可读；降级 = 关闭 blend 仍是有色光斑。
- **评级 ★★★★**：与 1.2 组合成「噪点 + 霓虹光斑」的暗色背景双件套，简单且惊艳。

### 1.5 文字效果：渐变 / 描边 / 立体（background-clip:text + -webkit-text-stroke + text-shadow）⭐⭐⭐⭐
- **类别**：widget 层 / 品牌字
- **参考**：MDN background-clip:text（https://developer.mozilla.org/en-US/docs/Web/CSS/background-clip，未联网验证，极成熟特性）；-webkit-text-stroke 全 Chromium 支持（Electron 28 ✅）
- **社区热度**：渐变大字 + 描边标题是 2024–2026 Awwwards 排版站（尤其暗色主题）的标识性元素；「把 GreetingBar 的大号问候语做成渐变发光字」是首页最便宜的视觉升级。
- **代表性案例**：Awwwards 排版向获奖站普遍（未联网验证具体 URL，作为已知趋势）；Chrome DevRel 的 CSS 示例与 CodePen 大量 "gradient text" pen（未联网验证）。
- **Vue 3 + Tailwind 写法**：Tailwind 无内置 `bg-clip-text` 需要任选：
  ```
  class="bg-gradient-to-r from-[--ui-color-action] via-[--ui-color-info] to-[--ui-color-content-purple] bg-clip-text text-transparent"
  ```
  描边用 arbitrary：`[-webkit-text-stroke:1px_var(--ui-color-action)]`；立体用现有 `--ui-shadow-*` + `text-shadow`。
- **性能/可访问性**：纯静态绘制零成本；渐变文字保留语义文本（勿用图片/占位）；`text-transparent` 下若梯度对比不足需兜底色；`prefers-reduced-motion` 时去掉流光动画即可。
- **评级 ★★★★**：30 分钟让 GreetingBar 从「普通标题」变「品牌级视觉锚点」。

### 1.6 CSS 3D transform：卡片 tilt / 背景视差 ⭐⭐⭐⭐
- **类别**：交互层 / widget 层
- **参考**：MDN transform 3D（https://developer.mozilla.org/en-US/docs/Web/CSS/transform-function/rotate3d，未联网验证，极成熟）；Chrome 全系支持，Electron 28 ✅
- **社区热度**：`perspective` + `rotateX/rotateY` 的鼠标 tilt 卡片是 2023–2026「Bento 卡片」演示的标配交互（Vercel/Linear 类产品页、无数 CodePen "3d tilt card"）；比 WebGL 轻一个数量级但观感接近。
- **代表性案例**：Vercel/Linear 官网的 3D 卡片动效为行业标杆（未联网验证）；CodePen "tilt card mouse" 常青（未联网验证）；scroll-driven-animations 的 3D cover-flow demo（https://scroll-driven-animations.style/demos/cover-flow/css/，已验证）。
- **Vue 3 + Tailwind 写法**：纯 CSS + 少量 JS（组件内 pointermove 更新 CSS 变量）：
  ```
  <!-- 组件上绑定 --rx/--ry -->
  class="transform-gpu [transform:perspective(900px)_rotateX(var(--rx,0deg))_rotateY(var(--ry,0deg))] transition-transform duration-200"
  ```
  复用 `transform-gpu`（Tailwind 内置 `translateZ(0)`）确保合成层；背景视差则对 1.2 的背景层在滚动/指针时平移 transform。
- **性能**：transform 是合成属性，`will-change: transform` + 限制 tilt 幅度（≤8°）即可 60fps；避免 tilt 同时叠加 backdrop-filter（会重绘）。
- **可访问性**：`prefers-reduced-motion` 时归零 tilt（项目 tokens 已全局归零 duration，再加一个 media query 关 pointermove 监听）；交互由鼠标驱动，键盘用户有焦点样式即可。
- **评级 ★★★★**：交互层最「显性炫酷」且零依赖；建议只给 Hero/创建入口 1–2 张卡用，避免全部 tilt 显得廉价。

### 1.7 Container Queries + subgrid —— Bento 响应式治理 ⭐⭐⭐⭐
- **类别**：布局基建（非炫，稳）
- **参考**：caniuse CQ https://caniuse.com/css-container-queries（全局 92.6%，Chrome 106+，Electron 28 ✅）；caniuse subgrid https://caniuse.com/css-subgrid（全局 90.5%，Chrome 117+，Electron 28 ✅）
- **社区热度**：2023 起 container queries 全面可用，Tailwind 3.2+ 已内置 `@container` 与 `@lg:` 容器断点变体（本仓 Tailwind 3.4 直接可用）；subgrid 让 Bento 里「标题行/内容行跨卡片对齐」成为可能。
- **代表性案例**：Tailwind 官方 docs 的 container queries 示例（https://tailwindcss.com/docs/container-queries，未联网验证，官方文档）；CQ polyfill 团队 demo（https://github.com/GoogleChromeLabs/container-query-polyfill，caniuse 引用）。
- **Vue 3 + Tailwind 写法**：给 Bento 网格容器加 `@container`，widget 内用 `@lg:...` 变体做「窄卡单列/宽卡双列」的布局切换；subgrid：`[grid-template-rows:subgrid]`（arbitrary 值）让 `UiPanelHeader` 与 widget body 跨卡对齐。
- **性能/可访问性**：纯布局计算零运行时开销；CQ 需要每个 widget 有明确 `container-type`，注意 `inline-size` 会让 widget 尺寸不再受内部内容撑开（现有 Bento 网格已是显式格子，天然契合）。
- **评级 ★★★★**：不是炫技但让「Bento 网格在不同尺寸下智能重排 + 卡片内部自适应」成为可能，是炫酷效果的承载底盘。

### 1.8 View Transitions API（同文档）—— SPA 过渡的正式化 ⭐⭐⭐⭐
- **类别**：入场动效 / 路由过渡
- **参考**：caniuse https://caniuse.com/view-transitions（单文档 88.5%，Chrome 111+，Electron 28 ✅；跨文档需 126+，Electron 28 不可用——本项仅用同文档）
- **社区热度**：Chrome 111（2023）→ Safari 18（2024）→ Firefox 144（2025）之后成为 **SPA 过渡的标准姿势**；Chrome DevRel 官方 demo 站 + Bramus 系列文章（https://developer.chrome.com/docs/web-platform/view-transitions/，已验证）。
- **代表性案例**：
  - https://http203-playlist.netlify.app/（Chrome 官方 VT 演示站，已验证引用）
  - https://view-transitions.chrome.dev/cards/spa/（卡片增删过渡官方 demo，已验证引用）
- **Vue 3 + Tailwind 写法**：包一个 `useViewTransition` composable：
  ```js
  export function withViewTransition(update) {
    if (document.startViewTransition) return document.startViewTransition(() => update())
    update()
  }
  ```
  首页场景：DashboardEditor 显示/隐藏、搜索面板开合、widget 增删、路由切换时调用，并配 CSS：
  ```
  ::view-transition-old(root), ::view-transition-new(root) { animation-duration: .35s; }
  ```
  可给特定 widget 加 `view-transition-name` 做「卡片飞入/飞出」。
- **性能/可访问性**：浏览器原生快照 + 合成，比手写 JS 动画更省；默认对整页做快照，注意给每个 widget 独立 `view-transition-name` 否则会全页一起淡；`prefers-reduced-motion` 时 VT 自动降级为无过渡（API 内建）。
- **评级 ★★★★**：与「DashboardEditor 编辑态切换」「搜索面板开合」两个现有交互是天作之合，零依赖、原生、优雅。

### 1.9 scroll-driven animations —— 滚动驱动的原生动画 ⭐⭐⭐（首页属加分项）
- **类别**：入场动效 / 背景视差
- **参考**：官方 demo 站 https://scroll-driven-animations.style/（已验证）与 Chrome 文档 https://developer.chrome.com/docs/css-ui/scroll-driven-animations（已验证，Chrome 115+；Safari 26+；Firefox 需 flag）
- **社区热度**：Chrome DevRel 2023 起主推，Bramus 制作 10 集视频课 + demo 站 + DevTools 调试插件（scroll-driven-animations.style 顶部已验证）；2025 Safari 支持后开始「baseline 化」。**但本质面向滚动叙事页，仪表盘首页滚动场景有限**。
- **代表性案例**：https://scroll-driven-animations.style/demos/progress-bar/css/（滚动进度条）、/demos/image-reveal/css/、/demos/stacking-cards/css/（全部已验证官方 demo）
- **Vue 3 + Tailwind 写法**：`animation-timeline: view()` 配 keyframes（任意 CSS，@layer utilities）；首页若 Bento 网格可滚，可为「网格卡片进入视口时逐张浮现」写：
  ```
  .home-dashboard-grid__item { animation: reveal linear both; animation-timeline: view(); animation-range: entry 10% cover 30%; }
  ```
- **性能**：动画跑在合成器线程、主线程零负担（官方文档明确验证「off the main thread」）；这是比 IntersectionObserver + rAF 更优的方案。
- **可访问性**：`prefers-reduced-motion` 时必须关闭（媒体查询内把 animation-timeline 复位为 none）；内容本身不依赖动画可见。
- **评级 ★★★**：技术很酷、性能极佳，但首页是「一屏仪表盘」而非滚动长页，性价比低于 1.1/1.8；适合首页未来的「更多内容」滚动区。

### 1.10 CSS 基建组合：color-mix() + :has() + 原生 Nesting + @property ⭐⭐⭐⭐⭐（本域底座）
- **类别**：基建（让上面所有效果都更好写）
- **参考**：caniuse color-mix https://caniuse.com/mdn-css_types_color_color-mix（91.2%，Chrome 111+，Electron 28 ✅）；:has https://caniuse.com/css-has（92.7%，Chrome 105+）；Nesting https://caniuse.com/css-nesting（90.8%，Chrome 120 默认，Electron 28 ✅）；@property（Chrome 85+）
- **社区热度**：这四个是 2023–2026 「现代 CSS 复兴」四件套：color-mix 让「透明变体颜色」不用再手写 alpha 值；:has 是等了几十年的父选择器（做「卡片 hover 时兄弟/父元素响应」）；原生 Nesting 替代 SCSS 缩进；**@property 注册渐变角度后，conic-gradient 可以真正连续旋转/动画**（这是纯 CSS 渐变动画的钥匙）。
- **代表性案例**：项目自身已在 8 处使用 color-mix（已验证）；Chrome DevRel color-mix 指南（https://developer.chrome.com/docs/css-ui/css-color-mix，未联网验证，官方文档）；@property 动画示例（MDN，未联网验证）。
- **Vue 3 + Tailwind 写法**：`@layer utilities` 注册一个 `.animate-hue` / `.spin-conic`：
  ```css
  @property --angle { syntax: '<angle>'; inherits: false; initial-value: 0deg; }
  .ui-conic-ring { background: conic-gradient(from var(--angle), ...); animation: rotate-angle 8s linear infinite; }
  @keyframes rotate-angle { to { --angle: 360deg; } }
  ```
  color-mix 已在设计系统内（tokens 同款写法）；:has 做「卡片 hover 时网格呼吸」：`.home-dashboard-grid:has(.ui-widget-frame:hover) { --glow: 1 }`。
- **性能**：全部是声明式、合成/绘制层一次算；@property 动画目前走主线程绘制但 conic 渐变区域小则无感。
- **可访问性**：无新增风险；注意 :has 在大量节点上的选择器成本（Bento 网格几十个节点完全无压力）。
- **评级 ★★★★★**：这四件套是让「零依赖炫酷」能写出来的底层能力，且项目已经在用其中一半。

### 1.11 @starting-style + transition-behavior: allow-discrete —— 原生入场动效 ⭐⭐⭐⭐
- **类别**：入场动效
- **参考**：MDN @starting-style（https://developer.mozilla.org/en-US/docs/Web/CSS/@starting-style，未联网验证，Chrome 117+，Electron 28 ✅）
- **社区热度**：Chrome 117（2023）引入后，`display: none → block` 与「首次挂载」也能平滑过渡，补齐了 CSS 入场动效最后一块拼图；配合 dialog/popover 成为 2024–2026 纯 CSS 弹层动画标准。
- **代表性案例**：Chrome DevRel「entry animations」相关示例（未联网验证具体 URL，作为官方特性）；CodePen "@starting-style" 逐年增长（未联网验证）。
- **Vue 3 + Tailwind 写法**：Vue 3.5 的 `<Transition>` 已有 JS 方案，但原生 CSS 可替代部分；对首页 modal（搜索/复盘/文档/自动化四个 home-modal 现用 v-if + 无过渡）加：
  ```css
  .home-modal { transition: opacity .18s var(--ui-ease-standard), overlay .18s allow-discrete, display .18s allow-discrete; }
  .home-modal[hidden] / v-show 过渡配合 @starting-style { from { opacity: 0 } }
  ```
- **性能/可访问性**：纯 CSS 过渡，无 JS 开销；`transition-behavior: allow-discrete` 让 display 也能过渡（对现有 v-if 弹层可直接替换）；reduced-motion 已被 tokens 归零。
- **评级 ★★★★**：让首页四个 modal + toast 的「出现/消失」从生硬变顺滑，改动量极小。

---

## 2. 2024–2026 前沿趋势（本域）

1. **Glassmorphism 组件化/桌面化**：从整站视觉风格退居为「桌面应用仪表盘的默认面板质感」（Linear/Notion 同款），Awwwards 单列分类 → 对 Bento 仪表盘是长期安全选择。
2. **Grainy gradient（噪点渐变）成为暗色站标配**：conic/radial 渐变 + feTurbulence 噪点，零成本去除 banding 并提升「材质感」，CodePen/Dribbble 高产量。
3. **现代 CSS 四件套普及**：color-mix / :has / 原生 Nesting / @property 已在主流浏览器稳定 2–3 年，2026 的「新 CSS」不再需要预处理器或运行时。
4. **View Transitions 成为 SPA 过渡正式 API**：2023–2025 三大引擎全部落地，Bramus/Chrome DevRel 持续产内容 → 首页编辑/搜索/路由过渡建议直接用它。
5. **scroll-driven animations 主线程外动画**：Chrome 115 起支持、Safari 26 补齐、官方 10 集课程 → 滚动页性价比高，但 dashboard 首页属于「备用技能」。
6. **CSS if() / anchor positioning / light-dark() 为 2026 新前沿**：caniuse 首页最新特性已列（css-if、cross-document VT、CSS Grid Lanes），但 Electron 28 尚不支持 → 观望，等 Electron 升级。

---

## 3. 落到首页 Bento 仪表盘：怎么用

### 3.1 背景层（推荐优先做，10 分钟起效）
- **方案 A（噪点 + 霓虹光斑）**：`.bg-aurora`（conic/radial 用 `--ui-color-*` 变量）平铺 `#home-shell` 根节点 + `mix-blend-screen` 的 2–3 个静态光斑 div + `bg-noise`（feTurbulence data-URI）最上层。三者全 CSS、`position:fixed; z-index:-1; pointer-events:none; aria-hidden`。
- **方案 B（缓慢漂移）**：给背景层挂 `@property --bg-x/--bg-y` 的 60s 线性位移动画，GPU 合成零卡顿；`prefers-reduced-motion` 停掉。
- 背景层**不做** WebGL 级内容——CSS 背景就该是纯装饰，动态数据交给 widget。

### 3.2 widget 层
- **全卡玻璃化（推荐）**：`UiWidgetFrame` 的单条规则加 `backdrop-blur-xl bg-white/[0.05] border-white/10`，整个 Bento 立刻「浮在背景上」；对重点 widget（今日焦点、创建入口）额外加 `bg-white/[0.08]` 提亮。
- **2–3 张异形卡**：创建入口/快捷命令做 clip-path 斜切角 + 渐变描边；日历/热力图保持圆角（clip 与 radius 互斥，别全做）。
- **品牌字**：GreetingBar 的 `早上好, 章` 用 `bg-clip-text text-transparent` 渐变 + `-webkit-text-stroke` 细描边，配 1.2 的背景成为首页视觉锚点。
- **conic 进度环**（新卡片）：conic-gradient + `@property --angle` 做「今日完成度」环形仪表，纯 CSS、无 canvas。

### 3.3 交互层
- **Hero/创建入口 tilt**：pointermove 写 CSS 变量 `--rx/--ry`，`transform: perspective(900px) rotateX/rotateY`，幅度 ≤8°，`transform-gpu`；reduced-motion 直接不监听。
- **:has 联动**：`.home-dashboard-grid:has(.ui-widget-frame:hover)` 控制背景光斑亮度变量，实现「鼠标在哪，哪片背景亮」的呼吸感。
- **widget 内部**：ECharts 热力图/日历不动，只给卡片容器加交互。

### 3.4 入场动效
- **View Transitions**：包 `useViewTransition` composable，接入 DashboardEditor 开关、搜索面板开合、路由跳转；给四个 `home-modal` 加 `::view-transition` 微过渡。
- **@starting-style**：现有 modal/toast 的 v-if 显隐直接加 `transition + allow-discrete`，0 行 JS 换顺滑。
- **滚动入场（可选）**：Bento 网格容器若可滚，用 `animation-timeline: view()` 让卡片「进入视口时逐张浮现」，主线程零负担；reduced-motion 关闭。
- 入场统一用 `--ui-duration-*` + `--ui-ease-standard`（tokens 已定义），动效节奏与设计系统一致。

### 3.5 工程落地要点
- **全部零依赖**：本域所有方案不需要新增任何 npm 包（对比 WebGL 域的 three/TresJS/regl，CSS 域体积收益巨大）。
- **放哪**：自定义 CSS 进 `src/assets/main.css` 的 `@layer components|utilities`；工具类直写 Tailwind class；composable 进 `src/composables/home/`。
- **Storybook/Vitest 兼容**：无 canvas/WebGL，jsdom 下样式不参与，无测试破坏风险；组件仅加 class/修饰符，保持现有 `data-visual-anchor` 语义。
- **Electron 约束**：light-dark()、anchor positioning、CSS if()、跨文档 VT 在 Electron 28 不可用 → 本报告方案已全部避开；若未来升 Electron 可再解锁。
- **性能纪律**：backdrop-filter 不叠加高频动画；mix-blend 光斑静态化；clip-path 不与 border-radius 混用；tilt 幅度小。
- **可访问性纪律**：装饰层 `aria-hidden` + `pointer-events-none`；reduced-motion 走 tokens 归零 + 专项 media query；对比度靠 color-mix 提底。

---

## 4. 评分卡汇总

| 候选 | 兼容性(25%) | 社区(20%) | 新颖度+契合(20%) | 性能体积(20%) | 无障碍降级(15%) | 总分 | 评级 |
|---|---|---|---|---|---|---|---|
| **1.1 backdrop-filter 玻璃拟态** | 5 | 5 | 5 | 3 | 5 | 4.6 | ★★★★★ |
| **1.2 渐变+feTurbulence 噪点背景** | 5 | 4 | 5 | 5 | 5 | 4.8 | ★★★★★ |
| **1.10 CSS 基建（color-mix/:has/nesting/@property）** | 5 | 5 | 5 | 5 | 5 | 5.0 | ★★★★★ |
| 1.3 clip-path / mask 异形卡片 | 5 | 4 | 4 | 5 | 4 | 4.4 | ★★★★ |
| 1.4 mix-blend-mode 光斑 | 5 | 4 | 4 | 4 | 4 | 4.3 | ★★★★ |
| 1.5 文字渐变/描边/立体 | 5 | 4 | 4 | 5 | 4 | 4.5 | ★★★★ |
| 1.6 CSS 3D tilt / 视差 | 5 | 4 | 4 | 4 | 4 | 4.3 | ★★★★ |
| 1.7 Container Queries + subgrid | 5 | 4 | 3 | 5 | 5 | 4.4 | ★★★★ |
| 1.8 View Transitions（同文档） | 4 | 5 | 5 | 4 | 5 | 4.6 | ★★★★ |
| 1.11 @starting-style + allow-discrete | 4 | 3 | 4 | 5 | 5 | 4.2 | ★★★★ |
| 1.9 scroll-driven animations | 4 | 5 | 2 | 5 | 4 | 4.0 | ★★★ |

**入选（首页落地）**：玻璃拟态（1.1）、噪点+霓虹背景（1.2+1.4）、CSS 基建底座（1.10）、View Transitions（1.8）、tilt 卡片（1.6）
**按需选用**：clip-path 异形卡（1.3）、文字效果（1.5）、CQ+subgrid（1.7）、@starting-style（1.11）
**观望**：scroll-driven animations（1.9，等首页出现滚动长区）、light-dark()/anchor/if()（等 Electron 升级）

---

## 5. 一句话结论

本域最推荐的 3 个方向：**① 渐变+SVG feTurbulence 噪点/霓虹光斑纯 CSS 背景层（零依赖、全兼容、性能最优，★★★★★）；② backdrop-filter 玻璃拟态 Bento 卡片层（与现有设计系统零摩擦、Electron 100% 支持、一用即高级，★★★★★）；③ View Transitions + @starting-style 原生入场/过渡动效（接通 DashboardEditor/搜索面板/modal 显隐，浏览器原生零依赖，★★★★）**，三者叠加即构成「暗色噪点背景 + 玻璃网格 + 丝滑过渡」的完整纯 CSS 首页升级，体积成本 ≈ 0。
