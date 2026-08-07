---
name: cool-render-research-loop
description: 首页炫酷渲染社区调研循环：每轮并行调研一个主题域并落盘 docs/rendering-research/，多轮收敛后产出综合报告与首页改造路线图
---

# 炫酷渲染社区调研 Loop（cool-render-research-loop）

## 触发条件

用户提到"引入炫酷渲染"、"首页视觉升级"、"大面积社区调研"、"新颖但炫酷渲染"等时，运行本 playbook。

## 项目背景（先读这些文件确认现状）

- 前端根目录：`study-hub/frontend/`，技术栈 **Vue 3.5 + Vite 5 + TailwindCSS 3 + ECharts 5 + Pinia + Storybook 8**，桌面端优先（Electron）+ 浏览器
- 首页：`study-hub/frontend/src/views/Home.vue` —— Bento 网格仪表盘（WorkbenchFrame + CapsuleNavigation + GreetingBar + BentoDashboardGrid + DashboardEditor），含热力图/日历/任务/队列等 widget
- 设计系统：`study-hub/frontend/src/design-system/`（foundations → components → patterns → widgets，组件必须配测试 + Storybook + 可访问性说明）
- 调研产出目录：`docs/rendering-research/`

## Loop 机制（核心）

1. **初始化**：创建本轮目录 `docs/rendering-research/round-NN/`（NN 从 01 递增）
2. **并行派发**：用 `fleet` 一次派发 N 个调研 agent（默认 6 个，一个主题域一个）。每个 agent 是只读调研 + 只写自己的笔记文件，`write_paths` 必须不重叠（各写各的 md）
3. **收敛判定**：本轮结束后检查主题域清单是否全部覆盖、或是否达到用户要求的轮数：
   - 未覆盖完 → 把上一轮笔记里的"待深挖问题"整理进 `round-NN/README.md`，作为下一轮焦点继续
   - 已覆盖完 → 进入汇总
4. **汇总**：合并各域笔记 → 生成 `docs/rendering-research/综合报告.md`（技术选型矩阵 + 首页改造路线图 + 风险清单）
5. **汇报**：给用户讲 3-5 个最值得做的方向、推荐优先级和理由，不要倾倒全文

## 第一轮主题域与文件约定（可扩展）

| # | 主题域 | 产出文件 |
|---|--------|----------|
| 1 | WebGL / 3D 渲染（Three.js、TresJS、Babylon、regl、OGL、Spline 等） | `round-NN/01-webgl-3d.md` |
| 2 | Canvas / 2D 粒子与生成艺术（PixiJS、tsParticles、Rive、Lottie、Paper.js 等） | `round-NN/02-canvas-particles.md` |
| 3 | 动效引擎与滚动叙事（GSAP+ScrollTrigger、Motion One、@vueuse/motion、Lenis、CSS scroll-driven 等） | `round-NN/03-motion-scroll.md` |
| 4 | CSS 前沿渲染（玻璃拟态、gradient 噪点、clip-path/mask、blend-mode、View Transitions、3D transform 等） | `round-NN/04-css-frontier.md` |
| 5 | 首页专属视觉模式（Bento 炫酷化、粒子背景、鼠标视差、spotlight、tilt 卡片、dock、glassmorphism 仪表盘参考：Linear/Vercel/Raycast 等） | `round-NN/05-homepage-patterns.md` |
| 6 | AI 时代范式 + 性能与可访问性（AI 生成视觉、WebGPU/wasm、LCP/INP 预算、prefers-reduced-motion、降级策略、Awwwards 评审标准） | `round-NN/06-ai-era-perf-a11y.md` |

## Agent Prompt 模板（派发时按域填充）

```
你是社区调研 agent。目标：为 Study-Hub（Vue 3.5 + Vite 5 + TailwindCSS 3 + ECharts + Storybook 的前端项目，首页是 Bento 网格仪表盘，含热力图/日历/任务等 widget）的【首页】寻找新颖但炫酷、且真实可行的渲染/视觉技术，来自社区与业界前沿（npm、GitHub、Awwwards、CodePen、Reddit/HN、知名官网等）。

本次主题域：<域名>（<简述范围>）

要求：
1. 用 web_fetch 尽力调研：GitHub API（api.github.com/repos/<owner>/<repo>）取 star；npm 页 / unpkg 确认版本与维护状态；Awwwards / 知名官网收集代表性案例 URL。网络不通就基于已知知识写，并标注"未联网验证"。
2. 每个候选技术记录：名称 + 类别 + 官方链接；成熟度（star/版本/维护活跃度，尽力而为）；社区热度信号；≤3 个代表性首页/官网案例（带 URL）；与 Vue 3 的集成方式（npm 包名 / 组件封装 / 原生 API / 是否需要 canvas 或 shader）；性能与可访问性考量（体积、GPU 开销、prefers-reduced-motion、降级方案）；候选评级 ★1-5 与一句话理由。
3. 结论必须落到"首页 Bento 仪表盘能怎么用"（背景层 / widget 层 / 交互层 / 入场动效），不产论文式清单。
4. 用 write_file 把完整笔记写到：<本轮目录>/<文件名>
   若该路径已有旧内容，覆盖前先确认是同一轮（round-NN 不同则新建）。
5. 最后用一句话回答：本域最推荐的 3 个方向 + 各自评级。
```

## 收敛规则

- 默认 1 轮大面积（6 域并行）+ 1 轮深挖（针对评分最高的 2-3 个方向做 POC 级调研），用户可指定轮数
- 每轮末尾生成 `round-NN/README.md`：本轮摘要 + 下一轮待深挖清单
- 全部完成后生成 `docs/rendering-research/综合报告.md`：技术选型矩阵（技术 × 首页层 × 评级 × 成本）× 三阶段改造路线图（低风险 CSS/动效层 → 交互增强层 → 可选 WebGL 层）× 风险清单

## 安全约定

- 调研 agent 只读 + 只写自己的笔记文件，禁止改源码
- 涉及 git 提交/切换前先跑 `bash scripts/check-uncommitted.sh`（worktree 安全约定）
- 汇总报告要附"先决条件"：哪些需要用户确认（如是否接受 WebGPU/WebGL 依赖、性能预算目标、是否支持 reduced-motion 降级）
