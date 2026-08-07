# Round-01 · 动效引擎与滚动叙事调研笔记

> 主题域：动效引擎与滚动叙事（GSAP / Motion / Lenis / Vue 转场 / View Transitions / scroll-driven animations）
> 面向项目：Study-Hub 首页 Bento 仪表盘（Vue 3.5 + Vite 5 + Tailwind 3.4 + ECharts + Storybook）
> 数据获取时间：2026-08-03（GitHub API / npm registry / npm downloads / caniuse / 各官网，均已联网验证；未验证项单独标注）

---

## 0. 一句话结论（Top 3）

1. **Motion for Vue（`motion-v`）** ★★★★★ — 官方 Vue 包、60 万周下载、声明式 `<motion.div>` API 与 Vue 组件模型天然契合，直接覆盖 Bento 仪表盘的入场/悬浮/交错浮现。
2. **View Transitions API（零依赖 + 路由转场封装）** ★★★★☆ — 88.47% 浏览器支持、零体积，是"轻量页面转场"与 widget 展开的首选原生方案。
3. **Lenis 平滑滚动** ★★★★☆ — <4KB、官方 Vue 支持、业界标准（GTA VI / Netflix 官网），给首页滚动叙事加"丝滑"底子。

备选强者：GSAP + ScrollTrigger/SplitText ★★★★☆（顶级定制动效，但偏重，用于"锦上添花"层）。

---

## 1. Motion / Motion for Vue（motion-v） — 官方声明式引擎

| 项 | 内容 |
|---|---|
| 名称 / 类别 | Motion（原 Framer Motion / Motion One）· 声明式动画引擎（JS + WAAPI 混合） |
| 官方链接 | https://motion.dev · Vue 文档 https://motion.dev/docs/vue |
| npm 包 | `motion`（v12.43.0，通用 JS/React）；**`motion-v`（v2.3.0，Vue 专属）** |
| 成熟度 | GitHub 33,059★（motiondivision/motion，2026-07-28 有推送）；`motion` 周下载 1726 万（含 framer-motion 依赖）；`motion-v` 周下载 **60.2 万**，2026-06 发版，MIT |
| 社区热度 | Motion+ 订阅、410+ 可复制示例、官方"GSAP vs Motion"对比页、MotionScore 性能审计工具；Figma/Framer/Linear/Clerk/Sanity 为赞助伙伴 |
| 代表案例 | Linear（linear.app，framer-motion 驱动）、Framer 生态站群、motion.dev 官网的滚动/手势演示（examples.motion.dev/vue/*） |
| Vue 3 集成 | `npm i motion-v`；`<motion.div>` 组件 + `:initial/:animate/:whileHover/:whilePress/:whileInView/:exit` props、`layout/layoutId`、`<AnimatePresence>`、composables `useScroll/useSpring/useTransform/useInView/useReducedMotion/useAnimate`；支持 `unplugin-vue-components` resolver 与 Nuxt 模块；peer 依赖 `vue>=3`、`@vueuse/core>=10` |
| 性能与可访问性 | 混合引擎走 WAAPI 硬件加速（transform/opacity 合成）；gzip 约 8–15KB；`useReducedMotion` 官方 hook；hover 在触屏不误触发（优于 CSS :hover）；layout 动画只动 transform、自动 scale 校正 |
| 评级 | ★★★★★ — 官方 Vue 一等公民 + 高活跃 + 声明式 API 与 Bento 组件树完美咬合，是首页动效首选引擎 |

**落地映射（首页 Bento）：**
- **widget 层入场**：`<motion.div :initial="{opacity:0,y:24,scale:.96}" :animate="{opacity:1,y:0,scale:1}" :transition="{delay:i*0.06}">` 实现卡片交错浮现（stagger 用 index 算 delay 即可，无需额外编排库）。
- **交互层**：`whileHover`（卡片 lift + 阴影过渡）、`whilePress`（按下缩放 0.98）、`layoutId`（Bento 卡片展开为详情面板时的"共享元素"过渡，或 CapsuleNavigation 滑动指示器）。
- **转场层**：`<AnimatePresence mode="out-in">` 包 RouterView / widget 切换，配合 `:exit` 做离场动画。
- **数据卡片**：`useSpring + useTransform` 做数字滚动计数，衔接现有 ECharts（仅包图表容器不动 canvas 内部）。

---

## 2. GSAP + ScrollTrigger / SplitText / Flip — 专业级全栈动效

| 项 | 内容 |
|---|---|
| 名称 / 类别 | GSAP（GreenSock）· 专业动画引擎 + 滚动/文本/布局插件族 |
| 官方链接 | https://gsap.com · showcase https://gsap.com/showcase/ |
| npm 包 | `gsap`（v3.15.0，2026-04 发布） |
| 成熟度 | 周下载 **442.97 万**；官方称被 Webflow 收购后继续维护；**所有核心插件免费**（3.13 起 SplitText/Flip/ScrollTrigger/ScrollSmoother/Observer/MorphSVG/MotionPath/CustomEase/ScrambleText 全部并入 npm 包） |
| 许可注意 | 非 OSI 开源：`Standard 'no charge' license`（免费无商业限制，但不是 MIT/GPL；需留意其条款） |
| 社区热度 | Awwwards 站点幕后主力；GSAP Showcase 常年更新（2025 Showreel）；社区论坛 + Discord 活跃；CodePen 生态庞大 |
| 代表案例 | Bombon（bombon.rs）、Cobloc 建筑事务所（cobloc.archi）、Kononenko Group（kononenkogroup.com）、Noomo（showcase.noomoagency.com）、Square43（square43.com） |
| Vue 3 集成 | 无官方 Vue 专用 hook（React 用 `@gsap/react`）；Vue 推荐 `gsap.context()` + `onMounted/onUnmounted` 手动注册/清理（或自封装 `useGsap` composable）；插件按需 `import { ScrollTrigger } from 'gsap/ScrollTrigger'; gsap.registerPlugin(...)` |
| 性能与可访问性 | 体积偏大：core min 72.9KB（gzip≈23KB）+ ScrollTrigger 44.6KB + SplitText 7.7KB，需**按需引入 + 懒加载**（首页才加载）；ScrollTrigger 默认监听 window 滚动，与 Lenis/局部滚动容器需要 `scrollerProxy`/`invalidateOnRefresh` 兼容配置；`gsap.matchMedia()` 官方支持 `prefers-reduced-motion` 分支；SplitText 拆分后 `aria` 配置可保无障碍 |
| 评级 | ★★★★☆ — 天花板级能力 + 超强社区，但体积与 Vue 集成成本偏高，作为"定制精品动效"而非全站默认引擎 |

**落地映射（首页 Bento）：**
- **GreetingBar 文本**：SplitText 按字符/单词入场（mask + stagger），做"数字时钟"或逐字扫过；这是 motion-v 不便做、GSAP 最擅长的部分。
- **滚动叙事**：ScrollTrigger 把首页纵向滚动绑定到 GreetingBar 淡出、Bento 卡片 parallax/逐段 reveal；`scrub` 让进度贴手。
- **Flip**：Bento 卡片布局变更（增删 widget）时的平滑 FLIP 过渡——但需注意与现有 `vuedraggable` 的拖拽动画并存问题（建议只给非拖拽场景用）。
- **背景层**：Observer/MotionPath 做光晕缓移、粒子缓动；`prefers-reduced-motion` 时整段跳过。

---

## 3. Lenis 平滑滚动 — 滚动叙事底座

| 项 | 内容 |
|---|---|
| 名称 / 类别 | Lenis（darkroom.engineering）· 轻量平滑滚动（虚拟滚动同步） |
| 官方链接 | https://lenis.dev · showcase /showcase |
| npm 包 | `lenis`（v1.3.25），子路径 `lenis/vue`、`lenis/react`、`lenis/snap` |
| 成熟度 | GitHub 15,238★，2026-07-23 有推送，MIT；周下载 **127.08 万**；官方宣称 <4KB |
| 社区热度 | 行业默认平滑滚动方案：**Locomotive Scroll v5 底层即依赖 lenis**；Framer 插件；Netflix / Rockstar / Google Sports 等大站使用 |
| 代表案例 | GTA VI 官网（rockstargames.com/VI）、Netflix 招聘（jobs.netflix.com）、Lando Norris（landonorris.com）、Unseen Studio（unseen.co）、Ibicash（ibi.cash） |
| Vue 3 集成 | `lenis/vue` 导出 `<Lenis>` 组件或 `useLenis`；或 vanilla `new Lenis({ autoRaf: true })` 在 `onMounted` 创建、`onUnmounted` destroy；官方原生支持 vue 3 |
| 性能与可访问性 | 不劫持滚动条、不改 CSS transform、不 hack 滚轮；`prefers-reduced-motion` 下建议直接禁用实例；与 ScrollTrigger 需 `scrollerProxy` 桥接；**局部滚动容器（如仪表盘内部滚动区）需 `content`/`wrapper` 指定或跳过** |
| 评级 | ★★★★☆ — 业界标准 + 官方 Vue 支持 + 极小，滚动叙事质感提升明显；但对纯单屏 Bento 首页收益有限，属"锦上添花" |

**落地映射（首页 Bento）：**
- 首页若保持"首屏即仪表盘 + 向下滚动更多 widget 分区"的结构，Lenis 让整页滚动丝滑，与 ScrollTrigger/scroll-driven reveal 同步更精准。
- 若首页固定视口不滚动：**不引入 Lenis**（仪表盘内部用原生 overflow 滚动即可，避免平滑滚动 + 拖拽的兼容成本）。

---

## 4. View Transitions API — 零依赖页面/元素转场

| 项 | 内容 |
|---|---|
| 名称 / 类别 | View Transitions API（浏览器原生）· 快照式转场 |
| 官方链接 | https://developer.chrome.com/docs/web-platform/view-transitions（MDN: ViewTransition） |
| npm 包 | 无（浏览器 API）；辅助封装可选 `vue-view-transitions`（v1.2.1，MIT，2024-02 发版，维护一般）；或 **Motion 12.42+ 的 `animateView()`（免费进 core）** 修复其粗糙边缘 |
| 成熟度 | caniuse 全球 **88.47%**：Chrome/Edge 111+、Safari 18.0+、Firefox 144+（2025 底补齐）→ 2026 年完全可用 |
| 社区热度 | MDN/Chrome 博客常客；Motion 官方发文《A View Transition API for the rest of us》；Nuxt/Vue 社区封装活跃 |
| 代表案例 | Chrome 官方演示（十字图片共享过渡）、Chrome/ChromeOS 文档站、大量 SPA 转场 demo |
| Vue 3 集成 | 手写 ~20 行封装：路由 afterEach/组件内 `document.startViewTransition(() => flushSync/nextTick)` + CSS `::view-transition-old/new` 与 `view-transition-name` 定制；或 `vue-view-transitions` 包；Vue Router 4.5+/5.x 无内建，需自己包一层 |
| 性能与可访问性 | 零 JS 体积；转场默认捕获整个视口快照（内存/GPU 开销），建议限定 `view-transition-name` 到少数元素；`prefers-reduced-motion` 时浏览器可跳过或自定义 CSS 关闭；Safari 早期版本（18.0-18.2）有历史记录 bug，现版本已修 |
| 评级 | ★★★★☆ — 2026 年浏览器全覆盖 + 零依赖，页面转场与卡片展开的"原生电影感"首选 |

**落地映射（首页 Bento）：**
- **转场层**：路由切换（Home ↔ 其它视图）用 `startViewTransition` 做整页淡入上移或"仪表盘网格"十字聚合过渡。
- **widget 层**：Bento 卡片点击展开详情时给卡片一个 `view-transition-name`，展开/收起变成连续动画（比 layout 动画更便宜且可与 motion-v 并存）。
- 注意：若同时用 motion-v 的 `AnimatePresence`，把 VT 留给"跨路由/跨页面"级，widget 内部用 motion-v，避免双重转场。

---

## 5. Vue `<Transition>` / `<TransitionGroup>` 高级用法 — 零成本基线

| 项 | 内容 |
|---|---|
| 名称 / 类别 | Vue 3 内置转场原语 · 框架自带 |
| 官方链接 | https://cn.vuejs.org/guide/built-ins/transition.html |
| npm 包 | 无（内置） |
| 成熟度 | Vue 3.5 稳定内置；TransitionGroup 底层即 FLIP（transform 位移），性能好 |
| 社区热度 | 所有 Vue 项目默认能力；VueUse 的 `useTransition` 可配数字滚动 |
| Vue 3 集成 | `<Transition>`（单元素进出场，支持 `mode="out-in"`、JS hooks、动态 `name`、`v-if/v-show`）；`<TransitionGroup>`（列表增删/重排，`move` 类做 FLIP）；与 v-for + key 天然配合 |
| 性能与可访问性 | 零体积；CSS transition/动画走合成器；`prefers-reduced-motion` 可在 CSS 媒体查询里关停；JS hooks 时注意 `done()` 时序 |
| 评级 | ★★★★☆ — 必须会用且免费的基线：widget 开关、列表增删、胶囊切换先用它，复杂手势/滚动叙事再上 motion-v/GSAP |

**落地映射（首页 Bento）：**
- **widget 层**：CapsuleNavigation 用 `<Transition>` 滑动指示器（绝对定位元素 + `transform`）；widget 展开/收起面板进出场。
- **交互层**：快捷入口涟漪、搜索框展开用 `v-show` + Transition 的 `enter/leave` 类。
- **结合**：`<TransitionGroup>` 包 Bento 网格的增删（搭配 vuedraggable 事件），`move` 动画让布局变化不跳变。

---

## 6. CSS scroll-driven animations（animation-timeline） — 零 JS 滚动动画

| 项 | 内容 |
|---|---|
| 名称 / 类别 | CSS 原生滚动驱动动画 · 纯 CSS |
| 官方链接 | MDN: animation-timeline / scroll() / view() |
| npm 包 | 无 |
| 成熟度 | caniuse 全球 **83.66%**：Chrome 115+/Edge 115+（2023）、Safari 26+（2025）、**Firefox 156+（2026 才支持）**、Opera 101+ |
| 社区热度 | Chrome DevRel 力推；2024-2026 前端趋势榜单常客；配合 `@supports` 做渐进增强 |
| 代表案例 | Chrome 官方 scroll-driven 演示站、bram.us/CSS-Tricks 大量教程 demo |
| Vue 3 集成 | 纯 CSS：Tailwind 里写 `animation-timeline: scroll(root block);` 或自定义 `@keyframes` + `view()`；JS 侧仅需判断 `CSS.supports('animation-timeline: scroll()')` 决定是否给元素加类 |
| 性能与可访问性 | 零 JS、走浏览器合成管线，性能最佳；支持率缺口（老 Safari 19-25 / Firefox <156）用 `@supports` 回退到无动画；`prefers-reduced-motion` 同样适用 |
| 评级 | ★★★☆☆ — 零成本但支持率仍有 16% 缺口、且仪表盘本身滚动场景少；适合做"顶部滚动进度条/装饰视差"等点缀 |

**落地映射（首页 Bento）：**
- **背景层**：页面滚动进度条（`animation-timeline: scroll()`）；背景光晕随滚动平移（纯 CSS）。
- **widget 层**：向下滚动进入各 widget 分区时用 `animation-timeline: view()` 做渐显（替代部分 ScrollTrigger 职责，省 15KB）。
- 前提：首页有纵向滚动叙事才值得；否则可整段忽略。

---

## 7. @vueuse/motion — Vue 生态传统选（维护放缓）

| 项 | 内容 |
|---|---|
| 名称 / 类别 | @vueuse/motion · Vue 声明式动效（指令 + composable） |
| 官方链接 | https://motion.vueuse.org · https://github.com/vueuse/motion |
| npm 包 | `@vueuse/motion`（v3.0.3，2025-03 发版） |
| 成熟度 | 周下载 **16.82 万**；GitHub 2,753★；**维护放缓信号：GitHub 最后 push 2025-03-11（>16 个月）**，依赖 `@vueuse/core ^13`（当前 14.x），底层仍是 popmotion/framesync（已被 Motion 引擎取代的旧栈） |
| 社区热度 | VueUse 品牌背书、Nuxt 支持；但功能面被 motion-v 覆盖，社区重心已转移 |
| 代表案例 | 官方 playground 演示（v-motion 指令）；部分 Nuxt 站点 |
| Vue 3 集成 | `v-motion` 指令（`:initial/:enter/:hovered`）、`useMotion`/`useSpring` composable、全局插件注册 |
| 性能与可访问性 | 走 transform/opacity 合成；依赖 popmotion 体积 ≈15KB gzip；无内置 reduced-motion hook（需自行判断） |
| 评级 | ★★★☆☆ — 历史上 Vue 首选，但已进入维护放缓期且与 motion-v 功能重叠；**新代码建议直接 motion-v，已有引入可暂留** |

---

## 8. Locomotive Scroll — 被 Lenis 吸收的前代方案

| 项 | 内容 |
|---|---|
| 名称 / 类别 | Locomotive Scroll · 平滑滚动 + data-scroll parallax 快捷层 |
| 官方链接 | https://scroll.locomotive.ca |
| npm 包 | `locomotive-scroll`（v5.0.1） |
| 成熟度 | 周下载仅 **1.55 万**（远低于 lenis 的 127 万）；GitHub 8,836★；**v5 底层依赖 lenis 1.3.17**（官方站承认 "powering libraries like Locomotive Scroll"），即已是 Lenis 的封装壳 |
| 社区热度 | 历史辉煌（2016-2021 Awwwards 常见），现已被 Lenis 替代叙事 |
| 代表案例 | 旧版站点（多为 2019-2022 时代） |
| Vue 3 集成 | `data-scroll` 属性 + `data-scroll-speed` 快速做视差；需自封装 init/destroy |
| 性能与可访问性 | 与 lenis 同底层；`data-scroll` 额外做元素检测有开销；混合滚动容器兼容需小心 |
| 评级 | ★★☆☆☆ — 仅当想"用属性快速堆 parallax"才考虑；新项目直接 Lenis + motion-v/GSAP 自行绑定，更可控 |

---

## 9. Framer Motion — React 对照参考（不引入）

| 项 | 内容 |
|---|---|
| 名称 / 类别 | Framer Motion（现并入 Motion 生态）· React 专属声明式动画 |
| 官方链接 | https://motion.dev/docs/react（即 motion/react） |
| npm 包 | `framer-motion`（v12.43.0，deprecated 但仍是 motion 内部依赖名） |
| 成熟度 | 与 motion 同源（Motion 是它的新名字）；React 生态头部库 |
| Vue 对照 | Vue 无官方 framer-motion；但 **motion-v 已把同一套 API 移植到 Vue**（`<motion.div>`、variants、layoutId、AnimatePresence、useScroll 全部等价），所以"Framer Motion 式体验"在 Vue 侧请用 motion-v |
| 评级 | ★★☆☆☆（对本项目）/ 作为 API 参照 ★★★★☆ — 不要直接引入 React 库；要它的体验就用 motion-v |

---

## 10. 横向对比与决策速查

| 候选 | 类型 | Vue3 集成 | 周下载 | 体积(gzip) | 维护 | 首页契合 | 评级 |
|---|---|---|---|---|---|---|---|
| **motion-v** | 引擎(声明式) | 一等公民 | 60.2 万 | ~8-15KB | 活跃 | ★★★★★ | ★★★★★ |
| **GSAP+ScrollTrigger** | 引擎(命令式+滚动) | context 手动 | 443 万 | core 23KB+ST 15KB | 活跃 | 精品定制 | ★★★★☆ |
| **Lenis** | 平滑滚动 | 官方组件 | 127 万 | <4KB | 活跃 | 滚动叙事 | ★★★★☆ |
| **View Transitions API** | 原生转场 | 手写封装 | — | 0 | 浏览器标准 | 页面/widget转场 | ★★★★☆ |
| **Vue Transition/Group** | 原生转场 | 内置 | — | 0 | 框架自带 | 基线 | ★★★★☆ |
| **@vueuse/motion** | 引擎(声明式) | 一等公民 | 16.8 万 | ~15KB | 放缓⚠️ | 中 | ★★★☆☆ |
| **CSS scroll-driven** | 纯CSS动画 | 无 | — | 0 | 标准(84%) | 点缀 | ★★★☆☆ |
| **Locomotive Scroll** | 平滑滚动壳 | 自封装 | 1.55 万 | ~8KB | 低 | 低 | ★★☆☆☆ |
| **Framer Motion** | React 对照 | ✗ | — | — | 活跃 | 不适用 | ★★☆☆☆ |

**组合建议（推荐栈）：**
`motion-v`（widget/交互/入场，全站主力）+ `View Transitions API` 封装（跨路由/大元素转场，零依赖）+ `Vue Transition/TransitionGroup`（组件内基线）→ 若做滚动叙事再按需懒加载 `lenis` + `gsap/ScrollTrigger`（仅首页 chunk）。

**落地分层（Bento 仪表盘）：**

| 层 | 职责 | 首选 | 备选 |
|---|---|---|---|
| 背景层 | 光晕缓移、粒子、滚动进度 | CSS scroll-driven / ECharts | GSAP Observer |
| widget 层 | 卡片交错浮现、展开/收起、增删 FLIP | motion-v（stagger/layoutId） | TransitionGroup + vuedraggable |
| 交互层 | hover lift、press、磁吸、数字滚动 | motion-v gestures + useSpring | GSAP + CustomEase |
| 入场动效 | GreetingBar 文本逐字、仪表盘整体入场 | GSAP SplitText（按需懒加载） | motion-v variants（无逐字） |
| 页面转场 | 路由切换、胶囊切换 | View Transitions API + Vue Transition | AnimatePresence(motion-v) |

---

## 11. 关键注意点（工程约束）

1. **ECharts 共存**：动画只作用于图表容器（opacity/transform），不碰 canvas 内部帧；motion-v 的 WAAPI 与 ECharts 自带动画互不干扰。已有 `html2canvas`（导出）时避免在快照瞬间让 widget 处于 mid-animation（可用 reduced-motion 或强制 finish）。
2. **vuedraggable 共存**：拖拽动画由 sortable 自己管；`layout`/Flip 动画只加给"非拖拽中的布局变更"，二者勿同时驱动同一元素 transform。
3. **Storybook / vitest**：motion-v、GSAP 在 jsdom 下需 `matchMedia` polyfill 与 rAF stub（vitest 用 `vi.stubGlobal` 或 `happy-dom`）；ScrollTrigger 需 mock `window.scrollY`/`ResizeObserver`。
4. **prefers-reduced-motion**：motion-v 用 `useReducedMotion()`，GSAP 用 `gsap.matchMedia()`，View Transitions 在媒体查询里关 CSS，Lenis 直接不实例化。
5. **懒加载**：首页才用的 `gsap`/`lenis` 走 `import()` 动态加载（Vite 自动分包）；`motion-v` 全局注册但同样 tree-shake 按组件引入。
6. **许可**：GSAP 是"Standard no-charge"非 OSI 开源许可（免费但非 MIT）；motion-v/lenis/VT API 均为 MIT/开放标准。若团队有严格 OSI 合规要求，GSAP 需法务确认。

---

## 附：本次联网验证来源清单

- GitHub API：motiondivision/motion（33,059★）、vueuse/motion（2,753★）、darkroomengineering/lenis（15,238★）、locomotivemtl/locomotive-scroll（8,836★）、productdevbook/motion 归档状态、greensock/GSAP src+dist 文件清单
- npm registry：gsap@3.15.0、motion@12.43.0、motion-v@2.3.0、@vueuse/motion@3.0.3、lenis@1.3.25、locomotive-scroll@5.0.1、@motionone/vue（deprecated）、vue-view-transitions@1.2.1、@vueuse/core@14.4.0、vue-router@5.2.0
- npm downloads API（2026-07-27→08-02 周下载）：gsap 4,429,724 / motion 17,260,659 / motion-v 601,898 / @vueuse/motion 168,194 / lenis 1,270,782 / locomotive-scroll 15,480
- caniuse：animation-timeline 83.66%（FF156 才支持）、ViewTransition 88.47%
- 官网：motion.dev（确认官方 Vue 文档 /docs/vue 与 motion-v 安装）、lenis.dev（<4KB、Vue 支持、案例列表）、gsap.com/showcase（案例 URL）
- 未联网验证（基于已知知识）：Framer Motion 具体案例站、Vue Transition API 细节、部分案例站内部实现归属
