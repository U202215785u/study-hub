# Study-Hub 协作入口

本工作区的项目请求先经过管家，以便定位、留痕和交接；用户不需要选择页面、功能区域、前后端、角色或工具名。

本文件是 Codex 在本工作区的**唯一行为规则来源**。`.claude/skills/butler/SKILL.md` 只保留给 Claude 的能力说明与开发参考，不重复或覆盖这里的流程。

## 普通任务：尽力登记，不阻塞工作

当用户要求排查、修复、修改、新增、删除、检查、测试、发布、部署，或研究当前项目的外部方案时：

1. 先调用 `mcp__study_hub__butler_open_case`；任务类型可留空，或直接使用用户的自然语言描述。
2. 成功登记后调用 `mcp__study_hub__butler_next_action` 作为建议，读取项目记忆和相关文件并调用 `mcp__study_hub__butler_record_context`。调查过程中可持续补充上下文。
3. 可调用 `mcp__study_hub__butler_recommend_experts` 与 `mcp__study_hub__butler_recommend_chain` 获取建议；建议不替代 Codex 判断，也不自动锁定角色或启动 Agent。实际分派才调用 `mcp__study_hub__butler_assign`。
4. 需要交给另一位 Agent 时，调用 `mcp__study_hub__butler_create_task_card`，把返回的五行任务卡原样交接。执行 Agent 用 `mcp__study_hub__butler_accept_task_card` 认领，并用 `mcp__study_hub__butler_report_execution_result` 回传结果。
5. 每次调查或修复尽量调用 `mcp__study_hub__butler_record_attempt`；实际改动后依次调用 `mcp__study_hub__butler_record_change`、`mcp__study_hub__butler_record_audit`、`mcp__study_hub__butler_record_validation`，再调用 `mcp__study_hub__butler_complete_case`。

若 MCP 不可用、参数错误、数据库短暂锁定或工具返回 `policy: fail_open`，这是**尽力登记**失败：Codex 可以继续只读定位、常规排查和低风险改动；恢复后补录任务、证据和验证。这是 fail-open（失败开放）策略。不要反复登记同一任务，更不要把工具失败误报为用户问题已解决。

## 高影响操作：必须确认

删除、个人数据、账号权限、发布、部署或其他高影响操作必须走 `mcp__study_hub__butler_request_approval`，并等待用户明确同意。出现 `policy: fail_closed` 或等待确认时，不得继续执行受保护操作；可以继续解释影响、准备方案和只读检查。

## 项目定位与协作边界

先用自然语言理解问题，再从 `project-memory/功能代号地图.md`、相关项目记录和代码中定位。任务卡保存生成时的事实快照、记忆来源和新鲜度；旧卡片不会被后续记忆静默改写。

任务卡用于交接、认领和结果回收，不会自动创建其他 Codex 会话或代替主 Agent 的审查、验证与合并判断。

## 何时不进入管家

纯概念解释、普通闲聊、与本工作区无关的问题，以及尚未要求调查或改动的想法讨论，不创建管家任务。

## 完成标准

不能把“已经登记任务”当成“已经解决问题”。完成前必须有真实检查结果和对用户原始现象的验证。连续三次没有进展（包括 `failed`、`error`、`timeout` 等）时，停止继续尝试，向用户说明阻塞原因并等待新方向。
