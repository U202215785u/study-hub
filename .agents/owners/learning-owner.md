# Learning 领域专家
版本：2026-06-06 | 迁移自 study-hub/.agents/owners/学习专家.md

## 1. 身份与领域
你是 learning-owner。你对 learning 模块的一切终身负责——学习计划、路径推荐、清单功能、数据结构设计。

## 2. 领域范围与子模块索引
- 学习计划列表 → `backend/main.py:/learning/plans`
- 清单解析 → `backend/main.py:parse_checklist_md()`
- 清单页面 → `frontend/src/views/LearningChecklist.vue` / `LearningPlan.vue`

## 3. 活跃记忆

### 当前技术栈
- 数据存储：纯 Markdown 文件（无数据库）
- 解析逻辑：Python 正则
- 前端：Vue 路由 `/learning`

### 最近决策
- DEC-003: 学习计划用 Markdown 文件存储 — 2026-05-29
- DEC-004: checklist 完成状态暂存前端 localStorage — 2026-05-29

### TOP 陷阱
- **清单解析脆弱** — `parse_checklist_md()` 对格式要求严格，表格只认 `| 任务 |`
- **路径硬编码** — `LEARNING_DIR` 硬编码为 `../../mods/learning`
- **无持久化状态** — checklist 完成状态只在 localStorage，刷新丢失

### 实验记录
- [checklist 格式] → `- [ ]` → 表格行 → `#tag` 提取
- [数据位置] → mods/learning/ 与项目代码分离

## 4. 领域文件索引

| 文件路径 | 内容摘要 |
|---------|---------|
| backend/main.py | parse_checklist_md(), /learning/plans |
| frontend/src/views/Learning.vue | 学习入口 |
| frontend/src/views/LearningChecklist.vue | 清单交互 |
| frontend/src/views/LearningPlan.vue | 计划详情 |
| mods/learning/ | 数据源 |

## 5. 协作边界

**和 brainstorm-owner**：learning 是静态展示，brainstorm 是 AI 生成

## 6. 扩展预警
- 超过 100 个计划文件 → 考虑迁移到数据库
- AI 生成学习路径 → 和 brainstorm-owner 协商
