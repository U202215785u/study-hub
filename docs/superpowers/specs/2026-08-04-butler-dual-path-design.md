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

复杂模式只有两种明确触发方式：用户说“走复杂逻辑”，或调用方显式传入 `mode=complex`。例如“走复杂逻辑”“请按复杂逻辑处理”会触发复杂模式；“这任务比较麻烦”“涉及多模块联动”以及“请完整留痕”本身都不会触发模式切换。管家可以提示模式选择，但不能未经用户同意自动切换。

### 2.2 安全边界

简单模式不等于跳过安全确认。以下操作仍必须调用 `request_approval`，并等待 `resolve_approval`：

- 删除文件、数据或项目资源；
- 发布、部署、上线或不可逆迁移；
- 个人数据处理；
- 账号、权限、密钥或访问范围变更；
- 其他由项目规则标记为高影响的操作。

删除边界按资源性质判断：受版本管理的源代码、配置、项目数据、数据库记录和用户数据属于受保护删除；临时目录、缓存、构建产物和测试输出在确认不含用户数据且不影响项目恢复时属于普通清理。

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

此外，`mcp_tools.py` 的结果包装器会对带任务 id 的返回值再次计算 `next_action`；`AGENTS.md` 又要求调用方显式读取下一步。因此，实际冗余是“包装器已返回 `next_action`”与“流程再次强制调用 `next_action`”同时存在，而不是包装器单独错误。

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
- 区分两类失败：输入缺失、状态不允许或内部不变量失败时，整个事务回滚并保持调用前状态；调用方收到错误后不得把任务当成已完成。
- `validation.passed=false` 是一次有效的失败验证，不是事务异常。此时提交已提供的改动、审查和验证证据，并显式拒绝收尾：简单模式回到 `implementing`，复杂模式回到 `investigating`，达到现有无进展上限时进入 `blocked`。
- 简单模式仍要求提供真实验证证据；
- 非代码任务可以使用 `report` 和证据字段，不要求伪造代码审查清单；
- 简单模式验证失败后的下一步是继续修复后再次调用 `finalize_case`，或在用户明确要求后调用 `set_mode`；两个模式都可以调用 `block_case`、`cancel_case` 和 `resume_case`。

`audit` 中的六个键必须与现有 `record_audit` 合同一致：`null`、`boundary`、`error`、`impact`、`regression`、`pattern`，来源是 `runtime.py:524`。其中 `null` 表示空值或缺失输入检查，不是占位符。

### 5.3 `butler_set_mode`

用途：只在用户明确要求或明确同意后切换模式。

规则：

- 只允许 `simple` 和 `complex`；
- 记录 `mode_changed` 事件和用户方向；
- 不复制任务、不覆盖原有上下文、不重置已完成证据；
- 只允许在非终止状态切换：`completed`、`cancelled`、`archived` 不可切换，`blocked` 可以先切换模式再恢复；
- 简单任务不能由内部判断自动切换为复杂任务。

### 5.4 保留的详细接口

以下接口继续存在，但只作为复杂模式的专家级能力或兼容接口：

- `record_context`；
- `assign`；
- `record_attempt`；
- `begin_implementation`；
- `create_task_card`、`accept_task_card`、`report_execution_result`；
- `block_case`、`cancel_case`、`resume_case`；
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

简单模式的失败路径固定为：

```text
finalize_case(validation.passed=false)
  -> 提交失败验证证据
  -> implementing
  -> Codex 继续修复并再次 finalize_case
```

用户也可以在任一模式调用 `block_case` 或 `cancel_case`；被阻塞的任务通过 `resume_case` 恢复。简单模式恢复到 `implementing`，复杂模式恢复到 `investigating`。`cancelled` 和 `completed` 是终止状态，不能恢复。

## 7. MCP 与数据库实现边界

### 7.1 MCP 层

- 工具目录展示的完整工具名统一使用 `butler_` 前缀：`butler_start_case`、`butler_finalize_case`、`butler_set_mode`。文档中的 `start_case`、`finalize_case` 只是短名称；
- 工具目录优先展示 `butler_start_case`、`butler_finalize_case`、审批接口和只读查询；
- 详细阶段接口继续注册，但描述为复杂模式专用；
- 简单模式的流程删除显式 `next_action` 调用；`butler_start_case` 在一次响应中返回下一步。结果包装器可以继续为兼容调用返回 `next_action`，但不能再被流程规则重复调用；
- 普通记录工具不配置 `approval_mode = "approve"`；审批只配置在高影响审批接口上。

工作台接口已经通过 `backend/workbench/cases.py` 返回 `next_action`，前端 `CasesPanel.vue` 按通用字段展示。迁移后后端必须返回模式感知的下一步：简单模式的 `implementing` 显示“修复并完成收尾”，复杂模式继续显示详细阶段；同时增加 `mode` 字段和接口合同测试，避免前端把 `finalize_case` 当成未知状态。

### 7.2 运行时层

- `mode` 由任务创建时确定，并由 `set_mode` 显式修改；
- `finalize_case` 负责调用现有底层存储函数，保持事件粒度不变；
- 保留现有 `ButlerRuntime` 作为详细能力层，新增聚合方法作为体验层；
- 简化数据库连接初始化：管家表结构在应用启动或显式迁移时初始化，不在每个 MCP 调用中重复执行。

### 7.3 存储层

- `butler_tasks` 增加 `mode TEXT NOT NULL DEFAULT 'simple'`；
- 历史任务统一回填 `complex` 模式，避免改变已有完整链路任务的行为；
- 新任务默认 `simple`；
- 所有模式切换、聚合收尾和审批继续写入现有事件表，不新增重复的审计表。

## 8. 兼容与迁移策略

### 阶段一：兼容入口

- 新增 `start_case` 和 `finalize_case`；
- 保留旧接口和旧状态流转；
- 新流程取消 `AGENTS.md` 中紧随开始接口的显式 `next_action` 调用；包装器为旧调用返回的 `next_action` 保持兼容，不再把它描述为重复查询缺陷；
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
4. 输入或状态校验失败时保持调用前状态；`validation.passed=false` 时提交失败证据并回到 `implementing`。
5. 验证证据缺失时不能完成任务；验证失败不能直接完成任务。
6. `block_case`、`cancel_case`、`resume_case` 在简单模式可用且状态目标明确。
7. 高影响操作仍必须经过审批，即使任务是 `simple`。

### 复杂模式

1. 只有显式 `mode=complex` 或用户明确要求复杂逻辑时才进入复杂链路。
2. 复杂模式继续支持上下文、角色、专家、调查尝试和任务卡交接。
3. `record_attempt` 的三次无进展阻断行为不变。
4. 复杂模式使用 `finalize_case` 后，数据库中仍有独立的改动、审查、验证和完成事件。
5. `set_mode` 只改变同一个任务，不创建重复任务；终止状态不可切换。

### 回归与性能

- 既有 Butler 状态机、审批、任务卡和 MCP 合同测试全部通过；
- 普通成功任务的强制管家调用不超过 2 次，审批除外；
- 普通工具调用不再弹出逐次人工批准；
- 启动时初始化管家 schema，单次 MCP 调用不重复执行完整 schema 初始化；
- 旧 `open_case` 调用继续可用，并提供迁移提示。
- `workbench/cases.py` 与 `CasesPanel.vue` 能正确展示简单模式 `implementing`、失败验证后的下一步和 `mode`。

## 10. 不在本次范围内

- 自动创建或自动调度其他 Codex 会话；
- 自动判断复杂度并替用户升级模式；
- 删除底层详细接口；
- 修改项目本身的业务功能；
- 重做整个 SQLite 存储架构。

## 11. 结论

管家从“所有任务都走完整流程”调整为“简单模式默认、复杂模式显式选择、风险确认独立存在”。外部体验只保留开始和收尾两个核心接口，内部仍保留完整事件和状态机，因此速度与审计可以同时保留。
