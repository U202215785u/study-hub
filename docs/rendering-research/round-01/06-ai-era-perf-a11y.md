# Round 01 · 主题域调研：AI 时代范式 + 性能与可访问性

> 目标项目：Study-Hub（Vue 3.5 + Vite 5 + Tailwind 3.4 + ECharts + Storybook 8.6，首页为 Bento 网格仪表盘，含热力图/日历/任务等 widget）
> 调研日期：2026-08（GitHub star / npm 版本与下载量 / web.dev 指南 / Awwwards 评审页均已联网验证；标注"未联网验证"的为基于已知业界知识的判断）
> 结论诉求：每个候选技术落到「首页 Bento 仪表盘怎么用」（背景层 / widget 层 / 交互层 / 入场动效），并明确哪些炫酷方案必须配降级策略

---

## 0. 全景候选池与硬数据（联网验证）

| 候选 | 类别 | GitHub ⭐ | npm 包 @ 版本 | 周下载量 | 许可 | 最近提交 | 数据来源 |
|---|---|---|---|---|---|---|---|
| **Three.js（WebGPURenderer/TSL）** | WebGPU 渐进 3D | 114,224 | `three@0.185` | ~1,380 万 | MIT | 2026-08 极活跃 | GitHub API |
| **@vueuse/motion** | Vue 动效 composable | 2,753 | `@vueuse/motion@3.0.3` | 168,194 | MIT | 2025-03（维护放缓） | GitHub+npm API |
| **tsParticles** | 粒子/魔法背景 | 8,938 | `tsparticles@4.x` | 103,153 | MIT | 2026-08 极活跃 | GitHub+npm API |
| —（tsParticles Vue3 封装） | — | — | `@tsparticles/vue3@4.3.2`（peer: vue ^3） | 7,370 | MIT | 2026-08 | npm registry |
| **shadcn-vue（unovue）** | Vue 组件生态 | 10,380 | 复制粘贴模式（registry） | — | MIT | 2026-08 活跃 | GitHub API |
| **inspira-ui（unovue）** | Vue 炫酷组件（Aceternity 风格） | 4,870 | 复制粘贴模式 | — | MIT | 2026-07 活跃 | GitHub API |
| **Magic UI** | 炫酷组件（React） | 21,783 | 复制粘贴模式（React+framer-motion） | — | MIT | 2026-07 活跃 | GitHub API |
| **Aceternity UI** | 炫酷组件（React，无公开主仓库） | 官方 org 仅 2 个模板仓 | 复制粘贴模式 | — | — | — | GitHub API |
| **vue-vben-admin** | Vue3+shadcn-ui 生态标杆 | 33,031 | — | — | MIT | 2026-07 活跃 | GitHub API |
| **wgpu-matrix** | WebGPU 数学库 | 473 | `wgpu-matrix@0.x` | — | MIT | 2026-02 | GitHub API |
| **canvaskit-wasm（CanvasKit）** | Skia WASM 浏览器渲染 | —（Skia 仓库内） | `canvaskit-wasm@0.41.1` | — | BSD-3-Clause | 发布活跃 | npm registry |
| **skia-canvas（Node）** | Skia 服务端渲染 | 2,590 | `skia-canvas@3.0.8` | — | MIT | 2025-09 | GitHub API |
| **WebGPU（平台能力）** | GPU API | MDN：**非 Baseline / Limited availability**，仅 secure context | — | — | 规范 | 2026-05 MDN 更新 | MDN |
| **WAAPI + scroll-driven** | 原生动画 API | 全浏览器支持 | 浏览器原生 | — | — | — | 已知知识（未逐一联网验证） |
| **Playwright 无头 WebGL** | 测试策略 | — | — | — | — | — | 已知知识（未联网验证） |

**与现有依赖冲突检查**：现依赖 echarts 5.5 / markmap / vuedraggable / html2canvas 均与上述候选无全局状态冲突。tsParticles/CanvasKit/three 各自持有独立 canvas；唯一注意点同第一轮：全站保持单一 WebGL context（背景层一个 canvas），多个 WebGL context 会撞浏览器上限（约 8–16 个）并增加 GPU 内存。

---

## 1. 候选技术详情（a 部分：新兴范式）

### 1.1 Web Animations API（WAAPI）全面化 —— 零依赖动效底座 ⭐⭐⭐⭐⭐

- **官方**：https://developer.mozilla.org/docs/Web/API/Web_Animations_API / web.dev 动画系列（已抓取 animations-guide、prefers-reduced-motion）
- **成熟度**：`element.animate()` 自 2020 年起全主流浏览器支持（Chrome 84 / Firefox 75 / Safari 13.1）；2023+ 新增 **scroll-driven animations**（scroll-timeline，Chrome 115+，Safari/Firefox 逐步跟进）与 `@scroll-timeline`；不需要任何库。
- **社区热度**：web.dev 将其与 CSS 动画并列为首选方案；Motion One / GSAP 等库底层均提供 WAAPI 兼容；无需维护依赖。
- **代表性案例**：web.dev animations-guide（已抓取，含官方 CodePen 对照 demo）；MDN 官方 guide。
- **Vue 3 集成**：在 `onMounted` 里 `el.animate(keyframes, options)`，`onUnmounted` 里 `animation.cancel()`；与 Vue `<Transition>`/`<TransitionGroup>` 可共存（JS hooks 里直接调 WAAPI 或 CSS）。封装成 `useWaapiAnimation(elRef, keyframes)` composable 即可。
- **性能与可访问性**：WAAPI 动画跑在 compositor 线程（transform/opacity），主线程零占用 → 对 INP 友好；`prefers-reduced-motion` 时直接不调用 `animate()` 或在 mediaQuery change 时 `cancel()`（web.dev 原文示例）；`animation.pause()` 可随时停。
- **评级 ★★★★★**：零依赖、全浏览器、天然 off-main-thread，是 Bento 里所有"小动效"的最省事底座。

### 1.2 @vueuse/motion —— Vue 生态的声明式动效层 ⭐⭐⭐⭐⭐

- **官方**：https://motion.vueuse.org / https://github.com/vueuse/motion
- **成熟度**：2.7k ⭐、`@vueuse/motion@3.0.3`、周下载 **16.8 万**、MIT、`sideEffects:false`（可 tree-shaking）、unpacked 仅 ~90KB；底层用 popmotion（spring/惯性/时间轴）。⚠️ 最近一次提交 2025-03，维护节奏放缓但仍可用。
- **社区热度**：VueUse 官方家族（antfu 团队维护），Nuxt module 同包提供；168k 周下载在 Vue 动效库中一骑绝尘。
- **代表性案例**：motion.vueuse.org 官方 playground；Nuxt 生态大量落地（未联网验证具体站点）。
- **Vue 3 集成**：`v-motion` 指令直接上模板，或 `useMotion()` composable；Vue 3.5 完全兼容；不引第三方运行时依赖。
- **性能与可访问性**：默认驱动 transform/opacity，compositor 友好；`useReducedMotion`/`useMotion` 可读系统偏好并在动画前短路（需自己接线）；指令式写法让"禁用动效"只需一个全局条件。
- **评级 ★★★★★**：Bento 卡片入场/悬停/hover 光效的唯一首选封装，体积小、API 简单、和 Vue 3.5 同源生态。

### 1.3 tsParticles 新生态（@tsparticles/engine + Vue3 封装）—— 魔法背景 ⭐⭐⭐⭐

- **官方**：https://particles.js.org / https://github.com/tsparticles/tsparticles
- **成熟度**：8.9k ⭐、v4.x、MIT、2026-08 极活跃；monorepo 提供 Vue 2/3、React、Svelte、Web Components 等封装；`@tsparticles/vue3@4.3.2` peer 依赖 `vue ^3` + `@tsparticles/engine@4.3.2`，与项目 Vue 3.5 匹配。
- **社区热度**：周下载 tsparticles 10.3 万 / vue3 封装 7,400；中文社区曾有大量 particles.js 教程，v4 生态延续度高（已知信息）。
- **代表性案例**：particles.js.org 官方 demo（含 confetti/fireworks 主题）；无数 Awwwards 风格粒子背景站（未联网验证具体 URL）。
- **Vue 3 集成**：`<Particles :options="..." />` 组件即用；或仅 `import { tsParticles } from '@tsparticles/engine'` 手动挂到 canvas。体积靠按需导入 presets/插件裁剪。
- **性能与可访问性**：canvas 2D 渲染，粒子数可配置（几千粒 60fps 无压力）；`prefers-reduced-motion` 时 `particles.destroy()` 落回 CSS 渐变；WebGL 非必需（2D canvas 兜底天然存在）；canvas `aria-hidden`。
- **评级 ★★★★**：粒子/魔法背景最省心的现成方案，但"粒子背景"本身已趋于同质化，创意上不如上一轮 regl shader 方案新颖。

### 1.4 WebGPU：Three.js WebGPURenderer + TSL / wgpu-matrix / Babylon WebGPU ⭐⭐⭐⭐（渐进增强，不裸用）

- **官方**：https://threejs.org（WebGPURenderer 自 r163+ 逐步稳定，TSL 自 r162+ 可用，未联网验证具体小版本号）/ https://github.com/toji/wgpu-matrix / https://www.babylonjs.com
- **成熟度**：**WebGPU 本身仍是"Limited availability"（MDN 明示非 Baseline）**，仅 secure context；三个事实：① 桌面 Chrome/Edge/Safari 16.4+/Firefox 141+ 已支持（未逐版本联网验证，按已知知识标注）；② 移动端 Safari 支持但功耗策略保守；③ three/Babylon 都提供 WebGPU→WebGL2 自动/手动回退。
- **社区热度**：three 114k ⭐ 仍是业界 3D 底座；Bruno Simon folio-2025（第一轮已验证）用 TSL 同时跑双后端；`wgpu-matrix` 仅 473 ⭐（greggman 维护、2026-02 有提交）——是"自写 WebGPU"而非"直接用 three"时才需要。
- **代表性案例**：https://webgpu.github.io/webgpu-samples（官方样例，MDN 收录）；MDN render/compute demo（已收录于 MDN 页面）。
- **Vue 3 集成**：与 three 系集成路径一致（见第一轮 TresJS 封装）；关键点是在初始化时先 `navigator.gpu?.requestAdapter()` 探测，不可用则直接用 WebGLRenderer——**同一套场景代码双后端**（three TSL 正是为此设计）。
- **性能与可访问性**：WebGPU 对仪表盘级场景的收益主要在"超多实例粒子/后处理/计算着色器"，纯装饰背景用 WebGL 已够；GPU 内存需 `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))` + 监听 `device.lost`/context lost 重建；`prefers-reduced-motion` 时停 rAF。
- **评级 ★★★★**：值得在背景层预留"WebGPU 增强位"，但首版用 WebGL2 起跑、WebGPU 作为渐进增强，避免把非 Baseline 技术做成硬依赖。

### 1.5 CanvasKit / Skia（WASM 渲染）：canvaskit-wasm + skia-canvas（Node） ⭐⭐⭐

- **官方**：https://github.com/google/skia/tree/main/modules/canvaskit / https://skia-canvas.org
- **成熟度**：`canvaskit-wasm@0.41.1`，BSD-3，Google 维护，发布活跃；unpacked **25.5MB（含 wasm 二进制，实际 gzip 传输约 1–2MB 量级，未实测）**；`skia-canvas@3.0.8`（2025-09）是 **Node 端** Skia 绑定。
- **社区热度**：CanvasKit 被 Flutter Web/Figma 级渲染使用；但作为"前端项目引入的运行时"在小团队中不算主流（已知信息）。
- **代表性案例**：Figma/Skia 自家产品（未联网验证）；Flutter Web 底层（已知信息）。
- **Vue 3 集成**：浏览器端 `await CanvasKitInit()` 动态加载 wasm；Node 端（skia-canvas）用于 **SSR/构建期生成高质量 SVG/PNG 图表**，比如把热力图预渲染成图片——但这与"前端实时渲染"诉求错位。
- **性能与可访问性**：WASM 初始化几十~上百 ms + wasm 体积，对 LCP 是负担，必须动态 import 且非首屏；GPU 加速（WebGL 后端）但通常用于离屏绘制再回贴。**对本项目属于"杀鸡用牛刀"**。
- **评级 ★★★**：只有当未来需要"构建期用 Skia 离屏渲染海报图/OG 图"时才引入 Node 版；浏览器端 CanvasKit 不建议进首页运行时。

### 1.6 AI 生成视觉（动态壁纸/纹理/视频背景）—— 工作流范式，无固定库 ⭐⭐⭐⭐

- **官方**：Midjourney / 即梦 / Flux / Recraft 等生图工具（未联网验证具体产品状态，按 2025–2026 已知趋势标注）
- **成熟度**：设计侧成熟；落地方式分三类：
  1. **AI 生成静态纹理/渐变资产 + 运行时动效**（推荐）：用 AI 产出高质感背景图（噪点、胶片颗粒、水墨、玻璃拟态底纹），浏览器端用 CSS/粒子/视差给它"活起来"——Awwwards 2026 SOTD 大量这类"AI 底 + WebGL 叠加"的站点。
  2. **AI 生成 loop 视频做首屏背景**：`<video muted autoplay loop playsinline poster>`，`prefers-reduced-motion` 时只显示 poster；必须懒加载 + `loading="lazy"`/`preload="none"`。
  3. **AI 生成数据插画**：作为 widget 内的装饰插画（SVG 化后体积小）。
- **代表性案例**：Awwwards WebGL/3D 榜单中的 AI 风格站点（已抓榜单页，如 Noomo Showcase、Grainient v2 的颗粒纹理方向）；"AI 壁纸"类产品（未联网验证）。
- **性能与可访问性**：静态纹理是**天然的降级兜底**（不需要 WebGL 也好看）；视频背景是 LCP/TTFB 杀手，只能放 hero 且必须 `poster` 兜底；纹理性资产注意 gzip（PNG→WebP/AVIF，或转 CSS 渐变代码）。
- **评级 ★★★★**：成本最低、最不依赖运行时重渲染的"AI 味"方案，与性能底线天然兼容。

### 1.7 炫酷组件生态：Aceternity UI / Magic UI / shadcn-vue / inspira-ui（中文社区热度专项） ⭐⭐⭐

- **Aceternity UI**（https://ui.aceternity.com）：**官方没有公开主仓库**（aceternity org 仅有 saasternity/nextjs-boilerplate 两个模板仓），组件走"复制粘贴"模式、React 专属。**中文社区热度信号（已验证）**：bilibili 搜索 "Aceternity UI" 仅命中 1 个直接相关视频（程序猿DD，2024-03，**2,873 播放 / 0 弹幕**）→ 中文圈热度很低，基本停留在"翻墙看到国外作品"层面。
- **Magic UI**（https://magicui.design）：21.8k ⭐、MIT、**React + framer-motion 专属**，复制粘贴模式。**中文社区热度信号（已验证）**：bilibili 搜索 "Magic UI 组件库" 被荣耀 MagicOS 的"Magic UI"完全淹没，无任何组件库相关内容 → 中文圈几无专门讨论。
- **shadcn-vue**（https://shadcn-vue.com，10.4k ⭐）：Vue 版 shadcn，radix-vue 底座，复制粘贴模式；**中文热度信号**：vue-vben-admin（33k ⭐，中文社区项目）已全面采用 shadcn-ui 组件 → 中文 admin 生态实际上已经重度拥抱 shadcn 系。
- **inspira-ui**（https://inspira-ui.com，4.9k ⭐）：unovue 出品的 **Vue/Nuxt 版 Aceternity 风格组件**（aurora 背景、粒子、数字翻转等），是本项目真正可抄的 Vue 对应物。
- **Vue 3 集成**：Aceternity/Magic UI **无法直接使用**（React + JSX + framer-motion），只能移植思路；shadcn-vue/inspira-ui 直接复制组件文件进项目（Tailwind 3.4 兼容，shadcn-vue 支持 Tailwind v3/v4，inspira-ui 文档倾向 v4 需注意）。
- **性能与可访问性**：这类库**常见性能坑**（GitHub 上有中文开发者 repo 直言"漂亮但卡"——搜到 andrey-kudinov/aceternity 描述 'Красиво но забаговано и тяжеловато по перфомансу'）；复制进项目后体积可控，但动画用 framer-motion 移植到 Vue 时容易变笨重。
- **评级 ★★★**：思路可抄（尤其 inspira-ui 的 aurora/粒子类组件），但 React 系生态在 Vue 项目里是"参考值"，且原生组件普遍不处理 `prefers-reduced-motion`，接入时需自己补。

---

## 2. 底线标准（b 部分：可直接套用的数字与规则）

> 以下 CWV 阈值、动画性能与 reduced-motion 建议均来自已抓取的 web.dev 官方页；包体积预算为业界常见做法（标注未联网验证具体出处）。

### 2.1 Core Web Vitals 预算（web.dev/vitals 已抓取）
| 指标 | 良好阈值 | 判定口径 |
|---|---|---|
| **LCP** | **< 2.5s**（p75） | 首屏大内容（本项目=Bento hero 区/首屏文本） |
| **INP** | **≤ 200ms**（200–500 需改进，>500 差；p75） | 点击/触摸/键盘交互；长任务 >50ms 是元凶 |
| **CLS** | **< 0.1**（p75） | 动画禁止用 layout-inducing 属性 |

### 2.2 包体积预算（gzip）
- **业界常见参考**（未联网验证出处，按已知实践标注）：WebPageTest/HTTP Archive 建议 **关键 JS gzip ≤ 170–200KB**、Lighthouse TBT ≤ 200ms、全页传输 ≤ 1.5MB gzip。
- **本项目建议硬预算**：首屏关键 JS **gzip ≤ 250KB**（Vue 3.5 + router + 首页必需代码已占大头）；任何炫酷渲染库（three/tsParticles/CanvasKit）一律 **`defineAsyncComponent` 动态 import + 路由级懒加载**，禁止进首屏主包；ECharts 按需注册（现有代码已按模块引）。

### 2.3 GPU 内存 / 帧率
- **帧率目标**：装饰动画 ≤ 2 个同时运行的连续动效时保持 60fps（DevTools FPS meter 掉帧率 ≥99% 帧为佳，web.dev 指南）；交互触发的动效应在 200ms 内给出下一帧反馈。
- **GPU 内存规则**：`setPixelRatio(Math.min(devicePixelRatio, 2))`；纹理总尺寸 ≤ 4096²/4096²；**全站单一 WebGL context**（背景层一个 canvas，widget 合场景或按需销毁）；监听 `webglcontextlost` / `device.lost` 并重建或降级；`visibilitychange` 隐藏时 `setAnimationLoop(null)` 停 rAF 省电省显存。

### 2.4 prefers-reduced-motion（web.dev 已抓取）
- 全浏览器支持（Chrome 74+ / Safari 10.1+ / Firefox 63+ / Edge 79+）。
- **CSS**：动画类单独提文件，`<link media="(prefers-reduced-motion: no-preference)">` 条件加载，或全局 `animation-duration: 1ms !important` override 兜底。
- **JS**：`matchMedia('(prefers-reduced-motion: reduce)')` + `change` 事件监听，动画启动前短路、进行中 cancel；`@vueuse/motion`/three/rAF 循环都要走这条线。
- **客户端提示**：`Sec-CH-Prefers-Reduced-Motion` 可在请求期就下发正确 CSS（web.dev 原文）。
- **静态图兜底**：`<picture><source media="(prefers-reduced-motion: no-preference)" srcset="动图.webp">` + 静态 `<img>`（web.dev 原文示范，对 AI 视频/动图背景直接套用）。

### 2.5 canvas/webgl 降级链（按顺序）
```
prefers-reduced-motion: reduce  →  直接给静态/无动画版本（CSS 渐变、静态纹理、静态图表）
WebGL/WebGPU 不可用           →  Canvas 2D 实现（tsParticles 天然支持）或 CSS 装饰
canvas API 不可用（老环境）    →  CSS 背景渐变 + 静态纹理
CI/无头/测试环境              →  占位 div + 功能渲染照常（见 2.7）
```
任何炫酷效果**必须**在架构上保证"没有它依然是一张好看的首页"。

### 2.6 Awwwards 评审标准（awwwards.com/about-evaluation 已抓取）
| 维度 | 权重 | 对本项目的启示 |
|---|---|---|
| **Design（设计）** | **40%** | Bento 视觉层次、留白、色彩系统是第一优先 |
| **Usability（可用性）** | **30%** | 交互反馈速度（INP）、导航明确、内容可读 |
| **Creativity（创意）** | **20%** | 新颖动效/3D/粒子是加分项，但只占两成 |
| **Content（内容）** | **10%** | 数据叙事（热力图/学习数据）本身是内容 |
- 判定规则：荣誉奖 HM ≥ 6.5 分；SOTD 由 ≥18 位评审投票（去极值 3 票）；Developer Award 需代码维度 ≥7（有公开的 Developer Guidelines 文档链接）→ **炫酷渲染要服务于设计，且不得牺牲可用性**。

### 2.7 无头浏览器 / CI 下的渲染策略（基于已知知识，未联网验证）
- **jsdom（Vitest）**：无 canvas/WebGL → 渲染组件需探测 `canvas.getContext('webgl')` 返回 null 时渲染占位（`data-fallback` div），快照/断言只依赖占位结构。
- **Playwright（Chromium new headless）**：支持 WebGL，通过 **SwiftShader 软件光栅化**，视觉测试/截图可用但**帧率与显存不代表真实硬件**；`prefers-reduced-motion: reduce` 可在 launch 时 `context.emulateMedia({ reducedMotion: 'reduce' })` 统一注入，保证截图稳定。
- **E2E 断言策略**：动画断言一律"结局态"（`waitFor` 到静态值/类名），不要断言动画中间帧。

---

## 3. 落到首页 Bento 仪表盘：怎么用

### 3.1 背景层
- **方案 A（首选，零重引擎）**：`BentoBackground.vue` = **AI 生成静态纹理/颗粒底图（WebP/AVIF，gzip 友好）+ CSS 渐变 + 慢速视差**；`prefers-reduced-motion` 时视差停掉只剩静态底 → 天然达标。用 @vueuse/motion 或 WAAPI 做视差 lerp。
- **方案 B（想要会"呼吸"的粒子/星云）**：tsParticles（canvas 2D 后端）做轻量粒子，`@tsparticles/vue3` 组件 + 按需 preset；粒子数预算 ≤ 3000，DPR 限 2；`reduced-motion` 时 destroy 落回 CSS 渐变。
- **方案 C（进阶，承接第一轮）**：TresJS/three 全屏背景，**WebGPU 作为渐进增强位**（`navigator.gpu` 可用则 `WebGPURenderer`，否则 WebGLRenderer 双后端同场景），不阻塞首版。
- **明确不做**：CanvasKit/浏览器端 wasm 渲染做背景（初始化成本 + 25MB 包）、AI 生成视频做整页背景（LCP 杀手）。

### 3.2 widget 层
- 组件库：**shadcn-vue** 统一 Bento 卡片基础样式（已在中文 admin 生态验证过），**inspira-ui** 抄"aurora/spotlight/border-beam"等 Aceternity 风格卡片光效（复制 Tailwind 组件文件即可，注意 Tailwind 版本适配）。
- **Aceternity / Magic UI 原库不引入**（React 专属），只把设计语言移植成 Vue/Tailwind 实现。
- 热力图 widget：数据可视化保持 ECharts（现依赖），可用 WAAPI 给柱体/色块加"点亮"过渡（compositor 线程，零 INP 风险）；不做 3D 化（已由第一轮覆盖，本轮强调其必须有 reduced-motion 静态版）。

### 3.3 交互层
- 卡片 hover：`@vueuse/motion`（spring 弹簧感 + transform/opacity），`useReducedMotion()` 短路；hover 光效跟随鼠标用 `--x/--y` CSS 变量（`transform: translate()` 驱动，不触发 layout）。
- 滚动联动：若首页有滚动，用 **WAAPI scroll-driven animations**（scroll-timeline）做 widget 视差/淡入，避免 JS scroll 监听 → 顺带降 INP。
- 禁做：hover 时的 margin/width/top/left 动画（会打爆 CLS 与帧率，web.dev 明令禁止）。

### 3.4 入场动效
- GreetingBar + Bento 网格错峰入场：`<TransitionGroup>` + `@vueuse/motion` 的 `v-motion` 指令（`:initial`/`:enter` 声明式），总时长 ≤ 1.5s，全部 transform/opacity。
- `reduced-motion` 时：不播入场动画，直接渲染结局态（预算清零，等价 3.1 的降级链顶层）。

### 3.5 必须搭配降级的炫酷方案清单
| 炫酷方案 | 必须配的降级 |
|---|---|
| tsParticles 粒子背景 | reduced-motion → CSS 渐变；无 canvas → 同上（本身 2D 兜底好） |
| three/TresJS 3D 背景与 3D 热力图 | WebGL 不可用 / context lost → 静态纹理 + ECharts 2D 热力图；reduced-motion → 停止 rAF 只渲一帧 |
| WebGPU 增强 | 不可用 → WebGLRenderer 同场景代码回退 |
| AI 生成视频背景 | poster 静态图 + 懒加载 + reduced-motion 只显 poster |
| Aceternity/Magic 式光效组件 | 不处理 reduced-motion 的原组件一律改造后再复制；无 WebGL 时纯 CSS 光效仍应可用 |

---

## 4. 评分卡汇总

| 候选 | 兼容性(25%) | 社区(20%) | 新颖度+契合(20%) | 性能体积(20%) | 无障碍降级(15%) | 总分 | 评级 |
|---|---|---|---|---|---|---|---|
| **WAAPI（底座）** | 5 | 5 | 4 | 5 | 5 | 4.8 | ★★★★★ |
| **@vueuse/motion** | 5 | 4 | 4 | 5 | 4 | 4.5 | ★★★★★ |
| tsParticles 生态 | 5 | 4 | 3 | 4 | 5 | 4.2 | ★★★★ |
| **AI 生成静态纹理+动效** | 5 | 4 | 5 | 5 | 5 | 4.8 | ★★★★★ |
| Three WebGPURenderer/TSL | 4 | 5 | 5 | 3 | 3 | 4.1 | ★★★★ |
| wgpu-matrix | 4 | 2 | 3 | 4 | 3 | 3.2 | ★★★ |
| CanvasKit/canvaskit-wasm | 3 | 3 | 3 | 2 | 3 | 2.8 | ★★★ |
| skia-canvas（Node） | 4 | 3 | 3 | 3 | 4 | 3.4 | ★★★ |
| shadcn-vue | 5 | 5 | 3 | 4 | 4 | 4.3 | ★★★★ |
| inspira-ui | 4 | 4 | 4 | 3 | 3 | 3.7 | ★★★★ |
| Magic UI（React） | 1 | 5 | 4 | 3 | 2 | 3.0 | ★★★ |
| Aceternity UI（React） | 1 | 4 | 4 | 3 | 2 | 2.8 | ★★★ |
| AI 生成视频背景 | 4 | 3 | 4 | 2 | 3 | 3.2 | ★★★ |

**入选（首页落地）**：WAAPI 底座、@vueuse/motion、AI 生成静态纹理+视差、tsParticles（粒子背景备选）
**渐进/观望**：Three WebGPURenderer（背景层 WebGPU 增强位）、inspira-ui（抄组件不引库）、shadcn-vue（组件基座）
**淘汰/不引入**：CanvasKit/canvaskit-wasm、skia-canvas、Magic UI 与 Aceternity（React 专属）、wgpu-matrix（无自写 WebGPU 需求）、AI 生成视频背景

---

## 5. 一句话结论

本域最推荐的 3 个方向：**① Web Animations API 全面化（零依赖动效底座 + scroll-driven，同时服务入场/交互/性能，★★★★★）；② AI 生成静态纹理/颗粒资产 + CSS 视差（用最省成本的方式做出"AI 味"视觉，且本身就是降级兜底，★★★★★）；③ @vueuse/motion（Vue 声明式动效，Bento 卡片入场与 hover 光效的首选封装，★★★★★）**——三个方向叠加即可覆盖 Bento 的背景层（AI 纹理+视差）、widget 层（shadcn-vue/inspira-ui 风格光效）、交互层与入场动效（motion + WAAPI），并把 CWV 预算（LCP<2.5s / INP≤200ms / CLS<0.1）、JS gzip ≤250KB、prefers-reduced-motion 与 WebGL 降级链作为不可协商的底线。
