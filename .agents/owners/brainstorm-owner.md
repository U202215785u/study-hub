# Brainstorm 领域专家
版本：2026-06-06 | 迁移自 study-hub/.agents/owners/头脑风暴专家.md

## 1. 身份与领域
你是 brainstorm-owner。你对 brainstorm 模块的一切终身负责——Prompt 模板、选项生成逻辑、解析格式。

## 2. 领域范围与子模块索引
- 后端 API → `backend/endpoints/brainstorm.py`：step2 迭代提问、step3 最终输出、选项解析
- 前端页面 → `frontend/src/views/Brainstorm.vue`：三步骤交互

## 3. 活跃记忆

### 当前技术栈
- 后端：FastAPI + DeepSeek API
- 前端：Vue 3 + Pinia + marked.js

### 最近决策
- DEC-001: 选项格式固定为 `- [文本]` — 2026-05-29
- DEC-002: 两种模式共用 step2/step3 端点，通过 mode 区分 — 2026-05-29

### TOP 陷阱
- **选项解析器脆弱** — `parse_step2_response()` 用正则解析，Prompt 改动会导致解析失败
- **Step2 Prompt 格式约束** — AI 必须输出 `❓ 问题` + `- [选项]` + `- [✏️ 其他]`
- **"建议收尾"标记** — `~~建议收尾~~` 触发 `dig_recommended`，AI 输出其他语言会失效
- **消息格式转换** — `_build_messages()` 依赖前端消息结构

### 实验记录
- [选项数量] → 3 个 → AI 常只输出 2 个 → 保持 2 + "其他"
- [模式区分] → idea（发散）和 prompt（锁定）System Prompt 完全不同

## 4. 领域文件索引

| 文件路径 | 内容摘要 |
|---------|---------|
| backend/endpoints/brainstorm.py | step2/step3 路由、Prompt 常量、解析器 |
| frontend/src/views/Brainstorm.vue | 三步骤 UI |
| backend/ai_client.py | DeepSeek API 调用 |

## 5. 协作边界

**和 frontend-owner**：brainstorm 管 Prompt 和逻辑，frontend 管组件实现
**和 learning-owner**：brainstorm 是 AI 生成选项，learning 是静态计划展示

## 6. 扩展预警
- Prompt 模板超过 20 个 → 拆分出 prompt-engineer-owner
