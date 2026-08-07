# 渲染调研 Round 01 · 域 05：首页专属视觉模式（Bento 仪表盘动效化）

> 调研对象：Study-Hub 首页（Vue 3.5 + Vite 5 + Tailwind 3 + ECharts + Storybook 8.6；Bento 8×4 仪表盘，9 个 widget：工作热力 4x2/日历日程 2x2/今日任务 2x3/自动化队列 2x2/知识库 2x1/今日手账 1x1/快捷指令 1x1/创作入口 2x2/快捷工作流 2x1；GreetingBar 顶部问候，CapsuleNavigation 胶囊导航；卡片底座 `DashboardModuleCard`/`UiWidgetFrame`，暗色 #1b1d1a 表面 + #d7ff63 荧光 accent）。
> 调研时间：2026-08-03。数据来源：产品官网 / Awwwards / Aceternity UI / Magic UI / GitHub / npm registry，均联网验证可达；标注「未联网验证」的条目基于公开已知知识，需人工复核。
> 评分卡权重（沿用任务书）：Vue3/Vite 兼容 25%、社区活跃度 20%、效果新颖度+场景契合 20%、性能/包体积 20%、无障碍/降级 15%。
> 与同轮 01（WebGL/3D）、02（Canvas/粒子）的分工：本域聚焦**不引重引擎**即可落地的 DOM/CSS/轻 JS 视觉范式，作为首页 Bento 的"皮肤与交互层"；canvas/WebGL 背景由 02/01 域负责。

---

## 0. 结论速览

| 模式 | 类别 | 主要实现路径 | 评级 | 一句话 |
|---|---|---|---|---|
| **Bento 卡片动效化（hover 放大/内容流动/展开）** | 布局·交互动效 | 纯 CSS + Tailwind `group-hover`，无需库 | ★★★★★ | Linear/Dub 首页的核心玩法，项目已具备 Bento 底座，成本≈0，收益最直接 |
| **Spotlight 光标聚光 + 方向感知高亮** | 交互·装饰 | 纯 CSS 变量 + `useMouse`，Aceternity 模式移植 | ★★★★★ | 暗色仪表盘的"高级感开关"，纯 CSS 可做、GPU 友好、a11y 无侵入 |
| **countUp 数字滚动 + SVG 描边/流光数据动效** | 数据·widget 动效 | `countup.js`（7KB）+ CSS `stroke-dashoffset` | ★★★★ | 让热力图/统计类 widget "活"起来，替换 ECharts 默认入场的最轻方案 |
| **tilt/3D 卡片视差** | 交互·3D 装饰 | `vanilla-tilt`（8.5KB，框架无关）或自写 composable | ★★★★ | 卡片 hover 立体感，Bento 网格做整体 tilt 比单卡更克制也更好看 |
| **鼠标视差分层（parallax layers）** | 背景·视差 | `@vueuse/core` `useParallax`（2.4KB） | ★★★★ | 背景光晕/渐变层随鼠标位移，给静态背景加"呼吸感"，与 02 域粒子不冲突 |
| **macOS Dock 缩放菜单** | 导航·交互 | 自写 composable（20 行）或 Aceternity floating-dock 移植 | ★★★ | CapsuleNavigation 已有替代，仅当要"收藏夹 Dock"时用；零依赖手写最稳 |
| **玻璃拟态仪表盘（glassmorphism）** | 皮肤·材质 | Tailwind `backdrop-blur` + `bg-white/10` | ★★★ | 当前已接近玻璃感（半透明边框），补 `backdrop-blur` 即可；注意 Electron 渲染性能 |
| **渐变/噪点背景层** | 背景·装饰 | Tailwind 渐变 + SVG 噪点 data-uri | ★★★★ | 与 spotlight 组合出"产品级"首页氛围，零 JS 成本 |
| **入场动效编排（stagger/fade/slide）** | 入场·编排 | `@vueuse/motion`（<20KB，20+ presets）或纯 CSS | ★★★★ | 首页首次加载的 widget 逐个浮现，与 02 域 GSAP 定位错开（轻量路径） |
| **Animated Beam / 边界流光** | 装饰·动效 | 自写 CSS `@property`/渐变旋转 + mask | ★★★ | Magic UI 的 border-beam 移植，适合"正在同步/队列运行"状态卡 |

**本域最推荐 3 个模式**（见 §3 组合）：
1. **Bento 卡片动效化**（★5）—— 首页视觉重构的第一抓手，成本≈0、视觉收益最高。
2. **Spotlight + 方向感知高亮**（★5）—— 暗色仪表盘氛围感神器，纯 CSS + `useMouse` 即可。
3. **countUp + SVG 描边数据动效**（★4）—— 统计类 widget 的"活数据"质感，7KB 级成本。

---

## 1. 候选模式明细

### 1.1 Bento 卡片动效化（hover 放大 / 内容流动 / 卡片展开） —— ★★★★★

- **类别**：布局动效（dashboard 卡片体系的核心交互语言）
- **参考案例**（均已联网验证可达）：
  - https://linear.app/ —— 首页即产品界面：暗色卡片 + 微动效 + 数据密集
  - https://dub.co/ —— 首页把真实 Dashboard（Bento 网格 + 数字滚动 + 实时数据表）当展示素材
  - https://vercel.com/ —— 首页卡片网格 hover 时的轻微放大/光晕
  - https://bentogrids.com/ —— Bento 网格范式合集（Linear/Vercel/Notion 等截图，JS 渲染页已验证可达）
- **在 Vue 3 + Tailwind 的实现路径**：**零新依赖**。项目已用 `BentoDashboardGrid`（8 列×4 行）+ `DashboardModuleCard`/`UiWidgetFrame` 作为卡片底座，只需：
  - hover 放大：`transform-gpu hover:scale-[1.02] hover:-translate-y-0.5` + `transition-transform duration-300 ease-out`；放大临界值注意 8 列 grid 中相邻卡不重叠。
  - 内容流动（参考 Magic UI bento-demo 的 `group-hover:scale-90` 背景内移）：卡片内绝对定位装饰层（如热力网格、日历 mini-grid）用 `group-hover` 从 `blur-[1px] opacity-60` → `blur-0 opacity-100 scale-105`，营造"进入卡片"感（参考 https://magicui.design/docs/components/bento-grid 的 BentoCard 背景 mask + group-hover 模式）。
  - 卡片展开/详情：`DashboardEditor` 已有编辑态；"hover 预览展开"建议用 `<Transition>` + 卡片内部展开（避免覆盖 grid 布局），键盘焦点时 `focus-visible` 同样触发展开态（`:focus-visible` 上加相同的 class）。
- **性能与可访问性**：只动 `transform/opacity/filter`（合成器属性），不触发重排；`filter: blur` 在 hover 瞬时（非持续）可接受；`prefers-reduced-motion` 下退化为无过渡直接显示；交互态必须同时绑定 `:hover` 与 `:focus-visible` 以保键盘可达（项目 a11y 测试基线：storybook addon-a11y + vitest）。
- **评级理由**：不动架构、不动依赖树，仅 CSS 层，就把首页从"静态网格"升级为"产品级 Bento"；且 Linear/Dub 已证明这是 dashboard 类首页的事实标准。

### 1.2 Spotlight 光标聚光 + 方向感知高亮 —— ★★★★★

- **类别**：光标跟随装饰（spotlight hover / direction-aware border glow）
- **参考案例**（均已联网验证可达）：
  - https://ui.aceternity.com/components/spotlight —— Aceternity 官方组件（受 TypeHero 着陆页启发），纯 Tailwind + CSS
  - https://ui.aceternity.com/components/card-spotlight —— 卡片级 spotlight
  - https://ui.aceternity.com/components/direction-aware-hover —— 方向感知高亮（从鼠标进入方向抹光）
  - Linear/Vercel 暗色首页的卡片 hover 均有类似"聚光"语言（未联网逐点验证，基于官网访问印象）
- **在 Vue 3 + Tailwind 的实现路径**：**零/轻依赖**。核心是 CSS 变量跟随鼠标：
  ```vue
  <div class="card group" @pointermove="onMove" @pointerleave="onLeave">
    <div class="spotlight" :style="{ '--mx': x+'px', '--my': y+'px' }" />
  </div>
  ```
  其中 `.spotlight { background: radial-gradient(240px circle at var(--mx) var(--my), rgb(215 255 99 / .08), transparent 60%); }`，`useMouse`/`useElementBounding` 算卡片内坐标（或手写 `pointermove` + `getBoundingClientRect`，30 行内）。方向感知高亮（direction-aware）是"鼠标进入方向决定高亮边"，用 `data-dir` 存 4 向 + CSS `::after` 渐变边，纯 CSS 可做（Aceternity 该组件本体 ~50 行）。
- **性能与可访问性**：pointermove 只写 CSS 变量（每帧一个 style 写 + 合成层），无重排；径向渐变是一次性绘制；装饰层 `pointer-events:none` + `aria-hidden`；`prefers-reduced-motion` 下关闭过渡/淡入即可；`@media (hover:none)` 触摸设备自动无效果（本来就没有光标）。
- **评级理由**：暗色 dashboard 的"氛围感"溢价最高、实现成本最低的范式；且本项目 accent 是荧光黄绿（#d7ff63），spotlight 用它做光晕与热力图色系一脉相承。

### 1.3 countUp 数字滚动 + SVG 描边/数据流光 —— ★★★★

- **类别**：数据 widget 动效（统计数字滚动、进度环描边、数据流光）
- **参考案例**：
  - https://github.com/inorganik/countUp.js —— **已联网验证**：8.2k stars、MIT、零依赖、ESM/UMD、`autoAnimate`（IntersectionObserver 可见才播）、`useEasing`/`smartEasing`、`useGrouping`、odometer 插件
  - https://dub.co/ —— 首页数字（clicks/leads/sales、$12K）滚动感（视觉印象，未逐帧验证）
  - Magic UI number-ticker（https://magicui.design/docs/components/number-ticker，React，实现参考）
- **在 Vue 3 的实现路径**：⚠️ `vue-countup-v2`（npm 已验证）最后发版 4.0.0 于 **2019-06**，基于 Vue2 时代（peerDeps `vue:*` 但 devDeps 全 Vue2），**不建议直接引**。正确做法：`npm i countup.js`（~7KB gzip），自写一个 `<CountUp :end=".." />` 组件（onMounted new CountUp + watch end + onUnmounted destroy，约 30 行）或直接 composable。**SVG 描边**（进度环/连线）：`stroke-dasharray` + `stroke-dashoffset` 由 Vue 响应式驱动（`watch(value)` → `el.style.strokeDashoffset = ...`），无需任何库；数据流光 = `stroke-dasharray` 动画 + CSS `@keyframes dash` 循环，配 `pathLength` 归一化。
- **性能与可访问性**：数字滚动是 DOM 文本替换（textContent），无重排风暴（低频率更新）；`autoAnimate` 用 IntersectionObserver 天然避免离屏动画；`prefers-reduced-motion` 下 `startVal=endVal` 直接显示终值（组件内一个三元）；数字本身是真实文本 → 屏幕阅读器可读；SVG 装饰层 `aria-hidden`。
- **评级理由**：热力图/今日任务/创作入口这些 widget 的"今日完成数/连续天数/队列条数"字段滚动起来，是 dashboard 数据感的最轻量表达；比 ECharts 动画便宜、可控。

### 1.4 tilt / 3D 卡片视差 —— ★★★★

- **类别**：鼠标视差（卡片跟随光标轻微旋转/平移，含 glare 反光）
- **参考案例**：
  - https://github.com/micku7zu/vanilla-tilt.js —— **已联网验证**：4k stars、MIT、零依赖 ~8.5KB min、支持 `glare`（反光）、`max` 角度、`gyroscope`（移动端陀螺仪）、`mouse-event-element`、reset
  - https://ui.aceternity.com/components/3d-card-effect —— Aceternity 3D Card（React + framer-motion，实现参考；原理是 `perspective` + `rotateX/rotateY`）
- **在 Vue 3 + Tailwind 的实现路径**：两选一：
  - `npm i vanilla-tilt`（8.5KB），composable 封装：`onMounted(() => VanillaTilt.init(el, { max: 6, glare: true, 'max-glare': 0.4, speed: 400 }))` + `onBeforeUnmount` destroy。卡内 `transform-style: preserve-3d`，子元素可配 `translateZ` 做出层叠。
  - 自写 20 行 composable（`useTilt`）：`pointermove` → 归一化坐标 → `rotateX/rotateY`（上限 ~6°），退出 reset。**Bento 网格建议全局 tilt 上限更小（3–5°）**，避免 8 列网格视觉歪斜。
- **性能与可访问性**：transform 属性动画合成器友好；vanilla-tilt 内部用 RAF + transition；`prefers-reduced-motion` 下禁用 tilt（`if (matchMedia('(prefers-reduced-motion: reduce)').matches) return`）；tilt 是纯装饰，不影响信息层级；注意 `will-change: transform` 只加在 hover 态。
- **评级理由**：Bento 网格整体做轻微 tilt + 高亮，能显著提升"活"感；包小、无 Vue 适配成本，但注意克制（网格场景角度宜小）。

### 1.5 鼠标视差分层（parallax layers） —— ★★★★

- **类别**：背景视差（鼠标移动时背景光晕/装饰层反向位移）
- **参考案例**：https://vueuse.org/core/useParallax/ —— **已联网验证**：VueUse 官方 composable（导出大小 2.41KB），内部 `useDeviceOrientation` + fallback `useMouse`，返回 `tilt/roll`（-0.5~0.5）
- **在 Vue 3 的实现路径**：`npm i @vueuse/core`，`const { tilt, roll } = useParallax(containerRef)`，背景层 `transform: translate(calc(tilt*20px), calc(roll*20px))`。适合：背景渐变光晕层/噪点层随鼠标平移，前景 Bento 网格不动 → 天然景深；**注意与 1.2 spotlight、02 域粒子同时存在时，运动层次不要超过 2 层**（背景视差 + 卡片聚光即可，再叠加粒子可能晕）。
- **性能与可访问性**：tilt/roll 是 ComputedRef，需节流/RAF 后写 style（VueUse 本身有 RAF 选项）；纯 transform；`prefers-reduced-motion` 停用；装饰层 aria-hidden。
- **评级理由**：给"静态渐变背景"加一层低成本视差，让首页在无粒子时也有呼吸感；与 02 域 tsParticles 是"低配/高配"两条背景路线。

### 1.6 入场动效编排（stagger / fade / slide） —— ★★★★

- **类别**：首次加载与切换的入场编排
- **参考案例**：https://motion.vueuse.org/ —— **已联网验证**：`@vueuse/motion` 3.0.3（npm registry 确认，2025-03 发布，MIT，peerDeps `vue>=3.0.0`，<20KB，SSR-ready，基于 Popmotion，API 仿 Framer Motion），20+ 预设：`fade-visible-once`、`roll-visible-once-bottom`、`pop-visible-once`、`slide-visible-*`
- **在 Vue 3 的实现路径**：`npm i @vueuse/motion`，`app.use(MotionPlugin)` 后模板内 `v-motion-fade-visible-once` 直接生效；或 `useMotion(target, { ... })`。Bento widget 逐个浮现：给 9 个 widget 容器加 `v-motion` + `:initial`/`:enter`，用 `:delay` 错峰（stagger 0.06s）。与 02 域 GSAP 的定位区分：**@vueuse/motion 管"DOM 级轻入场"，GSAP 管"复杂时间轴/与 canvas 粒子协同"**，不重复引入。
- **性能与可访问性**：仅在可见时触发（visible-once 预设内部 IntersectionObserver）；transform/opacity 合成器属性；`prefers-reduced-motion` 下 Motion 组件可全局禁用（MotionPlugin 提供 reducedMotion 配置）；入场后元素即静态，无持续开销。
- **评级理由**：首页首屏"9 个 widget 依次浮现 + 问候语淡入"是产品级观感的最低成本路径；官方 Vue3 支持、体积小、预设即用。

### 1.7 渐变/噪点背景层 + 玻璃拟态 —— ★★★★ / ★★★

- **类别**：皮肤材质（背景氛围 + 卡片材质）
- **参考案例**：
  - Linear/Vercel 暗色首页的径向渐变背景（线性渐变 + 品牌色光晕，未联网逐点验证，官网访问印象）
  - Aceternity grid-and-dot / aurora background（https://ui.aceternity.com/components/aurora-background 已验证可达，React+Tailwind 实现参考）
  - Magic UI noise-texture / grid-pattern（https://magicui.design/docs/components/ 目录已验证）
- **在 Vue 3 + Tailwind 的实现路径**：纯 CSS。a) 渐变：`bg-[radial-gradient(...)]` 两三个色块 + `opacity-20 blur-3xl` 的光晕 div，配合 1.5 视差；b) 噪点：SVG feTurbulence data-uri 作为 `background-image`，`opacity-[0.03]` 盖全屏，消除渐变"塑料感"（产品级细节，成本≈0）；c) 玻璃拟态：`backdrop-blur-xl bg-white/5 border border-white/10`（项目 `DashboardModuleCard` 已是 `border rgb(245 246 238 / .16)` + `#1b1d1a` 底，补 backdrop-blur 即玻璃化；`UiWidgetFrame` 走 `--ui-color-surface` 变量，需在主题变量处统一）。
- **性能与可访问性**：CSS 渐变/噪点零 JS；`backdrop-blur` 是合成层滤镜，**Electron 窗口里大量 backdrop-blur 有已知性能损耗**（尤其同时铺满屏时）——建议只在卡片 hover 或局部小面积启用，或提供"关闭毛玻璃"开关；装饰层 aria-hidden。
- **评级理由**：噪点 + 渐变 + spotlight 三件套是"2024–2026 产品级暗色仪表盘"的标准皮肤配方；成本极低。

### 1.8 macOS Dock 缩放菜单 —— ★★★

- **类别**：导航交互（光标靠近时图标放大、tooltip 弹出）
- **参考案例**：
  - https://ui.aceternity.com/components/floating-dock —— **已联网验证**：Aceternity floating-dock（React + framer-motion；官方注明灵感来自 rauno.me 与 Build UI magnified-dock，rauno.me 未联网验证）
  - https://magicui.design/docs/components/dock —— Magic UI dock（React，实现参考）
  - macOS Dock 本身（交互范式源头）
- **在 Vue 3 + Tailwind 的实现路径**：**无成熟 Vue 封装（npm 检索「vue dock magnify」无直接结果）→ 自写**：核心是"距光标最近的两个邻居放大"——`useMouse`/`pointermove` 记录容器内 x，每个 icon 按 `1 - min(|iconCenterX - mouseX|, 96) / 96` 计算 scale（clamp 0.85–1.5），写 `transform: scale()`；加 `transition: transform .15s` 平滑。约 30–40 行 composable + 模板。Aceternity 的鼠标 x 共享思路可参照（单容器内共享 `mouseX`）。
- **性能与可访问性**：每个 pointermove 只更新受影响的 2–3 个 icon（按距离差计算），而非全部；tooltip 需键盘可达（`focus-visible` 展开 + `aria-label`）；图标是导航 → 保持 `<a>/<button>` 语义；reduced-motion 下只显示 tooltip 不缩放。
- **评级理由**：炫、有记忆点，但项目已有 CapsuleNavigation；Dock 适合做"底部收藏夹/快捷入口"的补充层，属可选增强而非必需——评级 ★★★。

### 1.9 Animated Beam / 边界流光 —— ★★★

- **类别**：装饰动效（卡片边界光晕旋转、数据连线流光）
- **参考案例**：https://magicui.design/docs/components/border-beam 与 animated-beam（目录已验证可达；React 实现）——常用于"AI 正在处理/同步中"状态
- **在 Vue 3 + Tailwind 的实现路径**：自写 CSS。边界流光：卡片 `::before` 作渐变 `conic-gradient`（accent 色 0/90/360° 三段高光）+ 父容器 `overflow:hidden` + 旋转动画；现代写法用 `@property --a` 做角度插值（Chrome/Edge/Safari 16.4+），兼容方案退化为 `transform: rotate()` 套在裁切容器里。数据流光：`stroke-dasharray` 循环（见 1.3）。
- **性能与可访问性**：`@property` 角度动画是合成器友好；持续旋转类动画需 reduced-motion 停用；装饰层 aria-hidden。
- **评级理由**：只建议用在"状态卡"（自动化队列运行中、今日任务进行时）做一次性/低频流光，而非全部卡片常驻（会喧宾夺主且费电）——因此 ★★★。

---

## 2. 首页 Bento 仪表盘怎么用（落到真实组件）

> 现状锚点（已读代码确认）：`Home.vue` 用 `BentoDashboardGrid`（8 列×4 行，gap 14.31px）+ `DashboardModuleCard`（圆角 22px、暗底、overflow:hidden）承载 9 个 widget；`GreetingBar` 顶部问候；`CapsuleNavigation` 顶部导航；accent 荧光黄绿 `#d7ff63` / 紫 `#8b73ff` 与热力图同系；已有 echarts / markmap / vuedraggable；测试 vitest + Storybook a11y addon。

### 2.1 背景层（氛围，不抢 widget 焦点）
- **首选组合**：径向渐变光晕（品牌色 2 个） + SVG 噪点 data-uri 全屏覆盖（opacity ~0.03）→ 一次性成本，零 JS。
- **加视差**（可选）：`@vueuse/core` `useParallax` 让光晕层随鼠标 ±20px 平移，与 Bento 网格产生景深（★4，2.4KB）。
- **再升级**（02 域）：tsParticles 知识网络粒子背景；本域不再重复选型。
- **纪律**：背景层 `position:fixed; z-index:0; pointer-events:none; aria-hidden`；`prefers-reduced-motion` 停视差、噪点保留（静态）。

### 2.2 widget 层（卡片内局部效果）
- **通用卡片皮肤**（一次性改 `DashboardModuleCard`）：hover `scale-[1.02] + spotlight 聚光 div`（1.2 的 CSS 变量方案）；热力图/日历/创作入口这几个"有内容密度"的 widget 加"内容流动"（内层装饰在 hover 时 `scale-105 + blur-0`）。
- **统计字段**（今日任务/自动化队列/创作入口/热力图小计）：`CountUp` 组件（1.3）滚动数字；完成度/进度环用 SVG `stroke-dashoffset`。
- **状态卡**（自动化队列运行中、快捷指令执行）：`border-beam` 式流光（1.9），低频触发。
- **3D 层叠**（可选）：今日任务/快捷指令这类"工具型"卡片做轻量 tilt（1.4，max 3–5° + glare 0.3）。

### 2.3 交互层
- **光标聚光**：所有卡片共享一个 spotlight（1.2），hover 才显示。
- **Dock 收藏夹**（可选增强，底部）：自写 magnified-dock composable（1.8），放快捷指令/创作入口直达；不做则维持 CapsuleNavigation。
- **注意**：Bento 卡片可点击区域大、且 grid 密集，tilt/spotlight 都要"hover 触发、移出还原"，避免常驻动画与编辑态（`DashboardEditor` 拖拽排序）冲突——编辑态下所有 hover 动效应统一禁用。

### 2.4 入场动效
- **首屏**：GreetingBar 淡入下滑；9 个 widget 用 `@vueuse/motion` `v-motion` + stagger delay 0.06s 逐个 `fade-visible-once`（1.6），总时长 <1s，避免等待感。
- **数据刷新**：widget 数据更新时 ECharts 自带动画、countUp 重播（数据变化 watch）；不做全局重排动画。
- **降级链**：`prefers-reduced-motion` → 全部直接显示（CSS media query + MotionPlugin 配置 + CountUp startVal=endVal）；`navigator.deviceMemory < 4` / 2g-3g → 跳过视差与 spotlight（仅静态渐变）。

---

## 3. 推荐组合与下一轮原型验证

**推荐组合（本域，按优先级）**：
1. **Bento 卡片动效化 + Spotlight/方向感知高亮**（★5）—— 改 `DashboardModuleCard` 一个组件即全站生效：hover 放大 + 荧光聚光 + focus-visible 同态。成本≈0，最优先。
2. **countUp + SVG 描边数据动效**（★4）—— `countup.js` 7KB + 自写 `CountUp.vue`（30 行），热力图/任务/队列 widget 数字滚动。
3. **渐变 + 噪点背景 + useParallax 视差**（★4）—— `@vueuse/core` 2.4KB，首页氛围打底；与 02 域粒子路线互斥可切换。
4. （可选）@vueuse/motion 入场编排 —— 首屏 stagger，<20KB。

**下一轮原型验证（Storybook）**：
- `BentoCardMotion.stories.jsx`：hover 放大 + spotlight + 内容流动，Playwright 断言 transform 变化与 reduced-motion 降级、focus-visible 触发。
- `SpotlightCard.stories.jsx`：CSS 变量跟随 + `pointer-events:none` + a11y 无侵入断言。
- `CountUpWidget.stories.jsx`：countup.js 自封装组件，数字滚动、IntersectionObserver 可见才播、reduced-motion 终值。
- `ParallaxBackground.stories.jsx`：useParallax 光晕层视差 + 关闭降级。
- 硬约束复测：不破坏现有 vitest/Storybook；与 echarts/markmap/vuedraggable 无冲突（本域全走 DOM/CSS，不碰 canvas）；与 02 域粒子并存时运动层次 ≤2。

**淘汰/观望记录**：vue-countup-v2（2019 停更、Vue2 时代 → 淘汰，用 countup.js 自封装）；`vue3-dock`（npm 不存在 → 淘汰，Dock 自写）；PixiJS/WebGL 背景（本域不涉及，01 域已评）；per-pixel 粒子文字/常驻流光（噱头，reduced-motion 后无意义 → 不做）。

---

## 4. 调研元信息

- 联网验证（HTTP 200）：linear.app、vercel.com、raycast.com、dub.co、ui.aceternity.com（spotlight / 3d-card-effect / floating-dock / bento-grid / aurora-background）、magicui.design（components 目录 / bento-grid）、ui.shadcn.com/docs/components/card、bentogrids.com、vueuse.org/core/useParallax、motion.vueuse.org（presets）、github.com/inorganik/countUp.js、github.com/micku7zu/vanilla-tilt.js、awwwards.com/websites/dashboard/、npm registry（@vueuse/motion 3.0.3、vue-countup-v2 4.0.0、search「vue dock magnify」）。
- 未联网验证：Linear/Dub/Vercel 首页动效逐帧细节、rauno.me（dock 灵感源）、TypeHero 着陆页、Dribbble 案例具体内容、countup.js 精确 gzip 数值（README 言 ~7KB，基于经验量级）、Aceternity/Magic UI 组件代码逐行移植难度。
- 许可提醒：本域核心依赖（countup.js、vanilla-tilt、@vueuse/core、@vueuse/motion）均 MIT；Aceternity/Magic UI 组件用于**实现参考**（其代码主要面向 React + shadcn，本域全部改为 Vue 自写/CSS 移植，不直接拷贝其组件代码）。
