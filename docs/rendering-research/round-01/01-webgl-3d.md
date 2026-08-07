# Round 01 · 主题域调研：WebGL / 3D 渲染

> 目标项目：Study-Hub（Vue 3.5 + Vite 5 + Tailwind 3.4 + ECharts + Storybook 8.6，首页为 Bento 网格仪表盘，含热力图/日历/任务等 widget）
> 调研日期：2026-08（数据均通过 GitHub API / npm registry / npm downloads API 联网验证，未标注项为"未联网验证"）
> 结论诉求：每个候选技术落到「首页 Bento 仪表盘怎么用」（背景层 / widget 层 / 交互层 / 入场动效）

---

## 0. 全景候选池与硬数据（联网验证）

| 候选 | 类别 | GitHub ⭐ | npm 包 @ 版本 | 周下载量 | 许可 | 最近提交 |
|---|---|---|---|---|---|---|
| Three.js | 3D 引擎 | 114,224 | `three@0.185.1` | 13,795,847 | MIT | 2026-08（极活跃） |
| TresJS | Vue 3D 组件化 | 3,646 | `@tresjs/core@5.8.3` | 50,127 | MIT | 2026-08（活跃） |
| —（TresJS 生态） | — | — | `@tresjs/cientos` / `@tresjs/post-processing@3.7.4` | 29,666 / — | MIT | 活跃 |
| React Three Fiber（仅对比） | React 3D 渲染器 | 31,616 | —（React 专属） | — | MIT | 2026-08 |
| Babylon.js | 3D 引擎（重型） | 25,882 | `@babylonjs/core@9.19.0` | 294,971 | Apache-2.0 | 2026-08（极活跃） |
| regl | 函数式 WebGL（轻量） | 5,560 | `regl@2.1.1` | 843,488 | MIT | 2026-07（较活跃） |
| OGL | 极简 WebGL 库 | 4,606 | `ogl@1.0.11` | 567,097 | Unlicense（公有领域） | 2025-04（维护放缓） |
| twgl.js | WebGL 助手（教程向） | 2,994 | `twgl.js@7.0.0` | 39,415 | MIT | 2025-10（低频） |
| troika | Three.js 3D 文字/工具 | 1,962 | `troika-three-text@0.52.5` | 3,969,555 | MIT | 2026-07（活跃） |
| Spline Runtime | 3D 场景嵌入（商业） | 闭源 | `@splinetool/runtime@1.12.98` | 589,302 | 商业（免费版带水印） | 活跃 |
| Model Viewer | 3D 模型展示 Web Component | 8,183 | `@google/model-viewer@4.3.1` | 327,932 | Apache-2.0 | 2026-07（活跃） |

**与现有依赖冲突检查**：前端现有 echarts 5.5 / markmap / vuedraggable / html2canvas 均不涉及 WebGL 全局状态，`three` 类库为独立 canvas 渲染，无冲突。唯一注意点：多个 WebGL context 共存（如未来多个 3D widget 同时渲染）浏览器有 context 数量上限（通常 8–16），需要"单一 canvas + 分视图"或按需销毁。

---

## 1. 候选技术详情

### 1.1 Three.js —— 行业标准 3D 引擎 ⭐⭐⭐⭐⭐（作为底座，不直接裸用）

- **官方**：https://threejs.org / https://github.com/mrdoob/three.js
- **成熟度**：114k ⭐、周下载 1380 万、`three@0.185.1`，2026-08 仍有高频提交；是 WebGL 的事实标准，生态最大（GLTFLoader、postprocessing、troika 等 addons 全部围绕它）。
- **社区热度信号**：Awwwards「Site of the Day」中 3D 站点绝大多数基于 three；2025 年 Bruno Simon 的 `folio-2025`（已验证在线，https://bruno-simon.com）用 three 的 **TSL + WebGPU** 渲染，源码 MIT 开源（github.com/brunosimon/folio-2025）。
- **代表性案例**：
  - https://bruno-simon.com（已验证，3D 驾驶游戏式作品集，TSL/WebGPU）
  - https://threejs.org/examples（官方海量示例，WebGPU/物理/粒子）
  - https://lusion.co（已验证，Awwwards 获奖 WebGL 工作室官网）
- **Vue 3 集成**：npm 直接引入 + 自封装组件/`composable`（`onMounted` 建场景、`onUnmounted` dispose）；或用 TresJS 声明式封装（见 1.2）。Vite 下 `import * as THREE from 'three'` 可 tree-shaking。
- **性能与可访问性**：核心 gzip 约 150–200KB（`three` 完整包 ~600KB，靠 import 裁剪）；GPU 开销取决于场景复杂度（粒子数、post-processing 链）。降级方案成熟：`renderer.debug.checkShaderErrors`、捕获 context lost；`prefers-reduced-motion` 时停止 rAF 循环并停自动旋转。
- **评级 ★★★★★**：作为一切 3D 能力的底座生态无敌、许可干净，且与 TSL/WebGPU 前沿对齐。

### 1.2 TresJS —— Vue 3 专属的声明式 Three.js（本域首选集成层）⭐⭐⭐⭐⭐

- **官方**：https://tresjs.org / https://github.com/Tresjs/tres
- **成熟度**：3.6k ⭐、`@tresjs/core@5.8.3`、周下载 5 万；`peerDependencies: vue>=3.4, three>=0.133`，与项目 Vue 3.5 完全匹配；`sideEffects:false` 便于 tree-shaking；官方 monorepo 含 `@tresjs/cientos`（预设组件库，含 `Float`、`Stars`、`CameraControls` 等）与 `@tresjs/post-processing`。
- **社区热度信号**：Vue 生态内唯一的 Three.js 声明式方案（等价 R3F 之于 React，R3F 31.6k ⭐ 证明该模式受欢迎）；TresJS 是 VueUse/DevTools 生态同源维护，Discord 活跃。
- **代表性案例**：tresjs.org 首页与官方 examples（粒子星系、ShaderMaterial 示例，未联网验证具体 URL，官方站点在线）；社区作品集站。
- **Vue 3 集成**：写 `<TresCanvas>` + `<TresMesh>` / `<TresPerspectiveCamera>` 组件即可，模板即场景；对 Storybook/Vitest 友好（可把 3D 场景拆成独立可测试组件）；`@tresjs/post-processing` 提供 Bloom/DOF 等后期链。
- **性能与可访问性**：内核很薄（core unpacked ~132KB），真正的体积大头是 three 本身；渲染循环由 TresJS 管理，可 `pause` 动画；canvas 标签天然 `aria-hidden` 可处理。
- **评级 ★★★★★**：Vue 3 项目里把 three 塞进 Bento 的最短路径，声明式、可测试、与 design-system 组件化理念一致。

### 1.3 Babylon.js —— 引擎级重武器（参考/观望）⭐⭐⭐⭐

- **官方**：https://www.babylonjs.com / https://github.com/BabylonJS/Babylon.js
- **成熟度**：25.9k ⭐、`@babylonjs/core@9.19.0`、周下载 29 万、Apache-2.0；微软主导，2026-08 高频发布，WebGPU/Gaussian Splatting/流体渲染等前沿特性领先。
- **社区热度信号**：游戏引擎向，Playground 生态大；商业级能力（Node 材质、GUI、物理）。
- **代表性案例**：官方 Playground https://playground.babylonjs.com（未联网验证，知名）；过去经典商业案例 BMW/微软等为未联网验证的已知案例。
- **Vue 3 集成**：无官方 Vue 封装，需原生 API + 手写组件；包更大（unpacked 69MB 源码，按需 import 仍明显重于 three）。
- **性能与可访问性**：功能面比 three 大一个量级，对仪表盘属于杀鸡用牛刀；体积与复杂度是硬伤。
- **评级 ★★★★**：技术力强但与本项目场景不匹配（无游戏/物理需求），仅在需要流体/Gaussian Splatting 级效果时再考虑。

### 1.4 regl —— 函数式 WebGL，轻量 shader/粒子背景最优解 ⭐⭐⭐⭐⭐（背景层专用）

- **官方**：https://regl-project.github.io/regl / https://github.com/regl-project/regl
- **成熟度**：5.6k ⭐、`regl@2.1.1`、周下载 **84 万**（被大量数据可视化库依赖）、MIT；维护节奏慢但稳定（2026-07 仍有提交）。
- **社区热度信号**：stack.gl 生态核心；CodePen 上大量 regl 粒子/波浪 shader 作品。
- **代表性案例**：官方 gallery https://regl-project.github.io/regl/gallery.html（未联网验证具体页，站点在线）；算法艺术站 inconvergent.net（未联网验证）；无数 CodePen regl 背景。
- **Vue 3 集成**：无框架绑定，canvas + `regl()` 直连；封装成一个 `WebglBackground.vue` + `useReglScene` composable 即可，体积极小（min+gzip 约 50KB 量级）。
- **性能与可访问性**：极低开销（单 pass 全屏 shader 或几万点粒子轻松 60fps）；无场景图，适合"纯装饰背景"；`prefers-reduced-motion` 时直接不创建场景，落到 CSS 渐变。
- **评级 ★★★★★**：做"首页背景粒子/流动场/星云"这类装饰层，体积/性能/自由度三者平衡最佳。

### 1.5 OGL —— 极简 WebGL（观望）⭐⭐⭐⭐

- **官方**：https://oframe.github.io/ogl / https://github.com/oframe/ogl
- **成熟度**：4.6k ⭐、`ogl@1.0.11`、周下载 57 万（被依赖面广）、**Unlicense 公有领域**（商业零顾虑）；**最近提交 2025-04，维护明显放缓**。
- **社区热度信号**：Awwwards 场景被大厂站点用过（已知案例）；主创 Nathan Gordon。
- **代表性案例**：官方 examples https://oframe.github.io/ogl/examples（未联网验证具体页）；Awwwards 站点（未联网验证）。
- **Vue 3 集成**：原生 API，封装成本与 regl 相当；自带 Math/GL 工具比 regl 上层一点（有场景图），适合不想引入 three 又想写场景的中间态。
- **性能与可访问性**：体积小（unpacked ~423KB，min+gzip ~40–60KB）；无额外重量。
- **评级 ★★★★**：轻量好写，但维护放缓是选型硬伤；若追求"无依赖"或已在用它的团队才值得。

### 1.6 twgl.js —— WebGL 学习/工具向（淘汰或工具参考）⭐⭐⭐

- **官方**：https://twgljs.org / https://github.com/greggman/twgl.js
- **成熟度**：3k ⭐、`twgl.js@7.0.0`、周下载 4 万、MIT；低频维护（2025-10 后停滞）。
- **定位**：webglfundamentals.org 配套教学库，提供矩阵/纹理/程序封装；不像 regl 那样声明式。
- **评级 ★★★**：文档优秀但定位教学，功能面被 regl/OGL 覆盖，不推荐正式引入。

### 1.7 troika（troika-three-text）—— Three.js 3D 文字 ⭐⭐⭐⭐（3D 数据标签用）

- **官方**：https://github.com/protectwise/troika
- **成熟度**：2k ⭐、`troika-three-text@0.52.5`、周下载 **397 万**（被 @react-three/drei 大量依赖）、MIT、2026-07 活跃。
- **定位**：SDF 高质量 3D 文字（中文需加载字体，支持 worker 异步渲染）；适合给 3D 柱状图/3D 场景加标签，与 three/TresJS 直接搭配。
- **评级 ★★★★**：若做 3D 热力图/3D 数据卡片，它把"3D 里显示中文标签"这个痛点解决得最干净。

### 1.8 Spline —— 设计师驱动的 3D 场景嵌入（no-code 备选）⭐⭐⭐⭐

- **官方**：https://spline.design（已验证在线） / npm `@splinetool/runtime@1.12.98`
- **成熟度**：闭源商业产品（YC 系），周下载 59 万，发布活跃；免费版场景带 Spline 水印，商用订阅收费。
- **集成方式**：① `<spline-viewer url="...">` Web Component（script 引入即可，Vue 中当普通自定义元素用）；② `@splinetool/runtime` JS API（`new Application(canvas)` + `app.load(url)`）。
- **性能与可访问性**：runtime unpacked **6.8MB**（很重，需动态 import + 懒加载）；场景由设计师导出 `.splinecode`，无需写 shader/建模，最适合"团队里没有 WebGL 工程师"的情况。
- **代表性案例**：spline.design 官网（已验证）；社区模板遍布 Framer/Webflow（未联网验证）。
- **评级 ★★★★**：落地最快但最重且闭源；适合"快速有一个很炫的 3D 元素"，不适合做依赖数据的 3D 可视化。

### 1.9 Model Viewer —— GLB 模型展示（本项目淘汰）⭐⭐⭐

- **官方**：https://modelviewer.dev / https://github.com/google/model-viewer
- **成熟度**：8.2k ⭐、`@google/model-viewer@4.3.1`、周下载 33 万、Apache-2.0、活跃。
- **定位**：`<model-viewer>` Web Component 展示 glTF/GLB 模型 + AR（`ar` 属性），电商产品页标配（Shopify 案例为已知信息，未联网验证）。
- **评级 ★★★**：与"仪表盘数据可视化"场景无关；仅当未来做"3D 物件展示"（如学习成就徽章）才有价值。

### 1.10 React Three Fiber（对比参照，不采用）⭐（Vue 项目）

- R3F 31.6k ⭐ 证明了"框架级 3D 渲染器"模式的价值，但 **React 专属**。TresJS 就是它的 Vue 等价物（两者理念同构），故无需在 Vue 项目考虑 R3F。

---

## 2. 2024–2026 前沿趋势（本域）

1. **WebGPU + TSL（Three.js Shading Language）**：Bruno Simon folio-2025（已验证）用 TSL 同时跑 WebGL/WebGPU；TSL 让 shader 可组合、跨后端。→ 影响选型：选 three 系能吃到这波红利，Babylon 同样支持 WebGPU。
2. **Gaussian Splatting**：3D 实景/风格化背景，three/Babylon 均有 loader（未联网验证具体版本号，已在官方文档/仓库 seen）。→ 装饰层的新奇感天花板，但资产重、移动端适配差。
3. **数据即 3D**：3D 柱状图/3D 粒子热力图/地球上的数据流（Awwwards 数据叙事类站点常见）。→ 与 Bento 热力图 widget 天然契合。
4. **轻量 shader 背景成为首页标配**：全屏 flow-field/aurora 粒子 + 鼠标视差，CodePen 高产，Awwwards SOTD 高频出现。→ regl/OGL 的菜。
5. **No-code 3D 工具渗透**：Spline/Framer/Webflow 让非前端也能产出 3D 场景；大厂官网（已验证 Lusion、Spline）普遍用 3D 讲故事。

---

## 3. 落到首页 Bento 仪表盘：怎么用

### 3.1 背景层（推荐优先做）
- **方案 A：TresJS `<TresCanvas>` 全屏背景**（星星粒子场 + `@tresjs/cientos` 的 `Stars`/`Float`，缓速自转 + 鼠标视差）。固定 `position:fixed; inset:0; z-index:-1; pointer-events:none`，包在 `BentoBackground.vue` 里。
- **方案 B：regl 单 pass shader**（aurora 流动场 / 神经网络点线 / 数字雨），零场景图、性能最好、体积最小。若只做"氛围背景"此方案足够，甚至优于 three。
- **降级链**：WebGL 不可用或 `prefers-reduced-motion` → 渲染静态 `radial-gradient` / `bg-gradient` 的 CSS 背景；`visibilitychange` 隐藏时 `renderer.setAnimationLoop(null)` 省电。
- **可访问性**：canvas `aria-hidden="true"`，视觉信息一律由 DOM widget 承载。

### 3.2 widget 层（单个 3D 化，做亮点，不全做）
- **热力图 widget（`work-heatmap`）→ 3D 柱状热力图**：TresJS + `InstancedMesh` 按 7 天×N 格数据生成柱体，高度/颜色映射 activity；标签用 troika-three-text（中文需配字体）。数据来自现有 `heatmapCells`，纯展示。
- **日历/今日任务卡片 → 3D tilt + 光晕**：卡片 hover 时 CSS `perspective` + rotateX/Y 微 tilt（**不必上 WebGL**，CSS 足够），配合现有 Tailwind 即可。
- **快捷入口/创建入口 → Spline 导出的 3D 图标**（若团队有设计师且接受重量）：动态 import runtime，懒加载，仅展示用。

### 3.3 交互层
- **鼠标视差**：背景层对指针偏移做 `lerp` 平滑（TresJS 场景内移动相机，或 regl uniform 传鼠标位置），形成"仪表盘浮在 3D 之上"的层次感。
- **卡片 hover 磁吸/光晕跟随**：属 CSS/JS 交互，见交互动画域调研；WebGL 只负责背景深度配合。

### 3.4 入场动效
- GreetingBar 入场 + 背景相机 `fly-through` 或粒子"点亮"过渡：TresJS 内用动画（`useRenderLoop` 驱动）在 `onMounted` 播 1.5–2.5s 冷启动动画；`prefers-reduced-motion` 直接跳结局。
- 首屏 3D 大字（如品牌词/日期）用 troika 文字浮于背景，随后淡出让位给 Bento 网格。

### 3.5 工程落地要点
- **按需懒加载**：仅 Home 路由引入，`defineAsyncComponent(() => import('./BentoBackground.vue'))`，three/TresJS 不进首屏主包。
- **DPR 限制**：`renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`；粒子用 InstancedMesh/`Points` 而非独立 Mesh。
- **单一 canvas 原则**：全站只保留一个 WebGL context（背景层），3D widget 若多则合并进同一场景按 `data-module-id` 分块。
- **Storybook/Vitest 不破坏**：WebGL 组件在测试环境（jsdom 无 WebGL）内 fallback 渲染占位 div，`if (!ctx.canvas.getContext('webgl2') && !getContext('webgl'))` 提前返回。
- **许可**：除 Spline 外全部 MIT/Apache/Unlicense，合规无虞。

---

## 4. 评分卡汇总

| 候选 | 兼容性(25%) | 社区(20%) | 新颖度+契合(20%) | 性能体积(20%) | 无障碍降级(15%) | 总分 | 评级 |
|---|---|---|---|---|---|---|---|
| **Three.js（底座）** | 5 | 5 | 5 | 3 | 4 | 4.5 | ★★★★★ |
| **TresJS** | 5 | 4 | 5 | 4 | 4 | 4.5 | ★★★★★ |
| regl | 5 | 4 | 4 | 5 | 5 | 4.6 | ★★★★★ |
| Babylon.js | 3 | 5 | 5 | 2 | 3 | 3.6 | ★★★★ |
| OGL | 4 | 3 | 4 | 5 | 4 | 3.9 | ★★★★ |
| Spline | 5 | 4 | 5 | 2 | 3 | 3.9 | ★★★★ |
| troika | 4 | 4 | 4 | 4 | 4 | 4.0 | ★★★★ |
| twgl.js | 4 | 3 | 3 | 5 | 4 | 3.7 | ★★★ |
| Model Viewer | 4 | 4 | 2 | 3 | 4 | 3.4 | ★★★ |

**入选（首页落地）**：TresJS（+ three 底座）、regl、troika（配套）
**观望**：Spline（no-code 备选）、Babylon（重武器，遇高斯泼溅/流体再说）、OGL（维护风险）
**淘汰**：twgl.js、Model Viewer、R3F（React 专属）

---

## 5. 一句话结论

本域最推荐的 3 个方向：**① TresJS + three.js（Vue 声明式 3D，背景层 + 3D 热力图，★★★★★）；② regl 轻量 shader 背景（全屏粒子/流动场，体积最小、降级最干净，★★★★★）；③ Spline runtime（设计师 no-code 3D 图标/场景，快速出炫但偏重，★★★★）**，三者可叠加：背景用 regl 或 TresJS 二选一，3D 数据 widget 用 TresJS+troika，品牌元素用 Spline。
