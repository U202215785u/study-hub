---
name: butler
description: Study-Hub 项目管家的 Claude 适配说明。适用于项目定位、任务卡交接、审计和验证。
---

# Study-Hub 管家（Claude 适配层）

## 规则来源

项目运行行为、风险确认和降级策略以工作区根目录的 `AGENTS.md` 为准。本文件不定义另一套步骤，也不要求 Claude 暴露内部角色给用户。

## 可用能力

- `butler_open_case`：登记自然语言项目请求；任务类型可省略。
- `butler_next_action`：读取当前建议步骤，不是普通排查的硬阻塞。
- `butler_record_context`：记录或补充定位、记忆来源和新鲜度。
- `butler_recommend_experts`、`butler_recommend_chain`：给出可采纳的建议，不自动分派。
- `butler_assign`：仅在实际选择角色或专家时记录。
- `butler_create_task_card`、`butler_get_task_card`：生成和读取五行任务卡。
- `butler_accept_task_card`、`butler_report_execution_result`：认领任务卡并回收执行结果；不自动创建会话。
- `butler_record_attempt`、`butler_record_change`、`butler_record_audit`、`butler_record_validation`、`butler_complete_case`：保留调查、改动、审查和验收记录。
- `butler_request_approval`：对删除、个人数据、权限、发布、部署等受保护操作请求确认。

## 降级

普通工具错误为 `fail_open`：继续低风险工作并在恢复后补录。受保护操作为 `fail_closed`：没有明确确认不得执行。
