# 渲染与动效方案文档体系修订设计

日期：2026-08-04
状态：已获用户原则批准，等待书面规格复核
范围：`docs/rendering-research/` 文档体系，不修改业务代码或依赖

## 1. 目标

把现有两轮渲染调研整理成一套口径一致、证据可追溯、代码示例契约完整，并能直接拆给多个子代理执行的最终方案。

完成后的文档必须同时满足：

1. 《综合报告》是唯一当前决策基线，不再与 Round README 或 POC 笔记互相冲突。
2. Round README 只承担导航、摘要和状态索引，不重复制造第二套决策。
3. POC 笔记保留证据和实现细节，但所有标为“可粘贴”的示例必须接口一致。
4. 兼容性、体积和性能结论区分“静态推断”“构建实测”“Electron 实机验收”。
5. 实施工作包按文件所有权拆分，可以并行交给多个子代理，且不会同时编辑同一文件。

## 2. 文档权威关系

文档分为三层：

| 层级 | 文档 | 职责 | 是否可作为当前实施依据 |
|---|---|---|---|
| 决策层 | `综合报告.md` | 当前选型、阶段、预算、风险、任务卡与放行门槛 | 是，唯一基线 |
| 导航层 | `round-01/README.md`、`round-02/README.md` | 记录每轮输入、产出、结论演进和指向综合报告 | 否 |
| 证据层 | R1 六份域笔记、R2 三份 POC 笔记 | 来源、实验数据、代码骨架和备选方案 | 仅作为证据与实现参考 |

当证据层与决策层冲突时，以《综合报告》为当前实施口径，同时在证据层标明其结论所属轮次，不能静默改写历史判断。

产物总数统一写为 12 份 Markdown：R1 六份域笔记和一份 README，R2 三份 POC 笔记和一份 README，外加一份综合报告。

## 3. 最终阶段模型

### Phase 1A：零依赖视觉底座

范围仅包括：

- `.bg-aurora` 与 `.bg-noise`；
- `WorkbenchFrame` 的 `background` slot；
- `BentoBackground` 的 CSS 模式与编辑态静止；
- `DashboardModuleCard` 的首页玻璃拟态与实心降级；
- reduced-motion、reduced-transparency、Storybook、截图和目标机性能门禁。

本阶段不安装 motion-v、@vueuse/core、regl、three、TresJS 或 tsParticles。它可以独立发布和回滚。

### Phase 1B：可选动效原语

只有用户批准 `motion-v + @vueuse/core` 的真实构建增量后才进入：

- `MotionWrapper` 进入 design-system；
- 统一时序 token、reduced-motion 和属性透传；
- 首页只接入轻量入场与 hover/press；
- 不在此阶段加入 countUp、confetti 或跨路由转场。

### Phase 2：交互动效

在 Phase 1B 验收后，按需加入 widget stagger、数字终态动画、一次性反馈和页面转场。每种动效只由一个系统驱动，同一元素不叠加 Vue Transition、View Transitions 与 motion-v。

### Phase 3：可降级 WebGL

默认不实施。确认需要 shader 背景时先选 regl；只有确认建设 3D 热力图时才评估 TresJS/three。任何 WebGL 方案必须通过能力探测、加载失败、context lost 和 reduced-motion 四条降级路径。

## 4. 必须修正的实现契约

### 4.1 MotionWrapper

- Vue 对象属性使用 `:while-hover` 和 `:while-press`，禁止把对象字面量作为字符串传递。
- reduced-motion 状态既支持初始读取，也要描述媒体查询变化后的更新行为。
- 测试只断言结构和终态，不依赖动画中间帧。
- Storybook decorator 与组件内部策略不能产生两套相互矛盾的 reduced-motion 默认值。

### 4.2 背景模式

- 区分 `preferredMode`、`resolvedMode` 和 `fallbackReason`。
- `auto` 只在用户明确启用动态背景后生效；默认始终是 `css`。
- 粒子或 WebGL chunk 加载失败时，必须显式设置 `resolvedMode='css'`，不能让异步组件解析为 `undefined` 后留下空层。
- 模式持久化只保存用户选择，不保存一次性的能力探测结果。

### 4.3 WebGL 能力与生命周期

- `useWebglSupport` 返回组件可更新的本地状态；不能返回 readonly ref 后再从组件赋值。
- 能力探测函数可注入，测试和 Story 之间不得共享不可重置的模块级结果。
- 探测 canvas 成功创建 context 后应主动释放，或直接在实际渲染 canvas 上完成探测，避免占用额外 context。
- `initBackground` 统一返回 `{ renderer, resize, stop, dispose }`；调用方不得再解构不存在的嵌套对象。
- `dispose` 负责停循环、移除事件、断开 ResizeObserver、释放引擎资源和归还全局 slot。
- context lost 后立即停帧并进入 CSS fallback；只有明确的恢复流程才能重新进入 WebGL，最多尝试三次。
- context 预算器必须真实通知并释放被驱逐实例，不能只从 Map 删除记录。

## 5. 度量与兼容性口径

### 5.1 包体积

“首屏增量 0”不再作为笼统结论。每个候选必须报告：

1. 入口 chunk gzip；
2. 首次打开 Home 所需全部 JS 请求 gzip 总和；
3. 启用对应模式后新增的异步 chunk gzip；
4. Electron `file://` 下的 minified 字节数与解析耗时。

`defineAsyncComponent` 只能证明代码不在入口 chunk。若保存的模式在首页首次渲染时立即请求 WebGL chunk，该请求仍属于首次首页加载成本。

### 5.2 Electron

Electron 28 对应 Chromium 120 的 CSS/API 支持可标记为“静态兼容”。当前 Electron 运行链仍处于搁置状态，因此不能写“Electron 已验证兼容”。只有 Electron 能正常启动并完成目标机测试后，才能升级为“实机通过”。

### 5.3 性能

固定门禁：

- 首页活跃 WebGL context 目标不超过 2，硬上限 3；
- 合成层目标不超过 18，临时硬上限 22；
- 目标 Electron 机器录制 5 秒，编辑拖拽和普通静置分别检查长帧；
- 玻璃拟态不达标时按顺序降级为静态背景、blur 12px、实心卡片；
- reduced-motion 和 reduced-transparency 必须有独立终态验证。

预算值是项目门禁，不再描述为浏览器保证值。

## 6. 多子代理执行模型

所有代理共享当前工作树。禁止切分支、合并、checkout、清理 worktree 或修改未分配文件。执行前必须阅读根 `AGENTS.md`，并通过管家任务卡认领和回传结果。

### Wave 1：三个 POC 并行修订

| 工作包 | 独占文件 | 主要任务 | 完成条件 |
|---|---|---|---|
| W1-A Motion | `round-02/01-motion-v-integration.md` | 修正 Vue 绑定、reduced-motion、体积度量与 Phase 1B 口径 | 示例和测试契约一致，无“已落定即实施”表述 |
| W1-B WebGL | `round-02/02-tresjs-lazy-fallback.md` | 修正状态可写性、返回契约、缓存隔离、fallback、slot 驱逐和体积语义 | 四条降级路径完整，示例接口闭合 |
| W1-C CSS | `round-02/03-css-background-impl.md` | 收敛为 Phase 1A，补实心降级和真实性能门禁 | 不依赖未批准的粒子/WebGL/motion 实现 |

### Wave 2：汇总文档串行统一

Wave 1 全部完成后执行：

| 工作包 | 独占文件 | 主要任务 | 完成条件 |
|---|---|---|---|
| W2-A 综合报告 | `综合报告.md` | 建立唯一决策基线、四阶段模型、预算口径、风险、任务卡 | 与三个修订 POC 一致 |
| W2-B 轮次索引 | `round-01/README.md`、`round-02/README.md` | 标注文档角色、修正 12 份清单、同步阶段摘要 | 不再产生独立决策口径 |

### Wave 3：独立审查

审查代理不修改文件，只输出发现：

- 搜索残留的“9 份”“首屏增量 0”“Electron 全兼容”“Phase 1 已落定 motion-v”；
- 对照所有代码块的变量名、返回值和调用方式；
- 检查每个任务卡是否有任务、已知、定位、范围、验收五行；
- 检查 Wave 1/2 的文件所有权无重叠；
- 检查没有 TBD、TODO、未定义阈值或互相冲突的状态标记。

发现阻断问题时，退回原文件所有者修正，再由审查代理复核。

## 7. 任务卡标准

《综合报告》附录为每个工作包提供五行卡：

```text
【任务】一个代理只负责一个明确结果
【已知】已经验证的事实与上游工作包输出
【定位】独占文件、引用来源和相关代码位置
【范围】允许修改与明确禁止修改的边界
【验收】可运行命令、文本检查和人工检查结果
```

每张卡还必须标明：工作包 ID、依赖的 Wave、是否可并行、回传证据格式。管家生成的五行任务卡原样用于代理交接，报告中的卡片是稳定的人类可读基线。

## 8. 文档修订验收

最终交付通过以下检查才可称为“可直接移交”：

1. 六个目标文档完成修订，R1 六份域笔记保留历史内容不做无关重写。
2. 全目录只存在一套阶段命名和一套当前决策状态。
3. 所有标为可粘贴的代码块满足变量、可变性、返回值和调用方契约一致。
4. Electron、体积和性能结论均带验证级别，不把估算写成实测。
5. 五个写作工作包和一个独立审查工作包均有可直接交接的五行任务卡。
6. `git diff --check` 通过；Markdown 标题、表格和本地路径检查通过。
7. 未修改业务代码、依赖文件、项目记忆或其他工作树内容。

## 9. 非目标

- 本轮不实现 CSS、MotionWrapper、粒子或 WebGL 代码。
- 本轮不安装依赖、不生成截图基线、不恢复 Electron 运行链。
- 本轮不替用户批准 motion-v、WebGL、玻璃性能风险或 3D 热力图。
- 本轮不清理、提交或覆盖现有调研文档之外的未提交内容。
