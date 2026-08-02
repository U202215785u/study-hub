# Study-Hub 工作台接口契约

> 功能代号：`SH.WORKBENCH`
> 版本：`workbench.v1`
> 适用范围：`/workbench` 工作台的后端读模型、审批动作契约和前端共享 API 访问约定。
> 本文档只定义接口，不实现页面、业务路由或新的 Butler 持久化状态。

## 1. 设计边界

1. Butler 是案件状态、审批记录、事件和证据的唯一持久化事实来源。工作台返回的 `status`、`status_label`、`next_action` 和统计数字均为读取或派生结果。
2. `status` 使用 Butler 原始枚举，`status_label` 是固定中文展示映射。前端不得把中文标签提交给后端，也不得把工作台字段写回 Butler 状态列。
3. 工作台的版本、测试版本、环境和路线图是稳定的读模型。它们可以由现有发布/测试系统投影得到；没有记录时返回空数组或 `null`，不伪造一条持久化记录。
4. 审批通过只表示用户同意一项受保护操作，不表示已经执行、测试通过或发布成功。发布必须经过独立的发布执行和环境验证。
5. 所有时间使用带时区的 ISO 8601 字符串，例如 `2026-08-02T04:33:04Z`。数据库返回的无时区时间由后端按 UTC 序列化并补上 `Z`。

## 2. HTTP 与 JSON 约定

### 2.1 路径和请求头

- API 根地址由前端共享客户端配置，本文档中的路径均为根地址下的绝对路径，例如 `GET /workbench/cases`。
- 请求和响应编码为 UTF-8，媒体类型为 `application/json`。
- 前端发送 `Accept: application/json`。
- 前端为每次请求发送 `X-Request-ID`；没有现成 ID 时生成 UUID。后端在成功和错误响应中原样返回该 ID。
- `POST` 动作发送 `Idempotency-Key`。同一 key、同一路径和同一用户上下文必须返回同一业务结果，不得重复创建审批或重复处理决策。
- 认证和权限由宿主应用负责；本契约只规定无权访问时使用 `WB_FORBIDDEN`，不定义登录页面或令牌格式。

### 2.2 成功信封

所有成功响应统一为：

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "schema_version": "workbench.v1",
    "request_id": "req_01J9Y5K5M7Q7H2C6D4A8F3P2N1",
    "generated_at": "2026-08-02T04:33:04Z"
  }
}
```

`data` 的类型由端点固定。列表端点的 `data` 是分页对象；单对象端点的 `data` 是对象；动作端点的 `data` 是动作结果。

### 2.3 错误信封

所有可预期错误均返回 JSON：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "WB_INVALID_QUERY",
    "message": "page_size 必须是 1 到 100 之间的整数",
    "details": {
      "field": "page_size",
      "value": "500"
    },
    "retryable": false
  },
  "meta": {
    "schema_version": "workbench.v1",
    "request_id": "req_01J9Y5K5M7Q7H2C6D4A8F3P2N1",
    "generated_at": "2026-08-02T04:33:04Z"
  }
}
```

- `message` 面向用户，可直接展示；`details` 面向前端处理，不能放堆栈、密钥、令牌或内部 SQL。
- `retryable=true` 只表示在相同请求参数下稍后重试有意义；客户端不得自动重试 `POST`，除非复用同一个 `Idempotency-Key`。
- 未知错误统一使用 `WB_INTERNAL`，HTTP 500；详细原因只写服务日志。

### 2.4 分页

列表端点统一接受：

| 参数 | 类型 | 默认值 | 约束 |
|---|---|---:|---|
| `page` | integer | `1` | `>= 1` |
| `page_size` | integer | `20` | `1..100` |
| `sort_by` | string | 端点默认值 | 必须在端点白名单中 |
| `sort_order` | string | `desc` | `asc` 或 `desc` |

成功返回：

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 0,
    "has_next": false,
    "has_previous": false
  },
  "sort": {
    "by": "updated_at",
    "order": "desc",
    "tie_breaker": "id desc"
  }
}
```

后端必须在主排序字段相同时使用固定的 `id` 作为第二排序键，避免刷新页面时项目在分页边界跳动。未知筛选字段、排序字段或排序方向返回 `WB_INVALID_QUERY`，不能静默降级。

## 3. Butler 状态与中文映射

### 3.1 案件状态

以下是当前 `study-hub/backend/butler/models.py` 的完整状态集合。新增 Butler 原始状态时，必须先扩展此契约和映射；在扩展前不得复用已有值表达新含义。

| `status` 原值 | `status_label` | 前端语义分类 |
|---|---|---|
| `received` | 已接收 | 新建 |
| `located` | 已定位 | 上下文已找到 |
| `investigating` | 调查中 | 处理中 |
| `awaiting_approval` | 待审批 | 等待用户决定 |
| `implementing` | 执行中 | 处理中 |
| `auditing` | 待审查 | 等待审查 |
| `verifying` | 验证中 | 等待验证 |
| `completed` | 已完成 | 终态 |
| `blocked` | 已阻塞 | 停止推进 |
| `cancelled` | 已取消 | 终态 |
| `archived` | 已归档 | 终态 |

处理未知原值时保留原字符串，返回 `status_label: "未知状态"`，并在 `meta.warnings` 增加 `UNKNOWN_BUTLER_STATUS`；不得将未知值改成 `blocked` 或其他已知状态。

### 3.2 其他固定映射

| 字段 | 原值枚举 | 中文映射 |
|---|---|---|
| `task_type` | `bug` | 故障排查 |
|  | `change` | 变更 |
|  | `research` | 调研 |
|  | `health_check` | 健康检查 |
|  | `deploy` | 部署 |
|  | `memory_update` | 记忆更新 |
| `risk_level` | `normal` | 普通 |
|  | `protected` | 受保护 |
| `approval.status` | `pending` | 待决定 |
|  | `approved` | 已批准 |
|  | `rejected` | 已拒绝 |

### 3.3 下一步

`next_action.kind` 使用运行时动作名，不使用中文：

`locate_context`、`assign_role`、`record_attempt`、`record_report`、`resolve_approval`、`begin_implementation`、`record_change`、`record_audit`、`record_validation`、`complete_case`、`await_user_direction`、`inspect_case`。

`next_action` 的 `summary` 可以直接展示，`required` 是后续动作所需字段名数组。它是运行时建议，不是新的持久化状态，也不代表动作已执行。

## 4. 共享对象模型

### 4.1 案件摘要 `CaseSummary`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | Butler case ID，保持原值 |
| `task_type` | enum | 是 | 见 3.2 |
| `task_type_label` | string | 是 | 中文展示 |
| `title` | string | 是 | 案件标题 |
| `feature_code` | string | 是 | 例如 `SH.WORKBENCH`，无值时为空字符串 |
| `status` | enum/string | 是 | Butler 原始状态 |
| `status_label` | string | 是 | 中文展示 |
| `risk_level` | `normal|protected` | 是 | Butler 风险级别 |
| `risk_level_label` | string | 是 | 中文展示 |
| `attempt_count` | integer | 是 | 未通过尝试次数 |
| `current_role` | string | 是 | 当前运行时角色，无值时为空字符串 |
| `experts` | string[] | 是 | 当前领域专家，来源为 `current_expert` 的拆分结果 |
| `created_at` | datetime | 是 | 创建时间 |
| `updated_at` | datetime | 是 | 最后更新时间 |

### 4.2 案件详情 `CaseDetail`

`CaseDetail` 包含全部 `CaseSummary` 字段，并增加：

| 字段 | 类型 | 说明 |
|---|---|---|
| `description` | string | 用户原始描述，原样保留 |
| `context` | object | Butler `context_json` 解码结果 |
| `next_action` | object | `kind`、`required`、`summary` |
| `approvals` | Approval[] | 此案件关联的审批，按创建时间升序 |
| `events` | Event[] | 此案件事件，按 `created_at`、`id` 升序 |
| `evidence` | Evidence[] | 此案件证据，按 `created_at`、`id` 升序 |

`context` 允许出现以下稳定字段：`project_index_hits`、`owner_files`、`memory_summary`、`memory_sources`、`memory_freshness`、`location_notes`、`task_card`、`task_card_handoff`、`report`、`change`、`audit`、`validation`。未出现的字段省略，不用空对象覆盖。

### 4.3 事件和证据

```json
{
  "id": 42,
  "case_id": "6d4e4076e1b948fc845400ba28d15761",
  "type": "approval_requested",
  "actor": "butler",
  "summary": "需要用户确认后才能继续",
  "payload": {
    "approval_id": "ap_01J9Y5Q0D4F0P2J7N6W8M3C1R9",
    "risk_kind": "deployment"
  },
  "created_at": "2026-08-02T04:33:04Z"
}
```

```json
{
  "id": 7,
  "case_id": "6d4e4076e1b948fc845400ba28d15761",
  "evidence_type": "document_check",
  "summary": "契约覆盖全部十个工作台端点",
  "location": "study-hub/docs/workbench-api-contract.md",
  "payload": {},
  "created_at": "2026-08-02T04:33:04Z"
}
```

### 4.4 审批 `Approval`

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 审批 ID |
| `case_id` | string | 对外名称；来源于 Butler 的 `task_id` |
| `risk_kind` | string | 例如 `personal_data`、`permission`、`deployment`、`release` |
| `summary` | string | 用户可读的受保护操作摘要 |
| `status` | `pending|approved|rejected` | 持久化决策 |
| `status_label` | string | `待决定`、`已批准`、`已拒绝` |
| `response` | string | 用户决定说明；未决定时为空字符串 |
| `created_at` | datetime | 请求时间 |
| `decided_at` | datetime/null | 决定时间 |
| `operation` | object | 工作台动作上下文；没有时为 `null` |

`operation` 结构为：`kind`、`target_version`、`target_environment`、`release_requested`。它描述请求，不表示已经执行。

## 5. 端点总览

| 方法 | 路径 | 用途 | 是否改变持久化状态 |
|---|---|---|---|
| GET | `/workbench/overview` | 工作台聚合概览 | 否 |
| GET | `/workbench/cases` | 案件列表 | 否 |
| GET | `/workbench/cases/{case_id}` | 案件详情 | 否 |
| GET | `/workbench/approvals` | 审批列表 | 否 |
| POST | `/workbench/approvals/{approval_id}/resolve` | 记录审批决定 | 是，写入 Butler 审批和事件 |
| GET | `/workbench/versions` | 版本读模型列表 | 否 |
| GET | `/workbench/test-versions` | 测试版本读模型列表 | 否 |
| POST | `/workbench/cases/{case_id}/submit-approval` | 提交受保护操作审批 | 是，写入 Butler 审批和案件事件 |
| GET | `/workbench/environment` | 环境状态 | 否 |
| GET | `/workbench/roadmap` | 路线图读模型 | 否 |

## 6. 端点契约

### 6.1 `GET /workbench/overview`

查询参数：无。返回最近聚合快照：

```json
{
  "ok": true,
  "data": {
    "case_counts": {
      "received": 1,
      "located": 0,
      "investigating": 3,
      "awaiting_approval": 1,
      "implementing": 0,
      "auditing": 0,
      "verifying": 1,
      "completed": 8,
      "blocked": 1,
      "cancelled": 0,
      "archived": 2
    },
    "pending_approvals": 1,
    "recent_cases": [],
    "active_versions": [],
    "environments": [],
    "roadmap": {
      "total": 5,
      "in_progress": 1,
      "blocked": 1,
      "next_items": []
    }
  },
  "meta": {
    "schema_version": "workbench.v1",
    "request_id": "req_01J9Y5K5M7Q7H2C6D4A8F3P2N1",
    "generated_at": "2026-08-02T04:33:04Z"
  }
}
```

`case_counts` 必须包含 3.1 中的全部原始状态，即使数量为零。`recent_cases` 使用 `CaseSummary`，固定最多 5 条，按 `updated_at desc, id desc`。

### 6.2 `GET /workbench/cases`

筛选参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `status` | string | 逗号分隔的 Butler 状态，例如 `investigating,blocked` |
| `task_type` | string | 逗号分隔的任务类型 |
| `risk_level` | string | `normal` 或 `protected` |
| `feature_code` | string | 精确匹配功能代号 |
| `q` | string | 在 `id`、`title`、`description` 中做不区分大小写的包含匹配 |
| `include_archived` | boolean | 默认 `false`；为 `true` 时包含 `archived` |
| `page`、`page_size`、`sort_by`、`sort_order` | 见 2.4 | 分页和排序 |

`sort_by` 白名单：`updated_at`、`created_at`、`status`、`attempt_count`、`title`。默认 `updated_at desc`，平级按 `id desc`。

成功 `data` 为分页对象，`items` 是 `CaseSummary[]`。

### 6.3 `GET /workbench/cases/{case_id}`

路径参数 `case_id` 必填。成功 `data` 为 `CaseDetail`。不存在返回 `404 WB_NOT_FOUND`，`details.resource_type` 为 `case`，`details.resource_id` 为请求的 ID。

### 6.4 `GET /workbench/approvals`

筛选参数：`status`（`pending`、`approved`、`rejected`，可逗号分隔）、`case_id`、`risk_kind`、`page`、`page_size`、`sort_by`、`sort_order`。

`sort_by` 白名单：`created_at`、`decided_at`、`status`、`risk_kind`。默认 `created_at asc`，平级按 `id asc`。`items` 为 `Approval[]`。

### 6.5 `POST /workbench/approvals/{approval_id}/resolve`

请求体：

```json
{
  "approved": true,
  "response": "确认先执行测试，不直接发布"
}
```

`approved` 必填布尔值；`response` 必填字符串，允许为空字符串但建议提供决策理由。成功 `data`：

```json
{
  "approval": {
    "id": "ap_01J9Y5Q0D4F0P2J7N6W8M3C1R9",
    "case_id": "6d4e4076e1b948fc845400ba28d15761",
    "risk_kind": "release",
    "summary": "将候选版本 v0.8.0 发布到 staging",
    "status": "approved",
    "status_label": "已批准",
    "response": "确认先执行测试，不直接发布",
    "created_at": "2026-08-02T04:30:00Z",
    "decided_at": "2026-08-02T04:33:04Z",
    "operation": {
      "kind": "release",
      "target_version": "v0.8.0",
      "target_environment": "staging",
      "release_requested": true
    }
  },
  "case": {
    "id": "6d4e4076e1b948fc845400ba28d15761",
    "status": "awaiting_approval",
    "status_label": "待审批",
    "next_action": {
      "kind": "begin_implementation",
      "required": [],
      "summary": "审批已处理，可按批准范围开始执行"
    }
  }
}
```

批准时不得将版本状态改为 `released`；拒绝时返回 `status: rejected`，案件按 Butler 规则进入 `blocked`，并保留审批事件。重复决定返回 `409 WB_APPROVAL_ALREADY_DECIDED`。

### 6.6 `GET /workbench/versions`

筛选参数：`case_id`、`status`、`channel`（`candidate`、`test`、`release`）、`environment`、`page`、`page_size`、`sort_by`、`sort_order`。

`sort_by` 白名单：`created_at`、`updated_at`、`version`、`status`。默认 `created_at desc`，平级按 `id desc`。

`Version` 字段：

| 字段 | 类型 | 枚举或说明 |
|---|---|---|
| `id` | string | 版本记录 ID |
| `case_id` | string/null | 关联案件；无关联时为 `null` |
| `version` | string | 例如 `v0.8.0` |
| `channel` | enum | `candidate`、`test`、`release` |
| `status` | enum | `draft`、`ready_for_test`、`testing`、`passed`、`failed`、`approved`、`released`、`rolled_back` |
| `status_label` | string | 固定中文：草稿、待测试、测试中、测试通过、测试失败、已批准、已发布、已回滚 |
| `commit` | string/null | 提交标识，不含令牌 |
| `changelog` | string | 变更摘要 |
| `target_environment` | string/null | 目标环境 key |
| `approval_id` | string/null | 关联审批 ID |
| `test_version_ids` | string[] | 关联测试版本 ID |
| `created_at`、`updated_at` | datetime | 时间 |
| `approved_at`、`released_at` | datetime/null | 对应动作时间 |

没有版本记录时返回 `items: []`，不能返回不存在的“当前版本”。

### 6.7 `GET /workbench/test-versions`

筛选参数：`case_id`、`version_id`、`status`、`environment`、`suite`、`page`、`page_size`、`sort_by`、`sort_order`。

`sort_by` 白名单：`created_at`、`started_at`、`completed_at`、`status`。默认 `created_at desc`，平级按 `id desc`。

`TestVersion` 字段：

| 字段 | 类型 | 枚举或说明 |
|---|---|---|
| `id` | string | 测试版本 ID |
| `version_id` | string | 关联 Version ID |
| `case_id` | string/null | 关联案件 |
| `version` | string | 被测版本号 |
| `status` | enum | `queued`、`running`、`passed`、`failed`、`expired` |
| `status_label` | string | 排队中、测试中、测试通过、测试失败、已过期 |
| `suite` | string | 测试套件名称 |
| `environment` | string | 环境 key |
| `summary` | string | 测试摘要 |
| `failed_checks` | object[] | 每项含 `name`、`message`、`severity`；无失败时为空数组 |
| `started_at`、`completed_at` | datetime/null | 时间 |
| `artifact_url` | string/null | 可访问的测试产物 URL；不得放签名密钥或访问令牌 |

### 6.8 `POST /workbench/cases/{case_id}/submit-approval`

用于将一项明确的受保护操作登记为待审批。请求体：

```json
{
  "risk_kind": "release",
  "summary": "将 v0.8.0 发布到 staging",
  "operation": {
    "kind": "release",
    "target_version": "v0.8.0",
    "target_environment": "staging",
    "release_requested": true
  }
}
```

字段约束：`risk_kind` 和 `summary` 必填非空字符串；`operation.kind` 必须是 `data`、`permission`、`deployment`、`release` 之一；`release` 必须提供 `target_version` 和 `target_environment`；`release_requested` 必须为布尔值。成功 `data` 为 `{ "approval": Approval, "case": CaseSummary }`，其中 `approval.status` 为 `pending`，`case.status` 为 `awaiting_approval`。

案件已有未决审批时返回 `409 WB_APPROVAL_PENDING`，不得创建第二个相同未决审批。案件不存在返回 `404 WB_NOT_FOUND`。

### 6.9 `GET /workbench/environment`

查询参数：`key`（可选，逗号分隔环境 key）、`page`、`page_size`、`sort_by`、`sort_order`。环境 key 白名单为 `local`、`development`、`staging`、`production`。`sort_by` 白名单为 `key`、`availability`、`last_checked_at`，默认 `key asc`，平级按 `key asc`。

`Environment` 字段：

| 字段 | 类型 | 枚举或说明 |
|---|---|---|
| `key` | enum | `local`、`development`、`staging`、`production` |
| `label` | string | 本地、开发、预发布、生产 |
| `kind` | enum | `local`、`development`、`staging`、`production` |
| `availability` | enum | `healthy`、`degraded`、`unavailable`、`unknown` |
| `availability_label` | string | 健康、降级、不可用、未知 |
| `current_version` | string/null | 当前已确认运行版本 |
| `last_checked_at` | datetime/null | 最近检查时间 |
| `allowed_actions` | string[] | `view`、`test`、`submit_approval`、`release`，由后端权限和环境状态计算 |

环境响应不得包含 API key、数据库密码、Cookie、内部主机凭证或完整环境变量。环境不可达仍返回该环境对象并标为 `unavailable`；只有无法读取整个环境目录时才返回 `WB_ENVIRONMENT_UNAVAILABLE`。

### 6.10 `GET /workbench/roadmap`

筛选参数：`status`（`backlog`、`planned`、`in_progress`、`blocked`、`done`）、`priority`（`P0`、`P1`、`P2`、`P3`）、`owner`、`q`、`page`、`page_size`、`sort_by`、`sort_order`。

`sort_by` 白名单：`priority`、`target_date`、`updated_at`、`status`。默认 `priority asc`，平级按 `target_date asc`、`id asc`。

`RoadmapItem` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 路线图条目 ID |
| `title` | string | 条目名称 |
| `status` | enum | `backlog`、`planned`、`in_progress`、`blocked`、`done` |
| `status_label` | string | 待整理、已计划、进行中、已阻塞、已完成 |
| `priority` | enum | `P0`、`P1`、`P2`、`P3` |
| `owner` | string | 责任角色或团队 |
| `target_date` | date/null | 目标日期；未知时为 `null` |
| `dependencies` | string[] | 依赖条目 ID |
| `linked_case_ids` | string[] | 关联 Butler case ID |
| `updated_at` | datetime | 更新时间 |

路线图不存在的依赖只保留 ID，不在本接口伪造依赖对象。条目删除、编辑和拖拽排序不属于本版工作台接口。

## 7. 错误码与 HTTP 语义

| HTTP | `error.code` | 使用场景 | `retryable` |
|---:|---|---|---|
| 400 | `WB_INVALID_QUERY` | 查询参数、枚举或 JSON 结构无效 | false |
| 401 | `WB_UNAUTHENTICATED` | 缺少有效身份 | false |
| 403 | `WB_FORBIDDEN` | 身份存在但无权访问或执行 | false |
| 404 | `WB_NOT_FOUND` | 案件、审批、版本或环境不存在 | false |
| 409 | `WB_STATE_CONFLICT` | 当前 Butler 状态不允许动作 | false |
| 409 | `WB_APPROVAL_PENDING` | 已有未决审批 | false |
| 409 | `WB_APPROVAL_ALREADY_DECIDED` | 审批已处理，不能重复决定 | false |
| 409 | `WB_RELEASE_NOT_ALLOWED` | 缺少独立发布条件，不能发布 | false |
| 422 | `WB_VALIDATION_FAILED` | 请求字段语义校验失败 | false |
| 429 | `WB_RATE_LIMITED` | 超过访问频率 | true |
| 502 | `WB_UPSTREAM_UNAVAILABLE` | 版本、测试或环境数据源不可用 | true |
| 503 | `WB_SERVICE_UNAVAILABLE` | 工作台依赖暂不可用 | true |
| 500 | `WB_INTERNAL` | 未预期服务错误 | false |

`WB_STATE_CONFLICT.details` 至少包含 `case_id`、`current_status`、`current_status_label` 和 `allowed_next_actions`；不能只返回一段无法处理的字符串。

## 8. 审批、测试和发布边界

以下规则是前后端都必须遵守的流程边界：

1. `submit-approval` 只创建 `pending` 审批，并将案件置于 Butler 的 `awaiting_approval`；它不创建版本、不开始测试、不触发发布。
2. `resolve` 且 `approved=true` 只记录 `approved` 决策和用户响应。批准不等于执行成功，不能把 `Version.status` 直接改成 `released`，也不能把 `TestVersion.status` 改成 `passed`。
3. `approved=false` 记录 `rejected` 决策；案件按 Butler 规则进入 `blocked`，后续继续必须经过明确的恢复动作。前端不能自行把它显示为“已取消”。
4. 测试通过是 `TestVersion.status=passed`，不是审批通过，也不是发布成功。发布前必须同时满足目标版本可发布、必要审批已批准、测试版本通过、目标环境允许 `release`，并由独立发布执行器确认结果。
5. 生产发布结果只能在发布执行器完成后写入 `Version.status=released`，并带有 `released_at` 和目标环境；本契约没有发布动作端点，工作台不得把“批准”冒充“发布”。
6. `environment.allowed_actions` 仅是后端基于权限和环境状态计算的提示；后端对实际动作再次鉴权，前端隐藏按钮不构成安全边界。
7. `risk_kind=personal_data`、`permission`、`deployment`、`release` 均必须走审批；普通读取和文档检查不因展示在工作台而自动升级成受保护操作。

## 9. 前端共享 API 访问约定

前端统一通过 `workbenchApi`（建议实现于 `study-hub/frontend/src/services/apiClient.js` 的共享客户端）访问本契约，不在页面组件内拼接 URL、读取响应字段或重复实现错误解析。

### 9.1 地址解析

按以下优先级选择根地址：

1. 构建配置 `VITE_API_BASE_URL`；
2. `localStorage.getItem("api_base")`；
3. `window.location.origin`。

客户端对根地址去除末尾 `/`，对路径确保恰好一个 `/`。本文档的 `/workbench` 路径不自动追加 `/api`；若部署网关把 `/api` 作为前缀，应将它配置在根地址中。

### 9.2 调用结果

共享客户端提供以下行为：

- `request(path, options)` 只返回成功信封中的 `data`，同时保留 `meta.request_id` 供日志使用。
- HTTP 非 2xx 或 `ok=false` 统一抛出结构化 `WorkbenchApiError`，至少包含 `status`、`code`、`message`、`details`、`retryable` 和 `requestId`。
- 解析不到 JSON 时使用 `WB_UPSTREAM_UNAVAILABLE`，不得把 HTML 错误页直接交给组件。
- `AbortSignal` 取消请求时不显示错误 toast，不写入失败审计。
- GET 请求可由调用方显式重试；POST 只在复用同一 `Idempotency-Key` 时允许重试。
- 响应缺少必需字段或枚举值不认识时记录 `WB_SCHEMA_MISMATCH` 客户端日志，并保留原响应用于诊断；不得把缺失字段默认为“已完成”或“已发布”。

### 9.3 类型和展示

- 所有状态徽章读取 `status_label`，筛选和逻辑判断读取原始 `status`。
- `null` 表示后端明确没有值；空数组表示已查询但没有条目；两者不能互换。
- `pagination.total` 是后端过滤后的总数，前端不得用当前页长度推导总数。
- 时间只在展示层按用户时区格式化；请求参数和缓存 key 使用后端返回的 ISO 字符串。
- 组件只消费共享模型，不能把 `context` 中未列入契约的字段当成必填业务字段。

## 10. 实施验收清单

- [ ] 十个端点的路径、方法、请求参数和响应 `data` 结构与本文档一致。
- [ ] 列表端点接受统一分页参数，并执行端点排序白名单和固定 tie-breaker。
- [ ] 案件返回 Butler 原始状态和完整中文映射，未知状态不会被静默改写。
- [ ] 详情返回事件、证据和审批；`task_id` 对外统一命名为 `case_id`。
- [ ] 申请审批、批准、拒绝和重复决定遵循第 8 节边界。
- [ ] 版本、测试版本、环境和路线图没有记录时返回明确的空值语义，不新建 Butler 状态。
- [ ] 所有错误都符合错误信封和错误码表，不泄露内部堆栈或敏感信息。
- [ ] 前端只通过共享 API 客户端访问 `/workbench`，并按原始枚举做逻辑判断。
