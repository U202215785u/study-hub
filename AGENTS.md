# Study-Hub 协作入口

本工作区的项目请求先经过管家，以便定位、留痕和交接；用户不需要选择页面、功能区域、前后端、角色或工具名。

本文件是 Codex 在本工作区的**唯一行为规则来源**。`.claude/skills/butler/SKILL.md` 只保留给 Claude 的能力说明与开发参考，不重复或覆盖这里的流程。

## 普通任务：尽力登记，不阻塞工作

当用户要求排查、修复、修改、新增、删除、检查、测试、发布、部署，或研究当前项目的外部方案时：

1. 默认调用 `mcp__study_hub__butler_start_case`，不传模式即走 `simple`；只有用户明确说“走复杂逻辑”或显式传入 `mode=complex` 才走 `complex`。任务类型可留空，或直接使用用户的自然语言描述。
2. `simple` 成功登记后直接读取项目记忆、相关文件并完成修改和验证，最后调用 `mcp__study_hub__butler_finalize_case`；不要为普通任务额外调用 `butler_next_action`、`record_context` 或角色分派。开始接口的结果已包含必要的下一步信息。
3. `complex` 任务按需调用 `mcp__study_hub__butler_next_action`、`mcp__study_hub__butler_record_context`、`mcp__study_hub__butler_recommend_experts`、`mcp__study_hub__butler_recommend_chain` 和 `mcp__study_hub__butler_assign`；建议不替代 Codex 判断，也不自动锁定角色或启动 Agent。
4. 需要交给另一位 Agent 时，调用 `mcp__study_hub__butler_create_task_card`，把返回的五行任务卡原样交接。执行 Agent 用 `mcp__study_hub__butler_accept_task_card` 认领，并用 `mcp__study_hub__butler_report_execution_result` 回传结果。
5. 复杂任务的调查和修复尽量调用 `mcp__study_hub__butler_record_attempt`；详细收尾依次调用 `mcp__study_hub__butler_record_change`、`mcp__study_hub__butler_record_audit`、`mcp__study_hub__butler_record_validation`，再调用 `mcp__study_hub__butler_complete_case`。简单任务使用 `mcp__study_hub__butler_finalize_case` 聚合这些收尾记录。

模式只由用户决定，系统不得因为范围扩大、失败或发现跨模块影响而自动升级；需要升级时先说明并等待用户明确选择，再调用 `mcp__study_hub__butler_set_mode`。

简单模式验证失败后继续停在 `implementing`，由 Codex 修复后再次调用 `butler_finalize_case`；复杂模式验证失败回到 `investigating`。两种模式均可调用 `butler_block_case`、`butler_cancel_case`、`butler_resume_case`。

`mcp__study_hub__butler_open_case`、`mcp__study_hub__butler_next_action` 及其他详细阶段接口继续作为兼容入口；新普通任务优先使用 `mcp__study_hub__butler_start_case` 和 `mcp__study_hub__butler_finalize_case`。

若 MCP 不可用、参数错误、数据库短暂锁定或工具返回 `policy: fail_open`，这是**尽力登记**失败：Codex 可以继续只读定位、常规排查和低风险改动；恢复后补录任务、证据和验证。这是 fail-open（失败开放）策略。不要反复登记同一任务，更不要把工具失败误报为用户问题已解决。

## 高影响操作：必须确认

删除、个人数据、账号权限、发布、部署或其他高影响操作必须走 `mcp__study_hub__butler_request_approval`，并等待用户明确同意。出现 `policy: fail_closed` 或等待确认时，不得继续执行受保护操作；可以继续解释影响、准备方案和只读检查。

## 项目定位与协作边界

先用自然语言理解问题，再从 `project-memory/功能代号地图.md`、相关项目记录和代码中定位。任务卡保存生成时的事实快照、记忆来源和新鲜度；旧卡片不会被后续记忆静默改写。

任务卡用于交接、认领和结果回收，不会自动创建其他 Codex 会话或代替主 Agent 的审查、验证与合并判断。

## 何时不进入管家

纯概念解释、普通闲聊、与本工作区无关的问题，以及尚未要求调查或改动的想法讨论，不创建管家任务。

## Git 工作树（worktree）安全约定

本仓库使用大量 git worktree（当前 20+ 个活动工作树、30+ 个分支）。worktree 有一个易踩的坑：**未提交/未跟踪的改动是隔离的，只存在于它所在的工作树目录里，不随分支、不随合并走；工作树被 `git worktree remove` 清理时，未提交内容直接永久丢失**。用户已多次因此丢失内容。

铁律：

1. **任何"切换分支、`git merge`、`git checkout`/恢复文件、清理/删除 worktree"之前**，先跑 `bash scripts/check-uncommitted.sh`；有未提交内容时先 `git commit` 或 `git stash`（并记录 stash 位置），再继续。
2. **绝不 `git worktree remove`（含 `--force`）一个仍有未提交内容的 worktree**；先在该 worktree 里提交、或把改动复制出来备份。
3. 不要假设"改动在分支上"——未提交改动不跟着分支走，跨 worktree 看不到。
4. 工具（Claude/superpowers 等）自动创建或清理 worktree 前，先把当前未提交改动提交；新会话开始工作前先跑一次 `scripts/check-uncommitted.sh` 盘点现状。
5. 当前有 18 个分支尚未并入 master（`codex/butler-runtime*`、`codex/content-parser-workbench`、`codex/study-ui-*`、`codex/recovery-*`、`codex/douyin-reliable-import` 等）——这些分支的提交只在它们自己的 worktree/分支里，master 上没有，清理前必须确认不丢。

## 完成标准

不能把“已经登记任务”当成“已经解决问题”。完成前必须有真实检查结果和对用户原始现象的验证。连续三次没有进展（包括 `failed`、`error`、`timeout` 等）时，停止继续尝试，向用户说明阻塞原因并等待新方向。
