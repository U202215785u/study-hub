# Study-Hub AI 协作架构 v3.0：负责人群体 + RAG 底座

> ⚠️ **历史设计文档**。v3.0 架构未全面实施，部分内容已过时。
> 负责人文件已迁移至 `.agents/owners/`。当前活跃协议见根目录 `CLAUDE.md`。
> 本文档保留作为设计参考和未来迭代方向。
>
> 你不是在管理一套流程，你是在管理一个虚拟团队。
> 每个负责人有自己的记忆、自己的领域、自己的责任感。

---

## 一、方案演进

| 版本 | 核心思路 | 问题 | 结论 |
|------|---------|------|------|
| v1.0 | 13 角色模拟公司架构 | 角色切换成本极高，文档同步递归地狱 | 废弃 |
| v2.0 | 6 角色流程方案（架构师→实现者→审计者） | 角色太抽象（"实现者"不是人），没有领域记忆 | 方向正确，角色设计错误 |
| **v3.0** | **负责人群体 + RAG 底座** | — | **本方案** |

**v2.0 → v3.0 的关键转变：**

- v2.0：AI 是"临时工面具"，按流程穿戴（架构师→实现者→审计者）
- v3.0：AI 是"终身负责人"，每人有自己的领域记忆和责任感

**例子：brainstorm 模块改了 5 次**
- v2.0：每次找"实现者"，重新解释上下文 → 重复踩坑
- v3.0：找"brainstorm 负责人"，他记得前 4 次为什么改 → 不踩同一个坑

---

## 二、核心设计原则

### 原则 1：负责人有身份、有记忆、有责任感

不是"前端工程师"这种通用角色，而是：
- "brainstorm 模块负责人" —— 对 brainstorm 的一切终身负责
- "UI 设计负责人" —— 对 study-hub 的视觉风格终身负责
- "前端技术负责人" —— 对 Vue 代码规范和技术选型终身负责

### 原则 2：RAG 是底层器官，不是独立工具

RAG 不作为一个"阶段化功能"存在，而是每个负责人的"眼睛和神经系统"：
- 激活负责人时，自动检索领域相关文件
- 回答问题时，精确定位代码位置
- 发现记忆过期时，主动报告

### 原则 3：文档流水线是交接机制

负责人之间不直接对话，通过标准交付物文档交接：
```
产品经理 → PRD.md → UI 设计负责人 → design-ui.md → 前端技术负责人 → 代码
```

### 原则 4：管家负责"组建临时团队"

用户不需要自己判断"这次需要谁"，管家根据任务类型推荐团队名单。

### 原则 5：用户始终是最终决策者和验收者

负责人可以建议、可以反对、可以提醒，但最终拍板权在你。

---

## 三、角色体系：12 位负责人

### 3.1 角色总览

```
你打开 AI
    │
    ▼
  管家（唯一入口）
    │
    ├── 新功能 → 组建团队：产品经理 + 模块负责人 + 设计负责人 + 技术负责人 + QA
    │
    ├── 修 bug → 组建团队：模块负责人 + 调试者 + 技术负责人 + QA
    │
    ├── 视觉改版 → 组建团队：UI 设计负责人 + 交互负责人 + 前端技术负责人
    │
    ├── 上线部署 → 组建团队：DevOps 负责人 + 模块负责人 + QA
    │
    └── 不知道怎么办 → 读 state.md，告诉你现在该找谁
```

### 3.2 协调层

| 负责人 | 职责 | 不可替代性 |
|--------|------|-----------|
| **管家** | 判断任务类型，组建临时团队，推荐工作顺序 | 没有管家，你不知道该激活谁 |
| **产品经理** | 需求梳理、写 PRD、验收功能是否符合需求 | 没有 PM，需求理解错误无法被发现 |

### 3.3 模块负责人（纵向：对模块终身负责）

| 负责人 | 管什么 | 核心能力 |
|--------|--------|---------|
| **brainstorm 负责人** | brainstorm 模块的一切：Prompt 模板、选项逻辑、前端交互 | 知道选项从 3 减到 2 的历史，知道解析逻辑多脆弱 |
| **learning 负责人** | learning 模块的一切：学习计划、路径推荐、清单功能 | 知道数据结构怎么设计的，知道下一步该加什么 |
| **automation 负责人** | automation 模块的一切：抖音/B 站/小红书解析、ASR 逻辑 | 知道三级降级的坑，知道 ffmpeg 超时的根因 |
| **wiki 负责人** | wiki/knowledge 模块的一切：知识库、向量搜索、文档管理 | 知道 ChromaDB 的索引策略，知道分块逻辑 |

### 3.4 设计负责人（横向：对设计规范终身负责）

| 负责人 | 管什么 | 核心能力 |
|--------|--------|---------|
| **UI 设计负责人** | 所有页面的视觉风格、配色、组件外观、品牌一致性 | 知道 study-hub 的主色是什么，知道按钮圆角多少 |
| **交互设计负责人** | 所有页面的用户流程、点击路径、信息架构 | 知道从首页到功能完成的最短路径，知道哪里容易迷路 |
| **动效负责人** | 所有动画、过渡效果、微交互 | 知道哪些动画提升体验，哪些是炫技干扰 |

### 3.5 技术负责人（横向：对技术栈终身负责）

| 负责人 | 管什么 | 核心能力 |
|--------|--------|---------|
| **前端技术负责人** | Vue 3 / HTML / CSS / JS 技术栈、代码规范、组件库 | 知道为什么用 ref 不用 reactive，知道目录结构约定 |
| **后端技术负责人** | FastAPI / Python / SQLite / ChromaDB 技术栈 | 知道 API 返回格式规范，知道数据库索引策略 |
| **DevOps 负责人** | Docker / 部署 / 上线 / 环境配置 / CI/CD | 知道怎么从本地跑通到生产环境，知道环境变量怎么配 |

### 3.6 质量负责人（横向：对质量终身负责）

| 负责人 | 管什么 | 核心能力 |
|--------|--------|---------|
| **QA 负责人** | 测试策略、功能验证、回归测试、质量标准 | 知道哪些功能容易坏，知道测试覆盖率缺口 |

---

## 四、记忆系统：三层设计

每个负责人的记忆分为三层，每层有不同的维护方式和加载策略。

### 4.1 Layer 3：活跃记忆（每次必加载，<5KB）

存在负责人文件的前半部分，是负责人的"工作记忆"。

内容：
- 我的领域是什么（一句话定义）
- 当前技术栈和关键文件
- 最近 5 个决策（含日期和原因）
- TOP 10 已知陷阱
- TOP 5 演进方向
- 领域文件索引（RAG 阶段 1）
- 检索关键词映射（RAG 阶段 1）

### 4.2 Layer 2：RAG 实时检索（按需加载，动态生成）

负责人的"眼睛"——回答具体问题时，实时扫描代码找到相关片段。

内容：
- 用户问"收藏按钮在哪？" → RAG 找到精确文件+函数+行号
- 用户问"ASR 降级逻辑是什么？" → RAG 找到 automation.py 相关代码
- 自检时发现"记忆里的文件路径和实际不符" → RAG 报告过期

**对用户的透明度：** 用户看不到 RAG 的存在，只看到负责人回答时附带精确的文件位置。

### 4.3 Layer 1：归档记忆（需要时手动加载）

负责人的"档案室"——完整的历史记录，需要深挖时才打开。

内容：
- 完整决策历史 → `project-memory/[模块]/decisions.md`
- 完整变更记录 → `project-memory/[模块]/changelog.md`
- 历史陷阱和教训 → `project-memory/[模块]/lessons.md`

**加载方式：** 负责人说"我需要查一下历史"，然后读归档文件。

---

## 五、RAG：负责人的器官

### 5.1 RAG 不是工具，是能力

v2.0 把 RAG 当成"阶段性工具"（阶段 0 → 阶段 1 → 阶段 2）。
v3.0 把 RAG 当成负责人的"内置能力"——从出生就有，随成长增强。

### 5.2 RAG 阶段 1：领域文件索引（立即可用）

每个负责人的记忆文件顶部自带索引：

```markdown
## 领域文件索引（RAG 阶段 1：确定性检索）

| 文件路径 | 类型 | 最后验证日期 | 关键内容摘要 |
|---------|------|------------|-------------|
| backend/endpoints/brainstorm.py | 后端 API | 2026-05-28 | step2/step3 路由，选项生成 |
| backend/core/brainstorm_engine.py | 核心逻辑 | 2026-05-26 | Prompt 模板，parse_step2_response |
| frontend/views/Brainstorm.vue | 前端页面 | 2026-05-27 | 选项展示，收藏按钮（新增） |
| frontend/components/OptionCard.vue | 组件 | 2026-05-25 | 选项卡片 UI |

## 检索关键词映射（RAG 阶段 1：快速定位）

| 关键词 | 对应文件/函数 |
|--------|-------------|
| 选项生成 | brainstorm_engine.py → generate_options() |
| 选项展示 | Brainstorm.vue → <OptionCard> |
| 收藏 | favorite_option() 或 <FavoriteButton> |
| Prompt | STEP2_IDEA_PROMPT 常量 |
| 解析 | parse_step2_response() |
```

**激活负责人时，AI 自动读这个索引，就知道"我的领域有哪些文件"。**

### 5.3 RAG 阶段 2：语义检索（代码量 >100 文件时启用）

当索引无法覆盖全部代码时，启用 ChromaDB 向量检索：
- 索引回答不了的问题 → 语义检索补充
- 检索结果反馈给负责人 → 负责人判断"这个文件确实属于我的领域"
- 新发现的关联文件 → 回写进索引，让索引自动增长

### 5.4 RAG 的四个职责

| 职责 | 场景 | 用户感知 |
|------|------|---------|
| **自检记忆是否过期** | 激活时发现"记忆里的文件路径和实际不符" | 负责人说"我的记忆可能过期了，让我确认一下" |
| **回答问题时代码定位** | 用户问"收藏按钮在哪？" | 负责人回答"在 Brainstorm.vue 第 156 行" |
| **跨模块影响分析** | 改 shared_utils.py 时 | 负责人说"这会影响 brainstorm、learning、automation" |
| **辅助更新记忆文件** | 代码变更后 | 负责人收到"你的领域有变更，建议更新记忆" |

---

## 六、负责人文件标准格式

每个负责人文件遵循统一格式，8 个固定段落：

```markdown
# [姓名] 负责人

## 1. 身份与领域
我是谁、我管什么、我的专业背景、我的思维方式。

## 2. 核心职责
我唯一不可替代的工作是什么。绝不越界做什么。

## 3. 活跃记忆（Layer 3）
### 当前技术栈
### 最近 5 个决策
### TOP 10 已知陷阱
### TOP 5 演进方向

## 4. 领域文件索引（RAG 阶段 1）
### 文件清单
### 检索关键词映射

## 5. 协作边界
我和谁交接、我的输入是什么、我的输出是什么、我不做什么。

## 6. 交付物格式
我产出的文档必须长什么样（模板）。

## 7. 记忆更新规则
对话结束时，我如何更新自己的记忆文件。

## 8. 成功指标
怎么判断一次对话有没有价值。
```

---

## 七、工作流程：以"组建临时团队"为核心

### 7.1 场景一：新功能开发（完整流程）

**任务**：给 brainstorm 加"选项收藏"功能

```
Step 1: 找管家组建团队
─────────────────────
你：@.agents/owners/butler.md @project-memory/state.md
    我想给 brainstorm 加一个选项收藏功能

管家：【团队组建建议】
      这个任务需要：
      1. 产品经理 —— 写 PRD，明确收藏的行为逻辑
      2. brainstorm 负责人 —— 评估对模块的影响
      3. UI 设计负责人 —— 收藏按钮的视觉设计
      4. 前端技术负责人 —— 按钮实现 + 状态管理
      5. 后端技术负责人 —— 收藏 API
      6. QA 负责人 —— 验证

      建议流程：
      产品经理写 PRD → brainstorm 负责人评估 → UI 设计 → 前后端并行实现 → brainstorm 负责人验收 → QA 测试

Step 2: 产品经理写 PRD
─────────────────────
你：@.agents/owners/product-manager.md @project-memory/state.md
    给 brainstorm 加选项收藏功能，写 PRD

产品经理产出：project-memory/features/option-favorite/prd.md

Step 3: brainstorm 负责人评估
──────────────────────────
你：@.agents/owners/brainstorm-owner.md
    @project-memory/features/option-favorite/prd.md
    评估一下这个需求对你的模块有什么影响

brainstorm 负责人：
- 读自己的活跃记忆
- 读 PRD
- RAG 检索相关代码确认现状
- 产出评估报告（附在 PRD 后面或单独文件）

Step 4: UI 设计负责人出视觉方案
──────────────────────────────
你：@.agents/owners/ui-design-owner.md
    @project-memory/features/option-favorite/prd.md
    设计收藏按钮的视觉方案

UI 设计负责人产出：project-memory/features/option-favorite/design-ui.md

Step 5: 前端技术负责人实现
─────────────────────────
你：@.agents/owners/frontend-tech-owner.md
    @project-memory/features/option-favorite/prd.md
    @project-memory/features/option-favorite/design-ui.md
    实现收藏按钮

前端技术负责人：写代码，产出变更摘要

Step 6: 后端技术负责人实现 API
─────────────────────────────
你：@.agents/owners/backend-tech-owner.md
    @project-memory/features/option-favorite/prd.md
    实现收藏 API

后端技术负责人：写代码，产出变更摘要

Step 7: brainstorm 负责人验收
───────────────────────────
你：@.agents/owners/brainstorm-owner.md
    收藏功能实现了，你验收一下是否符合模块要求

brainstorm 负责人：
- 测试功能是否破坏选项生成流程
- 测试收藏状态是否持久化
- 确认是否符合模块演进方向
- 产出验收结论

Step 8: QA 负责人最终测试
─────────────────────────
你：@.agents/owners/qa-owner.md
    跑一遍测试

QA 负责人：按检查清单逐项验证，产出测试报告

Step 9: 各负责人更新记忆
───────────────────────
对话结束时，每个参与负责人更新自己的活跃记忆。
```

### 7.2 场景二：修 bug（精简流程）

**任务**：automation 抖音解析失败

```
Step 1: 找管家
─────────────────────
你：automation 抖音解析总是失败

管家：【团队组建建议】
      现象明确但原因不明 → 建议先找 automation 负责人评估
      如果原因是代码问题 → 找后端技术负责人修复
      最后 QA 验证

Step 2: automation 负责人评估
───────────────────────────
你：@.agents/owners/automation-owner.md
    抖音解析总是失败，看看怎么回事

automation 负责人：
- 读自己的活跃记忆
- RAG 检索 ASR 相关代码
- 判断：是 ASR 超时问题，已知陷阱
- 产出：根因定位 + 修复建议

Step 3: 后端技术负责人修复
─────────────────────────
你：@.agents/owners/backend-tech-owner.md
    automation 负责人说 ASR 超时，定位到 endpoints.py 第 156 行，修复一下

后端技术负责人：修复代码，产出变更摘要

Step 4: QA 验证
───────────────
你：@.agents/owners/qa-owner.md
    验证 ASR 修复

QA 负责人：测试，产出报告

Step 5: 更新记忆
───────────────
automation 负责人更新已知陷阱
后端技术负责人更新技术栈记忆
QA 负责人更新测试记录
```

### 7.3 场景三：视觉改版（设计主导流程）

**任务**：study-hub 整体视觉升级

```
Step 1: 管家组建设计团队
─────────────────────
UI 设计负责人 + 交互设计负责人 + 动效负责人 + 前端技术负责人

Step 2: UI 设计负责人出视觉方案
──────────────────────────────
产出：design-system.md（设计系统规范）

Step 3: 交互设计负责人优化流程
─────────────────────────────
读 design-system.md，产出优化后的用户流程

Step 4: 动效负责人补充动画规格
─────────────────────────────
读 design-system.md，产出动画规格文档

Step 5: 前端技术负责人实现
─────────────────────────
读所有设计文档，按模块逐个实现
每改一个模块，找该模块负责人验收

Step 6: QA 回归测试
──────────────────
验证所有页面是否正常
```

### 7.4 场景四：不知道从哪开始

```
你：@.agents/owners/butler.md @project-memory/state.md
    帮我看看现在该做什么

管家：读 state.md 优先级列表 + 各模块健康度
      告诉你："当前 P0 是 ASR 修复（等待验收），P1 是 brainstorm 选项缩减..."
      建议你先验收 ASR，完成后再推进下一个
```

---

## 八、交付物文档标准格式

每个负责人产出必须遵循标准格式，存入 `project-memory/features/[功能名]/`

### 8.1 PRD（产品经理产出）

```markdown
# PRD: [功能名]

## 背景
为什么要做这个功能

## 目标
- 用户目标：用户能做什么
- 业务目标：对项目有什么价值

## 功能描述
### 核心流程
1. 用户打开...
2. 用户点击...
3. 系统返回...

### 边界情况
- 空状态：...怎么处理
- 错误状态：...怎么提示
- 权限：...是否需要登录

## 验收标准
- [ ] 标准1
- [ ] 标准2

## 影响范围
- 涉及模块：brainstorm / learning / ...
- 涉及页面：...
- 风险点：...
```

### 8.2 视觉设计文档（UI 设计负责人产出）

```markdown
# 视觉设计: [功能名]

## 整体风格
[描述]

## 配色
- 主色：#xxx
- 辅助色：#xxx
- 背景色：#xxx

## 布局
[描述主要区域分布]

## 组件细节
| 组件 | 尺寸 | 样式 | 状态 |
|------|------|------|------|
| 按钮 | 120x40 | 圆角 8px，主色填充 | default / hover / disabled |

## 动画/过渡
[如果有]

## 响应式
- 桌面端：...
- 移动端：...
```

### 8.3 技术实现文档（技术负责人产出）

```markdown
# 技术实现: [功能名]

## 改动范围
| 文件 | 改动类型 | 说明 |
|------|---------|------|
| xxx.py | 修改 | 新增 API |
| xxx.vue | 新增 | 新组件 |

## 接口定义
```
POST /api/xxx
Request: { ... }
Response: { ... }
```

## 关键逻辑
[描述核心算法或流程]

## 已知风险
- [ ] 风险1及应对措施
```

### 8.4 测试报告（QA 负责人产出）

```markdown
# 测试报告: [功能名]

## 测试环境
- 分支：...
- 浏览器：...

## 测试结果
| 检查项 | 结果 | 备注 |
|--------|------|------|
| 核心流程 | 通过/失败 | ... |
| 边界情况 | 通过/失败 | ... |
| 回归测试 | 通过/失败 | ... |

## 发现的问题
1. [问题描述] — [严重程度] — [建议]

## 总体评估
[通过 / 有条件通过 / 不通过]
```

---

## 九、文件目录结构

```
study-hub/
│
├── .agents/owners/                        # 负责人定义（12 个文件）
│   ├── butler.md                          # 管家：团队组建
│   ├── product-manager.md                 # 产品经理
│   ├── brainstorm-owner.md                # brainstorm 模块负责人
│   ├── learning-owner.md                  # learning 模块负责人
│   ├── automation-owner.md                # automation 模块负责人
│   ├── wiki-owner.md                      # wiki 模块负责人
│   ├── ui-design-owner.md                 # UI 设计负责人
│   ├── ux-design-owner.md                 # 交互设计负责人
│   ├── motion-owner.md                    # 动效负责人
│   ├── frontend-tech-owner.md             # 前端技术负责人
│   ├── backend-tech-owner.md              # 后端技术负责人
│   ├── devops-owner.md                    # DevOps 负责人
│   └── qa-owner.md                        # QA 负责人
│
├── project-memory/                        # 项目中央记忆库
│   ├── state.md                           # 全局状态（优先级、健康度）
│   ├── decisions.md                       # 全局决策日志
│   ├── issues.md                          # 全局问题清单
│   ├── features/                          # 功能交付物
│   │   └── [功能名]/
│   │       ├── prd.md                     # 产品经理产出
│   │       ├── design-ui.md               # UI 设计产出
│   │       ├── design-ux.md               # 交互设计产出
│   │       ├── design-motion.md           # 动效产出
│   │       ├── tech-spec.md               # 技术方案
│   │       ├── test-report.md             # 测试报告
│   │       └── handoff.md                 # 交接记录
│   │
│   ├── brainstorm/                        # brainstorm 模块归档
│   │   ├── decisions.md
│   │   ├── changelog.md
│   │   └── lessons.md
│   ├── learning/                          # learning 模块归档
│   ├── automation/                        # automation 模块归档
│   └── wiki/                              # wiki 模块归档
│
└── rag-index/                             # RAG 工作区（阶段 2 启用）
    ├── rebuild.py                         # 索引重建脚本
    └── index/                             # ChromaDB 索引文件
```

---

## 十、与外部项目的对比

| 维度 | gstack (Garry Tan) | ClawCompany | agency-agents | **v3.0 本方案** |
|------|-------------------|-------------|---------------|----------------|
| **本质** | Claude Code 技能包 | AI 公司 OS | IDE 角色注入 | **负责人 + RAG 底座** |
| **角色数** | 23 | 38 | 112 | **12** |
| **角色粒度** | 命令级（/review） | 公司级（CEO/CTO） | 专业级（Backend Architect） | **模块/职能级** |
| **记忆** | gbrain（Supabase） | 4 层压缩记忆 | 无 | **Markdown 文件 + RAG 索引** |
| **记忆可解释性** | 中 | 低（黑箱压缩） | — | **高（明文文件）** |
| **自主性** | 中 | 高 | 低 | **低（用户控制每一步）** |
| **RAG/检索** | gbrain 语义搜索 | 内置工具 | 无 | **负责人自带领域索引** |
| **安装门槛** | git + Bun + Node.js | Node.js 20+ | shell | **零安装（纯 Markdown）** |
| **适用用户** | 会用 Claude Code 的开发者 | 技术用户 | 开发者 | **不懂代码的 vibe coding 用户** |

**v3.0 的独特定位：**
> 唯一一个为"不懂代码、不想安装任何东西、但需要管理复杂项目"的用户设计的 AI 协作系统。

---

## 十一、实施计划

### 第 0 天（5 分钟）：创建目录

```bash
# 创建目录结构
mkdir -p study-hub/.agents/owners
mkdir -p study-hub/project-memory/features
mkdir -p study-hub/project-memory/brainstorm
mkdir -p study-hub/project-memory/learning
mkdir -p study-hub/project-memory/automation
mkdir -p study-hub/project-memory/wiki
```

### 第 1 天（30 分钟）：生成负责人初稿

和 Kimi CLI 做一次"元对话"：

```
你是架构师。请扫描 study-hub 项目的完整代码，为每个模块和职能生成
负责人初稿。需要生成以下 13 个文件：

1. .agents/owners/butler.md —— 管家
2. .agents/owners/product-manager.md —— 产品经理
3. .agents/owners/brainstorm-owner.md —— brainstorm 模块负责人
4. .agents/owners/learning-owner.md —— learning 模块负责人
5. .agents/owners/automation-owner.md —— automation 模块负责人
6. .agents/owners/wiki-owner.md —— wiki 模块负责人
7. .agents/owners/ui-design-owner.md —— UI 设计负责人
8. .agents/owners/ux-design-owner.md —— 交互设计负责人
9. .agents/owners/motion-owner.md —— 动效负责人
10. .agents/owners/frontend-tech-owner.md —— 前端技术负责人
11. .agents/owners/backend-tech-owner.md —— 后端技术负责人
12. .agents/owners/devops-owner.md —— DevOps 负责人
13. .agents/owners/qa-owner.md —— QA 负责人

每个文件必须包含：
1. 身份与领域
2. 核心职责
3. 活跃记忆（基于代码扫描生成）
4. 领域文件索引（RAG 阶段 1）
5. 检索关键词映射（RAG 阶段 1）
6. 协作边界
7. 交付物格式
8. 记忆更新规则

同时生成：
- project-memory/state.md（全局状态初稿）
- project-memory/decisions.md（决策日志模板）
- project-memory/issues.md（问题清单模板）
```

### 第 2-7 天：日常试用

- 每次任务先找管家
- 按管家推荐的团队顺序激活负责人
- 每个负责人对话结束时，执行记忆更新
- 记录摩擦点：
  - 哪个负责人经常记忆过期？
  - 哪个步骤最冗余？
  - 什么情况下你会跳过流程？

### 第 2 周：优化负责人记忆

- 让活跃的负责人回顾自己的工作，补充陷阱和决策
- 合并冗余的交付物步骤（比如小改动不需要完整设计文档）
- 如果某个负责人从未被激活，考虑降级为"按需触发"

### 第 3 周+：按需升级 RAG

- 如果负责人经常找不到代码 → 启用阶段 2 语义检索
- 如果项目文件超过 100 个 → 写 rebuild.py 脚本
- 如果 Claude Desktop 使用频繁 → 让管家同时输出 Claude 可用格式

---

## 十二、风险与应对

| 风险 | 应对措施 |
|------|---------|
| 负责人记忆文件越来越大 | 活跃记忆限制 5KB，超出的历史归档到 `project-memory/[模块]/` |
| RAG 索引过期 | 负责人激活时自动比对索引和实际代码，不一致则报告 |
| 角色太多切换累 | 管家智能组建"最小必要团队"，小任务只派 2-3 人 |
| 交付物文档堆积 | 功能完成后，归档到 `project-memory/features/[功能名]/`，活跃区只保留进行中的 |
| 用户嫌流程太长 | 管家提供"快速模式"：小 bug 直接派模块负责人+技术负责人，跳过设计和 PM |
| 不懂代码无法验收 | QA 负责人产出可视化检查清单（通过/失败），你只需看结果 |

---

## 十三、最小可行验证（1 小时实验）

**目标**：验证"负责人 + 记忆"对你真的有用

**Step 1（5 分钟）**：创建 3 个空文件
- `.agents/owners/butler.md`
- `.agents/owners/automation-owner.md`
- `project-memory/state.md`

**Step 2（15 分钟）**：元对话生成初稿
```
扫描 study-hub/backend/endpoints/automation.py，生成 automation 负责人初稿。
要求：活跃记忆包含 ASR 三级降级的陷阱，领域文件索引列出相关文件。
```

**Step 3（15 分钟）**：激活负责人做真实任务
```
@.agents/owners/automation-owner.md
automation 抖音解析总是失败，帮我看看
```

**Step 4（15 分钟）**：关窗口，过 2 小时重新激活同一个负责人
```
@.agents/owners/automation-owner.md
上次 ASR 的问题，修好了吗？现在状态是什么？
```

**如果负责人能准确回答"上次定位到根因是 XXX，状态是已修复/未修复"——这套系统对你有用。**

---

*方案版本：v3.0*
*核心设计：负责人群体 + RAG 底座 + 文档流水线*
*适用：不懂代码的 vibe coding 用户，管理复杂长期项目*
