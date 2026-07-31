# Study-Hub 协作入口

本工作区涉及项目操作时，管家是唯一入口。用户不需要选择页面、功能区域、前端或后端、角色或工具名。

## 何时进入管家

当用户要求排查、修复、修改、新增、删除、检查、测试、发布、部署，或研究当前项目的外部方案时：

1. 先调用 `mcp__study_hub__butler_open_case` 登记任务；
2. 立即调用 `mcp__study_hub__butler_next_action`，只按返回的下一步继续；
3. 定位后调用 `mcp__study_hub__butler_record_context`；分派角色或领域专家后调用 `mcp__study_hub__butler_assign`；
4. 每次调查或修复调用 `mcp__study_hub__butler_record_attempt`；
5. 删除、个人数据、账号权限、发布、部署或其他高影响操作，先调用 `mcp__study_hub__butler_request_approval`，等待用户明确同意；
6. 实际改动后依次调用 `mcp__study_hub__butler_record_change`、`mcp__study_hub__butler_record_audit`、`mcp__study_hub__butler_record_validation`，再调用 `mcp__study_hub__butler_complete_case`。

先用自然语言理解问题，再从 `project-memory/功能代号地图.md` 和相关项目记录中定位。内部角色和外部专家由管家自动选择，不让用户承担内部编排。

## 何时不进入管家

纯概念解释、普通闲聊、与本工作区无关的问题，以及尚未要求调查或改动的想法讨论，不创建管家任务。

## 完成标准

不能把“已经登记任务”当成“已经解决问题”。完成前必须有真实检查结果和对用户原始现象的验证。连续三次没有进展时，停止继续尝试，向用户说明阻塞原因并等待新方向。
