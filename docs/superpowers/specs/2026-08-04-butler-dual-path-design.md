# Study-Hub 管家双通道与接口精简设计

日期：2026-08-04
状态：用户已确认方向，待审阅方案

## 1. 背景与目标

当前管家把普通 Web Coding 任务也带入完整协作链：登记、读取下一步、记录上下文、角色分派、调查尝试、实施、改动记录、审查、验证和完成。这个链路适合复杂任务，但对单 Agent、低风险、小范围修改造成了额外 MCP 往返和等待。

本方案的目标是：

1. 普通任务默认走简单逻辑，不要求用户理解内部角色和阶段。
2. 只有用户明确说“复杂逻辑”时，才启用完整协作链。
3. 删除、部署、权限、个人数据、发布等高影响操作始终保留确认闸门，不受模式选择影响。
4. 对外减少接口调用次数，对内继续保留可审计的事件、状态和验证证据。
5. 同一任务只创建一个 `case_id`；模式由用户决定，不由系统自动猜测或自动升级。

## 2. 已确认的产品规则

### 2.1 模式选择

| 用户意图 | 管家模式 |
|---|---|
| 未特别说明的项目排查、修改、测试和普通 Web Coding | `simple` |
| 用户明确说“复杂逻辑”或等价表达 | `complex` |
| 高影响操作 | 当前模式不变，但强制插入 approval 闸门 |

“复杂逻辑”是用户授权的模式选择，不是管家根据文件数量、模块数量或风险自行推断的升级信号。系统可以提示“当前步骤需要复杂逻辑”，但不能未经用户同意自动切换。

### 2.2 安全边界

简单模式不等于跳过安全确认。以下操作仍必须调用 `request_approval`，并等待 `resolve_approval`：

- 删除文件、数据或项目资源；
- 发布、部署、上线或不可逆迁移；
- 个人数据处理；
- 账号、权限、密钥或访问范围变更；
- 其他由项目规则标记为高影响的操作。

确认只阻塞受保护操作本身，不把整个任务强制改造成复杂模式。

## 3. 当前链路与主要冗余

### 3.1 当前普通编码链路

```text
open_case
  -> next_action
  -> 读取项目记忆和代码
  -> record_context
  -> assign
  -> record_attempt（可能多次）
  -> begin_implementation
  -> 修改和测试
  -> record_change
  -> record_audit
  -> record_validation
  -> complete_case
```

此外，`mcp_tools.py` 的结果包装器会对带任务 id 的返回值再次计算 `next_action`。因此，`open_case` 等调用已经返回下一步时，调用方仍可能再次显式调用 `next_action`。

### 3.2 应保留的能力

- 一个稳定的任务 id 和原始用户描述；
- 高影响操作的审批记录；
- 失败尝试和三次无进展阻断；
- 实际改动、验证结果和最终状态；
- 复杂任务的角色、专家、任务卡和交接事件；
- 追加式事件记录，便于恢复和审计。

### 3.3 应从普通调用中移出的能力

- 普通任务强制显式调用 `next_action`；
- 普通任务强制 `record_context`；
- 普通任务强制 `assign`；
- 每次调查都记录 `record_attempt`；
- 将 `record_change`、`record_audit`、`record_validation`、`complete_case` 暴露为四个连续的普通调用；
- 普通管家记录工具上的逐次人工批准。

这些能力不删除，而是只在复杂模式或明确需要时使用。

## 4. 目标架构

### 4.1 简单模式

```text
butler_start_case(mode="simple")
  -> Codex 直接读取文件、修改代码和运行验证
  -> butler_finalize_case(...)
```

普通成功路径最多需要两次管家往返：开始和结束。高影响任务在执行受保护操作前增加一次审批往返。

### 4.2 复杂模式

```text
butler_start_case(mode="complex")
  -> butler_record_context
  -> butler_assign
  -> butler_record_attempt（按需）
  -> 可选任务卡和跨 Agent 交接
  -> butler_begin_implementation
  -> Codex 修改和验证
  -> butler_finalize_case(...)
```

复杂模式保留现有状态机和详细事件，只把最终收尾合并为一个聚合接口。

### 4.3 模式不会自动升级

如果简单模式执行中发现根因不明、范围扩大或需要其他 Agent，管家返回“建议改用复杂逻辑”的可读提示，并暂停在当前任务上。只有用户明确同意后，Codex 才调用：

```text
butler_set_mode(case_id, mode="complex")
```

切换只修改同一个任务的模式并追加事件，不重新创建任务。

## 5. 对外接口设计

### 5.1 `butler_start_case`

用途：替代 `butler_open_case` 加显式 `butler_next_action`。

输入：

```json
{
  "description": "用户原始请求",
  "mode": "simple",
  "task_type": "",
  "feature_code": "",
  "title": ""
}
```

规则：

- `mode` 缺省为 `simple`；
- 创建任务、写入 `received` 事件并在同一响应中返回 `case_id`；
- 简单模式只返回必要的下一步提示，不要求继续调用 `next_action`；
- 复杂模式返回需要定位、上下文和分派的下一步；
- 不自动推荐专家、不自动分派、不自动创建任务卡；
- 旧 `butler_open_case` 暂时保留为兼容入口，但新流程和工具描述只推荐 `butler_start_case`。

### 5.2 `butler_finalize_case`

用途：替代普通成功路径中的四个收尾接口。

输入：

```json
{
  "case_id": "...",
  "summary": "完成了什么",
  "files": ["path/to/file"],
  "audit": {
    "null": "结果",
    "boundary": "结果",
    "error": "结果",
    "impact": "结果",
    "regression": "结果",
    "pattern": "结果"
  },
  "validation": {
    "passed": true,
    "evidence": "测试命令和用户原始现象验证结果"
  }
}
```

规则：

- 在一个数据库事务中完成必要的改动记录、审查、验证和状态收尾；
- 保留 `change_recorded`、`audit_recorded`、`validation_recorded`、`completed` 等独立事件；
- 任一校验失败时整体回滚，不产生“半完成”状态；
- 简单模式仍要求提供真实验证证据；
- 非代码任务可以使用 `report` 和证据字段，不要求伪造代码审查清单；
- 验证失败时任务回到 `investigating`，不直接标记完成。

### 5.3 `butler_set_mode`

用途：只在用户明确要求或明确同意后切换模式。

规则：

- 只允许 `simple` 和 `complex`；
- 记录 `mode_changed` 事件和用户方向；
- 不复制任务、不覆盖原有上下文、不重置已完成证据；
- 简单任务不能由内部判断自动切换为复杂任务。

### 5.4 保留的详细接口

以下接口继续存在，但只作为复杂模式的专家级能力或兼容接口：

- `record_context`；
- `assign`；
- `record_attempt`；
- `begin_implementation`；
- `create_task_card`、`accept_task_card`、`report_execution_result`；
- `events`、`evidence`、`get_case`。

`request_approval` 和 `resolve_approval` 继续独立保留，供两个模式使用。

## 6. 状态机设计

内部状态继续使用现有状态，新增一个独立的 `mode` 字段：

```text
mode: simple | complex

received
  -> located（复杂模式定位后）
  -> investigating
  -> awaiting_approval（仅高影响操作）
  -> implementing
  -> auditing
  -> verifying
  -> completed
```

简单模式允许 `start_case -> implementing` 的快捷进入，但仍必须经过审批检查和最终验证。复杂模式继续要求 `located -> investigating -> implementing` 的显式顺序。

`blocked` 和 `cancelled` 仍是终止或暂停状态；三次无进展阻断只由复杂模式的 `record_attempt` 触发，简单模式不自动制造调查循环。

## 7. MCP 与数据库实现边界

### 7.1 MCP 层

- 工具目录优先展示 `start_case`、`finalize_case`、审批接口和只读查询；
- 详细阶段接口继续注册，但描述为复杂模式专用；
- 删除结果包装器中的隐式二次 `next_action` 查询，或改为由 `start_case` 在一次事务中直接返回；
- 普通记录工具不配置 `approval_mode = "approve"`；审批只配置在高影响审批接口上。

### 7.2 运行时层

- `mode` 由任务创建时确定，并由 `set_mode` 显式修改；
- `finalize_case` 负责调用现有底层存储函数，保持事件粒度不变；
- 保留现有 `ButlerRuntime` 作为详细能力层，新增聚合方法作为体验层；
- 简化数据库连接初始化：管家表结构在应用启动或显式迁移时初始化，不在每个 MCP 调用中重复执行。

### 7.3 存储层

- `butler_tasks` 增加 `mode TEXT NOT NULL DEFAULT 'simple'`；
- 为已有任务按其当前阶段回填：未显式指定的历史任务视为 `complex`，避免改变旧任务行为；
- 新任务默认 `simple`；
- 所有模式切换、聚合收尾和审批继续写入现有事件表，不新增重复的审计表。

## 8. 兼容与迁移策略

### 阶段一：兼容入口

- 新增 `start_case` 和 `finalize_case`；
- 保留旧接口和旧状态流转；
- 修复 `open_case` 结果中的重复 `next_action` 查询；
- 为旧任务回填 `complex` 模式。

### 阶段二：规则切换

- 更新 `AGENTS.md`：默认简单，只有用户明确说复杂逻辑才调用复杂接口；
- 更新管家工具描述，明确哪些接口属于复杂模式；
- 将 `.codex/config.toml` 中普通管家工具的审批配置移除，只保留高影响审批接口；
- 更新 Claude 适配说明和项目记忆，避免不同入口使用不同规则。

### 阶段三：验证与观测

- 记录每个任务的模式、管家调用次数和总耗时；
- 对比简单模式与旧链路的 MCP 调用数；
- 保留复杂模式的全链路演练；
- 观察一段时间后再决定是否隐藏旧详细接口，而不是立即删除。

## 9. 测试与验收标准

### 简单模式

1. 不指定模式时创建 `simple` 任务。
2. 开始接口一次返回 `case_id` 和必要下一步，不产生重复 `next_action` MCP 调用。
3. 普通成功任务可以只调用 `start_case` 和 `finalize_case` 完成。
4. `finalize_case` 失败时事务回滚，任务不被标记为完成。
5. 验证证据缺失或失败时不能完成任务。
6. 高影响操作仍必须经过审批，即使任务是 `simple`。

### 复杂模式

1. 只有显式 `mode=complex` 或用户明确要求复杂逻辑时才进入复杂链路。
2. 复杂模式继续支持上下文、角色、专家、调查尝试和任务卡交接。
3. `record_attempt` 的三次无进展阻断行为不变。
4. 复杂模式使用 `finalize_case` 后，数据库中仍有独立的改动、审查、验证和完成事件。
5. `set_mode` 只改变同一个任务，不创建重复任务。

### 回归与性能

- 既有 Butler 状态机、审批、任务卡和 MCP 合同测试全部通过；
- 普通成功任务的强制管家调用不超过 2 次，审批除外；
- 普通工具调用不再弹出逐次人工批准；
- 启动时初始化管家 schema，单次 MCP 调用不重复执行完整 schema 初始化；
- 旧 `open_case` 调用继续可用，并提供迁移提示。

## 10. 不在本次范围内

- 自动创建或自动调度其他 Codex 会话；
- 自动判断复杂度并替用户升级模式；
- 删除底层详细接口；
- 修改项目本身的业务功能；
- 重做整个 SQLite 存储架构。

## 11. 结论

管家从“所有任务都走完整流程”调整为“简单模式默认、复杂模式显式选择、风险确认独立存在”。外部体验只保留开始和收尾两个核心接口，内部仍保留完整事件和状态机，因此速度与审计可以同时保留。
