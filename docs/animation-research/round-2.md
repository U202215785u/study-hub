# Round 2：首页真实代码深挖 —— 场景 × 动效方案匹配

> Loop: `animation-research-loop` · 上一轮：round-1.md · 下一轮：Round 3（原型 PoC）
> 方法：读 Home.vue + design-system 全部首页组件真实代码（explore），GSAP×Vue3 集成模式与 Bento 案例（research 交叉验证）

## 一、现状盘点（真实代码）

**design-system 动效基础设施：几乎为零，但地基已铺好**
- 全库无 `<Transition>/<TransitionGroup>`、无 v-show；仅 UiProgress 宽度 / UiInput 边框 / UiButton 色彩 / TaskWidget 行背景有 CSS transition；animation 仅 spinner 旋转
- **已有 motion tokens**（foundations/tokens.css:49-60）：`--ui-duration-fast/normal/slow`（120/180/260ms）、`--ui-ease-standard: cubic-bezier(0.2,0,0,1)`，且 `prefers-reduced-motion` 下 duration 全部归 0ms —— JS 动画库必须对齐这条降级约定
- 首页 widgets 无 canvas/echarts（echarts 只在 Wiki 页），Home 场景可放心做 DOM 动画

**结构风险锚点（动效方案的硬边界）**
1. WorkbenchFrame 舞台已占用 `transform: translate(-50%,-50%) scale(...)` —— 不能直接动该元素的 transform
2. 6 处 fixed 定位：4 个 modal + drawer + toast（z-index 90/95/100/120）
3. 焦点管理强依赖 nextTick 时序（Home.vue:319-324 watch activeSurface 后 focus）—— 入场动画不能阻塞 focus；出场合必须与 `restoreFocus` 协调
4. DashboardEditor 用 vuedraggable（transform 型拖拽），与 FLIP/Lenis 有冲突面
5. 8 个 widget 经 `v-for :key="widget.id"` 渲染（Home.vue:10），`grid-auto-flow: row dense`（Home.vue:376），是 TransitionGroup + FLIP 的天然候选

## 二、场景 × 方案匹配表（核心交付）

分级：🟢 CSS/Tailwind 即可（零依赖）· 🔵 GSAP（时间线/FLIP/计数）· ⚪ 可选/低优先

| 场景/组件 | 动效方案 | 层 | 实现要点 | 风险 |
|---|---|---|---|---|
| 首页整体入场（导航→问候→网格分区错峰） | 分区 fade+up stagger 时间线 | 🔵 | `gsap.context` + timeline；GreetingBar 60ms → CapsuleNavigation 90ms → grid 卡片 stagger 0.05s | 勿动 stage 的 translate/scale；reduced-motion 走 matchMedia 分支直接置终态 |
| Bento 网格 8 卡片入场 | 卡片 stagger fade+up | 🔵 | `gsap.from('.home-dashboard-grid__item', {y:24, opacity:0, stagger:0.06})` | `row dense` 重排开销小（只入场一次）；隐藏卡片不参与 |
| **Bento 卡片重排/显隐 FLIP**（DashboardEditor 保存后） | FLIP 网格重组 | 🔵 | `await nextTick()` 后 `Flip.from('.home-dashboard-grid__item', {targets, absolute:true, onEnter/onLeave})`；**widget.id 同时作 vuedraggable item-key 与 data-flip-id**（useDashboardLayout reorder/hide/show 即触发点） | Vue 重渲染非即时必须 nextTick；不显式传 targets 会失效 |
| CapsuleNavigation | active 胶囊滑动指示 + hover 过渡 | 🟢 | 指示条用 `transform: translateX` 插值（勿用 left 动画）；链接 `transition: background 180ms`（复用 `--ui-duration-normal`） | absolute 定位在缩放舞台内 |
| GreetingBar | 问候语入场 + 时间切换 | 🟢 | h1 用 CSS animation + delay；时间文本不计数（整点/半点刷新） | 低 |
| DashboardModuleCard 四态切换（loading/error/empty/content） | 状态 out-in 过渡 | 🟢 | 包裹 `<Transition mode="out-in">`（v-if 切换处），loading 态加 shimmer（纯 CSS） | slot 结构需包裹层；注意与 UiWidgetFrame 是两套外壳，统一以 DashboardModuleCard 为准 |
| modal/drawer/toast 出入场（5 处） | 遮罩 fade + 面板 scale/fade、toast 滑入 | 🟢 | CSS transition；**focus 已就绪不受影响**（元素挂载即 focus，动画只影响视觉） | 出场合不得延迟 `restoreFocus`（Home.vue:319-324 时序） |
| DashboardEditor 抽屉 + 拖拽行 | 抽屉滑入 + Sortable 原生过渡 | 🔵/🟢 | 抽屉入场 CSS；**拖拽中只用 vuedraggable 自带 `:animation`（DDL.vue:195 已有先例），`@end` 后再 FLIP 重组** | fixed z-90；拖拽 transform 与 GSAP 冲突 → 严格分工 |
| TodayFocusWidget | 数字滚动计数（completed/total） | 🔵 | `gsap.to(obj, {val, snap, onUpdate})` 或复用已装 `@chenfengyuan/vue-countdown` | 徽标绝对定位层，只动 innerText |
| AutomationQueueWidget | 任务状态流转 + 行入场 + shimmer | 🟢/🔵 | 行入场 stagger（CSS 足够）；进度条已有宽度 transition 保留 | 行高固定模板，动效不得改布局 |
| CalendarAgendaWidget | 日期选中缩放 + 议程行 stagger | 🟢 | `transform: scale` 过渡 + 行 fade（CSS animation-delay） | 低 |
| DailyMemoryWidget | 堆叠卡 hover 浮起 | 🟢 | CSS transition 展开/浮起 | 整卡是 button，动画避开点击目标 |
| CreationWidget | 条目入场 + hover | 🟢 | CSS stagger | 低 |
| WorkHeatmapWidget 196 格点亮 | 逐格点亮/涟漪 | ⚪ | `gsap.stagger` 限量（每行/每批），`batch` 防性能 | DOM 节点多，低优先级 |
| 全局 reduced-motion | 全部动效感知开关 | — | CSS 层已由 tokens 归零自动覆盖；**GSAP 层用 `gsap.matchMedia('(prefers-reduced-motion: no-preference)')`**，且 `duration:0` 必须落可见终态 | 结束态陷阱：归零后内容不可见 |

## 三、GSAP × Vue 3 集成模式（已交叉验证）

- **useGSAP 官方只支持 React**（gsap.com/resources/React，v3.15 确认）→ Vue 标准做法 = `gsap.context()` + `onMounted` 创建 / `onUnmounted` `ctx.revert()`；reduced-motion 用 `gsap.matchMedia()` 分支；交互类动画用 `ctx.add(fn)` 保证被 revert 收录
- 无主流 Vue GSAP composable（@vueuse/motion 是另一引擎，不混用）→ 自写 ~10 行薄封装（Round 3 落地）
- **tokens 对接**：duration 用 `parseFloat(getComputedStyle(el).getPropertyValue('--ui-duration-normal'))` 读取；ease 用 `power2.out` 近似（或 CustomEase 精确）
- **参考案例**：GSAP Demo "Scrubbed bento gallery"（demos.gsap.com）、Flip 插件文档（absolute/onEnter/onLeave/stagger，官方明确"Vue 需 nextTick 后 Flip.from + 显式 targets + data-flip-id"）

## 四、收敛判断（修正第 1 轮结论）

1. **引擎收敛：GSAP（core + ScrollTrigger + Flip + SplitText 按需）为唯一 JS 动画引擎**。motion-v 在首页 8-widget 场景收益不明显（体积 ~60KB+ 换布局动画，而 Flip 已覆盖重排需求）→ motion-v 降级为"备选"（后续大功能页可再评）
2. **Lenis 降级为"观望（仅长页面）"**：首页是 656px 固定网格 + footer，无长滚动叙事，平滑滚动收益低且引入 vuedraggable/滚轮冲突面 → 不进入首页方案
3. **分层定案**：🟢 CSS/Tailwind + `<Transition>` 管微交互与出入场（约占 70% 场景，零成本、自动继承 reduced-motion）；🔵 GSAP 只做 3 件事：首页入场时间线、Bento 卡片 FLIP 重排、数字计数
4. **收敛条件即将达成**：引擎已定、方案已映射到真实组件；只差 Round 3 原型验证性能与 reduced-motion 行为 → **收敛进入 Round 3（PoC）**，通过后出 FINAL-RECOMMENDATION

## 五、Round 3 计划（原型 PoC，需写代码）

1. `src/lib/gsap.ts`（js）单点注册 + `useGsap` composable（context + matchMedia + revert）
2. 三个最小原型（Storybook story 或 Home.vue 局部）：① 首页入场时间线（stagger + reduced-motion 归零）；② Bento 卡片 FLIP 重排（模拟 DashboardEditor 保存）；③ 计数动画
3. 体积实测：`vite build` 前后 gzip 增量（core+Flip，预算 ≤30KB）
4. vitest mock 策略 + playwright 截图稳定性方案
