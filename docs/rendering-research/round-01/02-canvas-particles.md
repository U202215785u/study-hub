# 渲染调研 Round 01 · 域 02：Canvas / 2D 粒子与生成艺术

> 调研对象：Study-Hub 首页（Vue 3.5 + Vite 5 + Tailwind 3 + ECharts + Storybook 8.6；Bento 8×4 仪表盘，9 个 widget：热力图/日历/今日任务/自动化队列/知识库/手账/快捷指令/创作入口/工作流；GreetingBar 顶部问候）。
> 调研时间：2026-08-03。数据来源：GitHub API / npm registry / 官方站点；标注「未联网验证」的条目基于公开已知知识，需人工复核。
> 评分卡权重（沿用 animation-research 任务书）：Vue3/Vite 兼容 25%、社区活跃度 20%、效果新颖度+场景契合 20%、性能/包体积 20%、无障碍/降级 15%。

---

## 0. 结论速览

| 候选 | 版本 | stars | 维护 | Vue3 集成 | gzip 量级 | 评级 | 一句话 |
|---|---|---|---|---|---|---|---|
| **tsParticles** | 4.3.2 | 8.9k | 极活跃（周更） | 官方 `@tsparticles/vue3` | 基础 ~10–20KB（slim 按需） | ★★★★★ | 粒子背景的第一选择：官方 Vue3 组件 + 分层按需包 + 与首页"知识网络"隐喻天然契合 |
| **canvas-confetti** | 1.9.4 | 12.7k | 活跃（2025-10） | 原生 API（框架无关） | ~8KB | ★★★★ | 极轻的庆祝/反馈动效，任务完成撒花、打卡成功，无 Vue 适配成本 |
| **Rive (@rive-app/canvas)** | 2.39.1 | 958 (runtime) | 活跃（周更） | 原生 API + 自写 composable | ~200KB（含 wasm） | ★★★★ | 轻量矢量动效格式，空状态/吉祥物/加载动效可交互，素材由 rive.app 提供 |
| **GSAP + Canvas** | 3.15.0 | 27.4k | 活跃（2026-04） | 原生 API（可 tween 任意数值） | ~24KB core | ★★★★ | 不动画库，而是"编排器"：给 canvas 粒子/入场时序/数字滚动做统一驱动 |
| **Konva / vue-konva** | 10.3.0 / 3.4.0 | 14.7k | 活跃（2026-07） | 官方 `vue-konva` (Vue3) | ~26–45KB | ★★★ | Canvas 场景图+交互，首页目前无强画布交互需求，仅当出现"可编辑画布/手写/标注"再启用 |
| **PixiJS** | 8.19.0 | 47.9k | 极活跃 | 原生 API + composable | core ~45KB（tree-shake） | ★★★ | WebGL/WebGPU 2D 最强渲染器，但首页粒子背景用它是杀鸡用牛刀 |
| **Proton (proton-engine)** | 7.1.5 | 2.5k | 低活跃（2026-03） | 原生 API | ~20KB | ★★★ | 想完全掌控粒子发射/物理时可用，文档与生态薄弱，需自写渲染循环 |
| **Lottie (lottie-web)** | 5.13.0 | 32k | 低活跃（2025-09） | **无官方 Vue3 封装**（vue-lottie-player 是 Vue2） | ~100KB+ | ★★★ | 素材极丰富，但 Vue3 要自封装，且维护放缓；Rive 是更现代的替代 |
| **fabric.js** | 7.4.0 | 31.4k | 活跃（2026-07） | 原生 API | ~200KB | ★★ | Canvas 对象模型+SVG 解析，定位是"编辑器"，与仪表盘场景不符 |
| **Paper.js** | 0.12.18 | 15.1k | 停滞（2024-07 后无 commit） | 原生 API | ~120KB | ★★ | 矢量生成艺术经典，但两年未更新，进生产有风险 |
| **OGV.js** | - | 1.2k | 低活跃 | 原生 API（wasm 解码器） | 数百 KB | ★ | 浏览器内解码 Ogg/Theora 音视频，与首页无场景交集 |
| **particles.js** | 1.0.6（停更） | 30.2k | 停更（2024-03） | 无 | ~13KB | ★ | 已被 tsParticles 官方迁移文档明确取代，勿新引入 |

---

## 1. 候选技术明细

### 1.1 tsParticles（粒子背景/彩纸/烟花） —— ★★★★★

- **类别**：Canvas 2D 粒子引擎（WebGL/WebGL2 可选渲染器）
- **官方链接**：https://particles.js.org · GitHub https://github.com/tsparticles/tsparticles
- **成熟度**：npm `tsparticles` 4.3.2、`@tsparticles/vue3` 4.3.2（2026-08 发布，GitHub pushed 2026-08-03，周更）；8.9k stars；MIT；官方 Discord/Reddit 社区活跃。
- **社区热度**：粒子背景事实标准；2026 年官网重建，推出 `@tsparticles/basic / slim / full / all` 分层包与 `@tsparticles/confetti / fireworks / ribbons` 单功能包（CDN bundle `@tsparticles/confetti@4.3.3` 已验证）。部分资料显示超过 9 万周下载量（未联网验证具体数字）。
- **代表性案例**（均已联网验证可达）：
  - https://particles.js.org —— 官网即 demo 中心（Big Blend Particle、Playground 在线调参）
  - https://confetti.js.org —— 彩纸子产品
  - 大量海外着陆页用它做动画背景（showcase 由官方维护，未联网逐个验证）
- **Vue 3 集成**：`npm i @tsparticles/vue3 @tsparticles/slim`（或按场景选 `@tsparticles/basic`），`<Particles id="tsparticles" :options="..."/>` 官方组件；也支持自定义 Engine + 按需注册模块（tree-shaking 友好，`sideEffects: false`）。
- **性能与可访问性**：full bundle unpacked 1MB，但 slim/basic 层可把 gzip 压到 ~10–20KB；粒子数量、`background.opacity`、link 连线距离是主要帧率开销，建议上限 ~80–150 粒子 + DPR 限制。官方支持 `pauseOnBlur / pauseOnOutsideViewport`、自动降低帧率（`fpsLimit`）；需配合 `prefers-reduced-motion` 停用 + 提供关闭开关（任务书全局要求）。canvas 装饰性 → 不承载信息，`aria-hidden`。
- **评级理由**：Vue3 官方封装 + 按需体积 + 全功能预设，是目前把"粒子背景"落进 Vue 项目成本最低、最稳的选择。

### 1.2 canvas-confetti（庆祝/反馈彩纸） —— ★★★★

- **类别**：Canvas 2D 一次性粒子爆发（confetti/snow/fireworks）
- **官方链接**：https://github.com/catdad/canvas-confetti · demo https://catdad.github.io/canvas-confetti/
- **成熟度**：npm 1.9.4（2025-10，GitHub pushed 2025-10-25）；12.7k stars；ISC；单文件零依赖，unpacked 92KB / gzip ~8KB。
- **社区热度**：GitHub 常客，CodePen 大量衍生用法；jsDelivr CDN 可直接引用。
- **代表性案例**（未联网验证，基于知名度）：各类"任务完成"型产品（Todo 应用、打卡类）庆祝效果；官方 demo 页可调 origin/粒子形状。
- **Vue 3 集成**：`npm i canvas-confetti`，直接 `import confetti from 'canvas-confetti'` 在事件回调中调用；也有一批社区封装（vue3-canvas-confetti 等，未联网验证），但原生 API 足够，无需封装。
- **性能与可访问性**：按需触发、自带自清理，不做持续动画 → 帧率开销只在爆发瞬间；支持 `disableForReducedMotion: true` 选项（可直接匹配 reduced-motion 策略）。触发后 2–3s 自动消散，不影响 Bento 网格交互。
- **评级理由**：体积几乎可忽略、零框架依赖、与"完成任务/打卡成功"微交互场景一一对应。

### 1.3 Rive（轻量矢量动效素材格式） —— ★★★★

- **类别**：矢量动画运行时（Canvas/WebGL + wasm 解码 `.riv` 文件；含状态机、可交互触发）
- **官方链接**：https://rive.app · runtime GitHub https://github.com/rive-app/rive-wasm
- **成熟度**：npm `@rive-app/canvas` 2.39.1（2026-07 发布，GitHub pushed 2026-08-02）；runtime repo 958 stars（编辑器闭源，star 数低属正常）；MIT；官方团队（Rive 公司）持续维护。
- **社区热度**：营销官网/产品空状态高频出现；rive.app 有 Marketplace 免费素材库（https://rive.app/community/files 可达但为 JS 渲染页，未联网验证内容）。
- **代表性案例**（未联网验证，基于知名度）：Rive 官网 showcase（展示交互动画 demo）；不少 SaaS 产品用 Rive 做吉祥物/加载/空状态；官方社区文件市场大量免费 `.riv`。
- **Vue 3 集成**：无官方 Vue wrapper（官方 wrapper 是 `@rive-app/react-canvas`）；用 `@rive-app/canvas` 原生 API 包一个 composable（onMounted 初始化 + onBeforeUnmount cleanup + 响应式 layout/autoplay），或用社区 `vue-rive` 包（未联网验证）。素材本身是 .riv 文件，走 Vite 静态资源导入。
- **性能与可访问性**：wasm 解码比 GIF/视频轻；单文件 ~200KB gzip 级（unpacked 5MB）；矢量缩放无损；支持 `prefers-reduced-motion` 时只播放静止帧（读取状态机首帧）；对辅助技术同样视为装饰。
- **评级理由**：相比 Lottie 是"新一代"：体积更小、可交互状态机、编辑器免费、素材生态正在成长；代价是需要第三方编辑器出素材 + 自写 Vue 封装。

### 1.4 GSAP + Canvas（动效编排器） —— ★★★★

- **类别**：动画编排库（可 tween 任意对象属性，包括 canvas 内粒子的 x/y/alpha；不是粒子库本身）
- **官方链接**：https://gsap.com · GitHub https://github.com/greensock/GSAP
- **成熟度**：npm `gsap` 3.15.0（2026 年发版）；27.4k stars；pushed 2026-04；Standard "no charge" 许可（免费商用，非 OSI 开源，团队/企业注意条款）；社区为业界最大。
- **社区热度**：Showcase 页（https://gsap.com/showcase 已验证可达）收录 Bombon、Cobloc Architecture、Kononenko、Noomo、Square43 等获奖站点；CodePen @GreenSock 数千 demo；2026 年 GSAP 已是 Webflow 官方背后动画引擎。
- **代表性案例**（showcase 列表来自已联网验证的 gsap.com/showcase）：https://bombon.rs · https://www.cobloc.archi/ · https://square43.com（具体粒子效果未逐个验证）
- **Vue 3 集成**：`npm i gsap`，框架无关；composable 里 `gsap.to(obj, {...})` 驱动 canvas 内粒子数值，或直接 `gsap.to('.bento-card', { stagger: ... })`；与 PixiJS 有官方 PixiPlugin。
- **性能与可访问性**：ticker 自带时间轴、可 `gsap.matchMedia()` 里按 `prefers-reduced-motion` 条件注册/注销动画（官方推荐做法）；不做高频 canvas 重绘时成本低。
- **评级理由**：它不是本域"粒子库"的竞争者，而是把粒子/入场/数字滚动统一编排的粘合剂；但按任务书分域，它更适合归入"动效趋势/编排"域做细评，这里只记录与本域的交叉用法。

### 1.5 Konva / vue-konva（Canvas 场景图+交互） —— ★★★

- **类别**：Canvas 2D 场景图（节点树、命中检测、拖拽、事件）
- **官方链接**：https://konvajs.org · GitHub https://github.com/konvajs/konva
- **成熟度**：npm `konva` 10.3.0（2026-07，pushed 2026-07-28）+ 官方 `vue-konva` 3.4.0（peerDeps `vue: ^3` 已验证）；14.7k stars；MIT；size-limit core 26KB / full 45KB。
- **社区热度**：Konva React 封装（react-konva）社区较大；vue-konva 相对小众但维护正常（2026 年仍随 Vue3 发布）。
- **代表性案例**（未联网验证）：konvajs.org 官方 sandbox（画板/节点编辑器 demo）；大量设计工具的 canvas 标注功能基于 Konva 类库。
- **Vue 3 集成**：`npm i konva vue-konva`，`<v-stage><v-layer><v-rect/></v-layer></v-stage>` 声明式写画布。
- **性能与可访问性**：命中检测走内部节点树，比手写 canvas 高效；持续动画需自管 RAF；canvas 内容仍对辅助技术不可见，需要 aria 文本层。
- **评级理由**：若首页要上"可编辑画布/手写批注/拓扑拖拽"这类 widget，它是 Vue3 下最顺手的方案；但当前 9 个 widget 没有这类需求 → 观望级，不建议本轮引入。

### 1.6 PixiJS —— ★★★

- **类别**：WebGL/WebGPU 2D 渲染引擎（粒子、滤镜、批渲染）
- **官方链接**：https://pixijs.com · GitHub https://github.com/pixijs/pixijs
- **成熟度**：npm `pixi.js` 8.19.0（2026 发版，pushed 2026-07-19）；47.9k stars；MIT；团队持续迭代（v8 大版本 + WebGPU）。
- **社区热度**：业界最活跃的 2D WebGL 引擎；playground 大量游戏/互动作品；被众多游戏类官网使用。
- **代表性案例**（未联网验证）：PixiJS playground/官方 showcase（https://playground.pixijs.com）；各类 HTML5 游戏与互动营销页。
- **Vue 3 集成**：无官方 Vue wrapper；原生 API + composable（初始化 Application、resize、销毁）；v8 支持子路径按需导入（`pixi.js/particle-container` 等）。
- **性能与可访问性**：72MB unpacked 但 tree-shake 后 core ~45KB gzip；WebGL 上下文上限、移动端 GPU 差异是风险点，需降级到 2D canvas（v8 保留 canvas 后端）；`prefers-reduced-motion` 下停 ticker。
- **评级理由**：能力最强，但首页粒子背景用不到它的 90%；仅当未来要自研"高密度粒子/滤镜/批量 sprite"级特效时再升级。

### 1.7 Proton —— ★★★

- **类别**：底层粒子引擎（发射器/Behaviours/渲染器可插拔）
- **官方链接**：http://drawcall.github.io/Proton/ · GitHub https://github.com/drawcall/Proton
- **成熟度**：npm `proton-engine` 7.1.5（2025-03，pushed 2026-03）；2.5k stars；MIT。
- **社区热度**：小众但稳定存在，GitHub 有 demo 页与文档；常被"想自己写粒子系统"的人采用。
- **代表性案例**（未联网验证）：官方 demo 页（烟花/拖尾等粒子特效）；部分游戏项目集成。
- **Vue 3 集成**：原生 API + composable；无官方 Vue 封装，需自管 RAF/清理。
- **性能与可访问性**：控制面细（能精确控制粒子寿命/速度/拖尾），但意味着自己负责渲染循环与降级逻辑。
- **评级理由**：tsParticles 能覆盖 95% 场景且省事；除非需要超出 tsParticles 预设的自研物理（如磁力/场强模拟），否则不值得自己造轮子。

### 1.8 Lottie —— ★★★

- **类别**：After Effects → JSON 矢量动效播放器
- **官方链接**：https://github.com/airbnb/lottie-web · 素材 https://lottiefiles.com
- **成熟度**：npm `lottie-web` 5.13.0（2025-09，pushed 2025-09）；32k stars；MIT；维护放缓（两年一版）。
- **社区热度**：素材库 LottieFiles 有海量免费动画（featured 页 https://lottiefiles.com/featured 被 Cloudflare 拦截，未联网验证）；业界存量最大。
- **代表性案例**（未联网验证）：Airbnb 自身、大量移动/网页产品的空状态与加载动画。
- **Vue 3 集成**：⚠️ 官方 `@lottiefiles/vue-lottie-player` 1.1.0 的依赖是 `vue ^2.6.12`（npm 元数据已验证）——**Vue2 专属，不能直接用**。Vue3 两条路：a) 用框架无关的 web component `@lottiefiles/lottie-player`（`<lottie-player>` 自定义元素）；b) lottie-web 原生 API + composable（手动 loadAnimation/destroy）。新格式 dotLottie（`@lottiefiles/dotlottie-web`）值得关注（未联网验证）。
- **性能与可访问性**：SVG 渲染时可注入 DOM，做动画更重；canvas 渲染提升性能但丢失部分特性；unpacked 25MB、gzip 100KB+；同样需要 reduced-motion 静态帧。
- **评级理由**：被 Rive 挤压；且 Vue3 封装要自造。素材若已在团队 AE 流程里才值得引入，否则优先级在 Rive 之后。

### 1.9 fabric.js —— ★★

- **类别**：Canvas 对象模型 + SVG 解析/导出（编辑器向）
- **官方链接**：http://fabricjs.com · GitHub https://github.com/fabricjs/fabric.js
- **成熟度**：npm `fabric` 7.4.0（2026-07，pushed 2026-07-31）；31.4k stars；MIT；需要 Node ≥ 20（构建侧）。
- **社区热度**：图像编辑器/设计工具领域主流；与首页仪表盘场景无关。
- **Vue 3 集成**：原生 API；无官方 Vue wrapper（社区 vue-fabric-wrapper 等未验证）。
- **评级理由**：重（gzip ~200KB）、定位是"可编辑对象模型"。首页没有 SVG 编辑/导出需求 → 淘汰级（如未来做"白板/海报编辑器"再评估）。

### 1.10 Paper.js —— ★★

- **类别**：矢量脚本/生成艺术（Scriptographer 移植）
- **官方链接**：http://paperjs.org · GitHub https://github.com/paperjs/paper.js
- **成熟度**：npm `paper` 0.12.18（2024-07 发布，GitHub pushed 2024-07 后停更）；15.1k stars；MIT；429 个 open issues 无响应迹象。
- **社区热度**：曾是一代生成艺术神器，学术/艺术圈仍有存量；新项目增长停滞。
- **Vue 3 集成**：原生 API + composable。
- **评级理由**：纯矢量生成艺术（Bezier/几何）优雅，但 2 年停更 + 高 open issues 存量，进生产风险大 → 淘汰级。

### 1.11 particles.js —— ★

- **类别**：经典 Canvas 粒子背景（已停更）
- **官方链接**：https://vincentgarreau.com/particles.js/ · GitHub https://github.com/VincentGarreau/particles.js
- **成熟度**：30.2k stars 但 pushed 2024-03；367 open issues 无维护；无 ESM/tree-shaking。
- **评级理由**：tsParticles 官网有专门迁移文档（`/migrations/particles-js`），官方已明确替代关系 → 勿新引入。

### 1.12 OGV.js —— ★

- **类别**：浏览器内 Ogg/Theora/WebM 音视频解码播放器（wasm）
- **官方链接**：https://github.com/bvibber/ogv.js
- **成熟度**：1.2k stars；pushed 2026-06；许可 NOASSERTION（MPL 系），需注意。
- **评级理由**：解决的是"不支持 Ogg 的浏览器也能播"这一历史问题；包大、wasm 解码 CPU 开销高，与首页粒子/动效无交集 → 淘汰级。（若未来要"音画"类背景，用原生 `<video muted loop autoplay>` + Web Audio 可视化即可，不碰 OGV.js。）

---

## 2. 首页 Bento 仪表盘怎么用（落到真实组件）

> 现状锚点（已读代码确认）：`Home.vue` 用 `BentoDashboardGrid`（8 列 × 4 行 grid，gap 14.31px）承载 9 个 widget；`GreetingBar` 顶部问候；`WorkHeatmapWidget` 是 28×7=196 个 `<i>` 色块；已有 echarts/markmap/vuedraggable；测试体系 vitest + Storybook a11y addon。

### 2.1 背景层（全局 canvas，z-index 0，全页装饰）
- **首选 tsParticles**（`@tsparticles/vue3` + `@tsparticles/basic`）：
  - 主题：低饱和暗色 + "知识节点连线"（shape: circle + links 连线 + 鼠标 hover 吸引），隐喻学习 hub 的知识网络，与热力图的荧光色系（#d7ff63/#8b73ff）一致。
  - 配置纪律：粒子 ≤ 100、`links.opacity` 低、`fpsLimit: 30`、`pauseOnBlur: true`、DPR 上限 1.5；canvas 用 `position: fixed; inset: 0; z-index: -1`（或放在 dashboard 容器后），`pointer-events: none` + `aria-hidden`。
  - 降级链：`prefers-reduced-motion` → 只渲染一帧静态粒子；`navigator.connection.effectiveType` 为 2g/3g 或 `navigator.deviceMemory < 4` → 完全不挂载；设置页提供开关（任务书要求"可选、可关闭"）。
- **备选（包体积 0）**：纯 CSS 渐变光晕 + 40 行手写 canvas 浮动光点（RAF 循环 + reduced-motion 停帧）。预算敏感时的 Plan B。

### 2.2 widget 层（卡片内局部效果）
- **完成任务庆祝**（`TodayFocusWidget` 勾选 / 复盘周报生成）：`canvas-confetti`，`origin: { x: 卡片中心归一化, y: 0.6 }`，一次性爆发 80–150 片，`disableForReducedMotion: true`。比全屏彩纸克制、符合 dashboard 工作语境。
- **空状态 / 加载 / 吉祥物**：Rive `.riv` 素材（快捷指令、知识库、日历的空状态插画动效；解析队列 loading 图标）。这是 Rive 比 Lottie 更值得的先手场景：体积小 + 可交互（hover 触发状态切换）。
- **热力图入场**：196 个 cell 的 stagger 点亮，用 CSS `transition-delay` 或 GSAP `stagger` 即可（DOM 属性动画，不必 canvas）；`prefers-reduced-motion` 下全部直接渲染。
- **数据卡片**：ECharts 图表入场/重渲染过渡衔接（本轮不引新库；ECharts 自带 animation，只需统一时长曲线）。

### 2.3 交互层
- **鼠标跟随/光点**：tsParticles 自带 interactivity（repulse/hover 连线），一条配置即可；不引入额外依赖。
- **卡片 hover 磁吸/涟漪**：属"动效编排"域（GSAP/交互范式），本域不重复选型；注意 Bento 卡片是 DOM+文本，不用 canvas 承载内容交互。
- **何时才需要 Konva/PixiJS**：出现"手写批注、画布标注、高密度粒子、滤镜"级需求再启用；本轮不引入。

### 2.4 入场动效
- **GreetingBar**：问候语进场用 GSAP（或纯 CSS）淡入+上移即可；"文字拆粒子飞入"这类 canvas 效果炫但成本高、reduced-motion 后毫无意义 → 列为噱头，不建议。
- **Dashboard widget 入场**：GSAP stagger 或 Flip（切换布局时 Bento 卡片平滑重排）——归编排域，本域确认"驱动 canvas 粒子时用它做时序"。

---

## 3. 推荐组合与下一轮原型验证

**推荐组合（本域）**：
1. 背景层：`@tsparticles/vue3` + `@tsparticles/basic`（★5）—— 粒子背景事实标准，Vue3 官方封装，体积可控。
2. 反馈层：`canvas-confetti`（★4）—— 任务完成的庆祝微交互，8KB 级成本。
3. 素材层：`@rive-app/canvas`（★4）—— 空状态/吉祥物/加载的轻量矢量动效，需 rive.app 出素材 + 自写 composable。

**下一轮原型验证（Storybook，按任务书第 3 阶段）**：
- `ParticleBackground.stories.jsx`：tsParticles basic 包 gzip 增量、Playwright 帧率（performance.now 采样）、reduced-motion 静态帧断言、低端设备降级分支。
- `ConfettiTrigger.stories.jsx`：canvas-confetti 触发-自清理、a11y 无侵入。
- `RiveEmptyState.stories.jsx`：@rive-app/canvas 加载 `.riv`、composable 生命周期、wasm 体积增量。
- 复测硬约束：不破坏现有 vitest/Storybook、与 echarts/markmap/vuedraggable 无冲突（各库独立 canvas/DOM 域）。

**淘汰/观望记录**：particles.js（停更）、paper.js（停更）、OGV.js（场景不符）、fabric.js（编辑器定位）→ 淘汰；PixiJS、Konva、Proton、Lottie → 观望，仅当对应具体需求出现时再评估。

---

## 4. 调研元信息

- 联网验证：GitHub API（pixijs/tsparticles/particles.js/Proton/konva/paper/fabric/rive-wasm/lottie-web/GSAP/canvas-confetti/bvibber-ogv）、npm registry（上述全部 + @tsparticles/vue3 + @rive-app/canvas + vue-konva + @lottiefiles/vue-lottie-player 依赖确认 Vue2）、官网（particles.js.org、confetti.js.org、gsap.com/showcase 均 200）。
- 未联网验证：Rive/LottieFiles showcase 具体案例内容、Awwwards SOTD 站点、第三方 Vue 封装（vue-rive、vue3-canvas-confetti）、周下载量精确数值、部分案例站点。
- 许可提醒：GSAP 为 "Standard no-charge license"（非 OSI 开源，商用免费但有条款）；其余核心候选均 MIT/ISC。
