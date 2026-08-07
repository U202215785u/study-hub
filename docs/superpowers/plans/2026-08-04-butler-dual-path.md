# Butler 双通道执行计划

> 目标：默认 Web Coding 任务走 `simple`，仅用户明确指定 `complex` 时走完整协作链；保留高影响审批和复杂任务审计能力。

## 1. 后端数据与状态机

- [x] 为任务增加持久化 `mode`，新任务默认 `simple`，历史任务统一回填 `complex`。
- [x] 为 `runtime` 增加 `start_case`、`finalize_case`、`set_mode` 聚合能力。
- [x] 明确验证失败路径：`simple` 回到 `implementing`，`complex` 回到 `investigating`；事务/输入错误才回滚。
- [x] 让 `resume` 按任务模式恢复到对应工作状态，并禁止终止任务切换模式。

## 2. MCP 与流程入口

- [x] 新增 `butler_start_case`、`butler_finalize_case`、`butler_set_mode` 工具。
- [x] 保留旧工具兼容，并修正结果包装和普通流程中的重复 `next_action` 负担。
- [x] 保留 `block_case`、`cancel_case`、`resume_case` 两模式共用，并更新工作区流程说明。

## 3. 工作台与性能

- [x] 让工作台返回并展示 `mode`，按模式提供正确的 `next_action`。
- [x] 避免每次 MCP 调用重复初始化 Butler schema，同时保留显式迁移能力。

## 4. 验证与收尾

- [x] 先运行后端 Butler 相关测试确认基线和新增测试的 RED/GREEN。
- [x] 运行后端全量测试、前端单元测试和构建；前端有 2 个工作区既有缺失组件套件未通过，其余 137 个测试通过，生产构建通过。
- [x] 检查 diff，仅将本任务相关文件纳入 Butler 变更记录，并补录审查、验证证据；共享工作树不做清理或提交。

## 实施约束

- 共享工作树中已有用户未提交改动，不执行清理、恢复、stash 或 worktree 删除。
- 不自动把 `simple` 升级为 `complex`；只有用户明确授权才调用 `set_mode`。
- 高影响操作继续经过独立 approval 闸门。
