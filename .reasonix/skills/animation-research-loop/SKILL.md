---
name: animation-research-loop
description: 交互动画库社区调研的循环执行 playbook：每轮=种子演化→并行调研→评分卡→原型验证→收敛判断，产出可落地的库选型与首页动效方案
---

# 交互动画库调研 Loop（Animation Research Loop）

用于「Study-Hub 前端引入交互动画库 + 首页（Home.vue）新颖交互动效」的社区调研。目标不是一份一次性报告，而是一个**收敛式循环**：每轮产出候选池评分卡，下一轮在上一轮基础上收窄/换向，直到 Top 推荐稳定或用户拍板。

## 项目硬约束（筛选候选时不可违反）

- 技术栈：Vue 3.5 + Vite 5 + Tailwind 3.4 + Pinia + vue-router；组件库是自建 design-system（Storybook 8.6 + vitest + playwright 测试）
- 首页现状：Home.vue 是 Bento Dashboard（WorkbenchFrame / CapsuleNavigation / GreetingBar / BentoDashboardGrid / DashboardEditor），已有 echarts、markmap、vuedraggable（拖拽）、html2canvas
- 只接受 **Vue 3 兼容**（原生 Vue 3 或框架无关）的库；vue2 专属、无维护、MIT 以外不友好许可（GPL/AGPL/专有）直接淘汰
- 性能预算：动画库按需加载/懒加载；纯视觉库 gzip 后 ≤ 60KB 优先（GSAP 全量 ~23KB gzip 可作基准），WebGL/3D 库需有降级方案
- 无障碍：必须支持/兼容 `prefers-reduced-motion`；交互动效不得依赖单一感官（颜色/悬停），要有键盘可达替代
- 工程：tree-shaking 友好、Vite 集成文档/社区实践、不破坏现有 Storybook 与 vitest 测试

## Loop 结构（每轮 4 个阶段）

### 阶段 0：种子演化（由主 Agent 完成，不派 subagent）
- 第 1 轮：种子 = 固定的全景候选池（见下）+ 调研方向
- 第 N 轮：种子 = 上轮评分卡中「保留」区间候选 + 上轮调研中新发现；每轮可收窄评分维度或换方向（如从"库选型"转向"具体动效方案原型"）
- 每轮开始前必须读上一轮的 `docs/animation-research/round-N.md`，不得重复已覆盖的结论

### 阶段 1：并行调研（fleet / parallel_tasks，全部 read-only）
按方向拆分 3-4 个并行任务，每个任务返回**结构化 markdown 评分卡**。方向建议：
1. 库盘点：候选库的版本、维护状态、npm 周下载量、许可、gzip 体积、Vue 3 兼容性、tree-shaking
2. 动效趋势：2024-2026 获奖/热门站点（awwwards、GSAP showcase、CodePen 热门）中的新动效模式
3. 交互范式：适用于 dashboard/首页的新交互方式（bento 展开、磁吸 hover、cursor 跟随、滚动驱动、morphing、手势/键盘替代）
4. 工程实践：包体积预算、懒加载策略、与 Tailwind/Storybook 集成、WCAG 2.2 动效要求、design tokens 动效规范

每个 subagent 的任务书模板（主 Agent 填充方括号部分后派发）：
```
你是一个前端动效领域调研 agent。目标：为 [研究主题] 做社区调研，输出一份结构化评分卡。

约束（必须遵守）：
- 只读调研：可用 web_fetch/research/read_file，不改任何代码
- 技术背景：Vue 3.5 + Vite + Tailwind 3.4 + 自建 Storybook design-system，首页是 Bento Dashboard
- 每个结论必须附来源 URL 或文件路径，禁止无依据断言
- 库类结论必须包含：版本、npm 周下载量、GitHub stars、最后提交时间、许可、gzip 体积、Vue 3 支持情况

输出格式（严格按此结构，markdown）：
# [主题] 第 N 轮调研
## 候选清单（表格：名称 | 版本 | 活跃度 | 许可 | gzip | Vue3 | 一句话结论）
## 关键发现（每条 1-3 句 + 来源 URL）
## 风险与陷阱
## 推荐（Top 3 + 理由，标注置信度 高/中/低）
## 下一步建议（供下一轮种子演化）
```

### 阶段 2：评分与汇总（主 Agent 完成）
用统一评分卡给每个候选打分（1-5 分）：
- 兼容性（Vue3/Vite/tree-shaking）权重 25%
- 社区活跃度（下载量/维护/issue 响应）权重 20%
- 效果新颖度/与首页场景契合 权重 20%
- 性能与包体积 权重 20%
- 无障碍与可降级 权重 15%
输出 `docs/animation-research/round-N.md`（含评分表 + 候选分级：入选/观望/淘汰）。

### 阶段 3：原型验证（可选，第 2 轮起）
对 Top 2-3 在 Storybook 或临时组件中做最小原型（一个首页场景：如 GreetingBar 入场、Bento 卡片 hover 展开、CapsuleNavigation 切换过渡），验证：
- 包体积增量（vite build 前后对比 dist 大小）
- 帧率/掉帧（playwright 录制或手动）与 `prefers-reduced-motion` 表现
- 与 design-system tokens 的契合度
原型结果写回 round-N.md 的「原型验证」小节。

### 阶段 4：收敛判断（主 Agent 完成）
- 收敛：Top 1 连续两轮不变 且 与 Top 2 分差 ≤ 0.5 → 输出最终推荐报告 `docs/animation-research/FINAL-RECOMMENDATION.md`（含试点范围：先在首页哪个组件用、接入步骤、回滚方案）
- 未收敛 → 调整种子/维度/门槛，进入下一轮；最大 4 轮
- 任何一轮用户拍板（选定了库或方向）→ 立即收敛
- 连续两轮无新候选进入「入选」区间 → 视为已穷尽，提前收敛

## 输出物清单
- `docs/animation-research/round-{N}.md`：每轮评分卡与分级
- `docs/animation-research/FINAL-RECOMMENDATION.md`：最终推荐（收敛时）
- 所有文档互相链接上一轮/下一轮

## 常识基准（第 1 轮种子，调研时核对而非盲信）
- Vue 生态：@vueuse/motion、Motion for Vue（motion-v）、vue-transition 增强
- 框架无关动画：GSAP、Motion One (motion)、Anime.js、Mo.js、Lottie (lottie-web) / dotlottie、Rive、Theatre.js、SVG 动画（snap.svg、vivus、kute.js）
- 滚动/视差：Lenis、scroll-driven animations（CSS 原生 + @scroll-timeline 兼容）、GSAP ScrollTrigger
- 文本/拆字：SplitType、gsap SplitText
- 首页场景趋势：bento grid hover 展开、magnetic 按钮、cursor 光晕跟随、morphing 搜索框、数字滚动计数、入场 stagger、3D tilt 卡片、纸屑/粒子轻量背景
