# Round 1：全景候选库评分卡

> Loop: `animation-research-loop` · 上一轮：无（首轮）· 下一轮：Round 2（原型验证）
> 评分维度与权重：兼容性 25% / 活跃度 20% / 新颖度+场景契合 20% / 性能体积 20% / 无障碍 15%（1-5 分）

## 一、候选评分总表

| 候选 | 兼容 | 活跃 | 新颖 | 体积 | 无障碍 | 加权分 | 分级 |
|---|---|---|---|---|---|---|---|
| **GSAP**（core+ScrollTrigger+SplitText） | 5 | 5 | 5 | 4 | 4 | **4.65** | ✅ 入选 |
| **Lenis**（平滑滚动，搭档非引擎） | 5 | 5 | 4 | 5 | 4 | **4.65** | ✅ 入选 |
| **motion-v**（Motion for Vue） | 5 | 4 | 4 | 3 | 3 | **3.90** | ✅ 入选（备选 PoC） |
| Anime.js v4 | 4 | 4 | 4 | 4 | 3 | 3.85 | 👀 观望 |
| @vueuse/motion | 5 | 2 | 3 | 5 | 3 | 3.70 | 👀 观望（停更风险） |
| @lottiefiles/dotlottie-web (+dotlottie-vue) | 4 | 4 | 3 | 4 | 3 | 3.60 | 👀 观望（AE 资产才需要） |
| Rive | 3 | 4 | 4 | 2 | 3 | 3.25 | 👀 观望（WASM 重、需编辑器） |
| @tweenjs/tween.js | 4 | 4 | 2 | 4 | 3 | 3.45 | 👀 观望（API 原始） |
| lottie-web | 3 | 2 | 3 | 2 | 3 | 2.65 | ❌ 淘汰（被 dotlottie 取代） |
| Theatre.js | 2 | 2 | 4 | 3 | 3 | 2.75 | ❌ 淘汰（停更 2 年） |
| SplitType | 4 | 2 | 3 | 5 | 3 | 3.40 | ❌ 淘汰（SplitText 免费后无优势） |
| Mo.js / Snap.svg / vivus / kute.js | — | — | — | — | — | — | ❌ 淘汰（废弃/停更/小众） |
| CSS scroll-driven animations | — | 原生 | — | 5 | 4 | — | 渐进增强层（Firefox 未默认开启） |

## 二、关键发现（第 1 轮）

1. **GSAP 全插件免费**：2025-12 Webflow 收购后，SplitText/MorphSVG 等此前 Club 付费插件全部免费，可直接 npm 按需导入（core gzip 27.3KB，插件各 ~10KB）。
2. **Vue 官方两条路线**：motion-v（活跃、SSR 原生、60.6KB 入口偏重）vs @vueuse/motion（14KB 但已停更 17 个月）。
3. **dotlottie 取代 lottie-web**：官方主推 @lottiefiles/dotlottie-web（Rust+WASM，29.1KB+WASM），lottie-web 已放缓且无 ESM 入口（76.8KB）。
4. **Lenis 5.4KB 原生支持 Vue**，但需实测与 vuedraggable 的 transform 冲突。
5. **体积分档**：Lenis 5.4KB / @vueuse/motion 14KB 属"近零成本"；motion-v ~60KB+、lottie-web 77KB、Rive 52.5KB+WASM 属重档。
6. **无障碍硬门槛（WCAG 2.2）**：2.3.1 三次闪烁 / 2.2.2 暂停停止隐藏 / 2.3.3 交互触发动画可禁用；JS 动效必须走 `prefers-reduced-motion` + `change` 监听，GSAP 官方方案 `gsap.matchMedia()`。

## 三、推荐组合（第 1 轮结论，待 Round 2 验证）

**主方案：GSAP（core + ScrollTrigger + SplitText）+ Lenis，配自写 `useGsap` composable（context + matchMedia(reduceMotion) + onUnmounted revert），不引入第二动画引擎。**

- 边界划分：Tailwind 3.4 `transition-*`/`animate-*` + `motion-safe:`/`motion-reduce:` 管状态切换；`<Transition mode="out-in">` 管组件进出；GSAP 只管时间线/滚动联动/stagger/SVG/数字动画。
- 备选：motion-v 单独 PoC 对比（若偏好声明式布局动画/SSR）。
- 首页场景映射：GreetingBar 入场 stagger + SplitText；Bento 卡片 hover 展开/磁吸 + 入场 stagger；CapsuleNavigation 指示器滑动过渡；数据卡片数字滚动（GSAP 或 CSS）；搜索框 morphing（CSS 即可）。

## 四、候选分级

- ✅ 入选：GSAP、Lenis、motion-v（备选）
- 👀 观望：Anime.js v4、@vueuse/motion、dotlottie、Rive、@tweenjs/tween.js
- ❌ 淘汰：lottie-web、Theatre.js、SplitType、Mo.js、Snap.svg、vivus、kute.js

## 五、Round 2 计划（种子演化 + 原型验证）

1. **PoC 1（GSAP+Lenis）**：Bento 首页最小原型——卡片 stagger 入场、滚动进度条、标题 SplitText；重点回归：Lenis×vuedraggable 冲突、ScrollTrigger×echarts/markmap 容器、组件卸载无残留。
2. **PoC 2（motion-v）**：LayoutGroup/AnimatePresence 对卡片重排的价值 + 构建后 chunk 体积对比。
3. **体积实测**：`vite build` 前后 gzip 增量，对照预算 ≤30-50KB；manualChunks 拆分 animations chunk。
4. **工程基建**：`src/lib/gsap.ts` 单点注册；`useGsap` composable；design tokens（--duration-*/--ease-*）与 Tailwind extend 共用；Storybook reducedMotion global + 双 story；Vitest mock 工厂。
5. **补全**：task-3 交互范式清单中间段（命令面板、骨架屏时序、View Transitions 与 vuedraggable 共存）。
