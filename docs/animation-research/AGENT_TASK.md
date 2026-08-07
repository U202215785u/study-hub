# 任务书：交互动画库社区调研（细化版）

> 由用户原始需求细化而来，供 agent 执行。循环机制见 skill `animation-research-loop`（`.reasonix/skills/animation-research-loop/SKILL.md`）。

## 一、原始需求

> 该项目要开始引入交互动画库了，特别是首页，需要一些新颖但交互动效以及交互方式，请进行大面积的社区调研。

## 二、需求拆解（细化后）

| # | 子需求 | 细化说明 | 交付物 |
|---|--------|----------|--------|
| R1 | 引入交互动画库 | 选型要落到**具体库 + 版本**，而非泛泛推荐；需给出 Vue 3 兼容、包体积、许可、维护度证据 | 候选库评分表 |
| R2 | 首页（Home.vue）动效 | 动效方案要**绑定首页真实组件**：GreetingBar 入场、BentoDashboardGrid 卡片 hover/展开、CapsuleNavigation 切换、搜索/快捷入口微交互 | 场景 × 动效方案映射表 |
| R3 | 新颖交互动效 | 调研 2024-2026 前沿趋势（awwwards/CodePen/GSAP showcase），区分"可落地的"与"噱头" | 趋势清单 + 可行性评级 |
| R4 | 新颖交互方式 | 不止 hover/点击：cursor 跟随、滚动驱动、磁吸、morphing、手势、键盘/无障碍替代 | 交互范式清单 |
| R5 | 大面积社区调研 | 必须**多来源、多轮迭代**：npm/GitHub/官方文档/社区教程/issue/竞品站点；循环直到收敛 | round-N.md + FINAL-RECOMMENDATION.md |

## 三、硬约束（不可违反）

1. Vue 3.5 + Vite 5 + Tailwind 3.4 + 自建 design-system（Storybook 8.6 / vitest / playwright）
2. 只接受 Vue 3 兼容或框架无关的库；vue2 专属、无维护、非宽松许可（GPL/AGPL/专有）直接淘汰
3. 动画库按需/懒加载；纯视觉库 gzip ≤ 60KB 优先；WebGL/3D 必须有降级方案
4. 支持 `prefers-reduced-motion`；动效不依赖单一感官；键盘可达
5. 不破坏现有 Storybook 与 vitest 测试；不引入与现有 echarts/markmap/vuedraggable 冲突的方案

## 四、调研维度（评分卡权重）

- 兼容性（Vue3/Vite/tree-shaking）：25%
- 社区活跃度（周下载量/维护/issue 响应）：20%
- 效果新颖度 + 首页场景契合：20%
- 性能与包体积：20%
- 无障碍与降级能力：15%

## 五、执行方式

按 `animation-research-loop` 的 Loop 流程执行：

1. **阶段 0 种子演化**：第 1 轮用固定全景候选池；后续轮次用上轮「入选」候选 + 新发现
2. **阶段 1 并行调研**：3-4 个 read-only agent 并行（库盘点 / 动效趋势 / 交互范式 / 工程实践）
3. **阶段 2 评分汇总**：产出 `docs/animation-research/round-N.md`，候选分三级：入选 / 观望 / 淘汰
4. **阶段 3 原型验证**（第 2 轮起）：Top 2-3 在 Storybook 做最小原型，测包体积增量、帧率、reduced-motion
5. **阶段 4 收敛判断**：Top 1 连续两轮稳定且分差 ≤ 0.5 → 出最终推荐；最大 4 轮

## 六、首页场景锚点（动效方案必须能对号入座）

- GreetingBar：问候语入场（stagger/擦除/数字时钟）
- BentoDashboardGrid：卡片 hover 展开、磁吸、3D tilt、内容 reveal
- CapsuleNavigation：胶囊切换过渡（morphing / 指示器滑动）
- 搜索/快捷入口：morphing 搜索框、光标跟随、涟漪
- 数据卡片：数字滚动计数、图表入场（衔接已有 echarts）
- 全局：prefers-reduced-motion 降级、背景粒子/光晕（可选、可关闭）
