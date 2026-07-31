# Study-Hub Butler Entry Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make project operations in this Codex workspace enter the existing Butler runtime automatically while leaving ordinary explanations and unrelated chat uninterrupted.

**Architecture:** Add a workspace-level `AGENTS.md` contract that defines the Butler-first trigger boundary and required lifecycle calls. Keep state, approvals, retries, evidence, and completion gates in the existing `study-hub/backend/butler/` runtime. Add contract tests that protect the entry rules and the existing runtime gates.

**Tech Stack:** Codex `AGENTS.md` guidance, local stdio MCP, Python 3.12, pytest, existing SQLite Butler runtime.

---

### Task 1: Add the workspace Butler entry contract

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: Write the durable entry rules**

Create `AGENTS.md` with these requirements:

```markdown
# Study-Hub 协作入口

本工作区涉及项目操作时，管家是唯一入口。

当用户要求排查、修复、修改、新增、删除、检查、测试、发布、部署，或研究当前项目的外部方案时：

1. 先调用 `mcp__study_hub__butler_open_case` 登记任务。
2. 立即调用 `mcp__study_hub__butler_next_action`，只按返回的下一步继续。
3. 定位后调用 `mcp__study_hub__butler_record_context`；分派后调用 `mcp__study_hub__butler_assign`。
4. 每次调查或修复调用 `mcp__study_hub__butler_record_attempt`。
5. 受保护操作先调用 `mcp__study_hub__butler_request_approval`，等待用户明确同意。
6. 改动完成后依次调用 `mcp__study_hub__butler_record_change`、`mcp__study_hub__butler_record_audit`、`mcp__study_hub__butler_record_validation`，再调用 `mcp__study_hub__butler_complete_case`。

纯概念解释、普通闲聊、与本工作区无关的问题，以及尚未要求调查或改动的想法讨论，不创建管家任务。

用户不需要选择页面、功能区域、前端/后端、角色或工具名。先用自然语言理解问题，再从 `project-memory/功能代号地图.md` 和相关项目记录中定位。内部角色和外部专家由管家自动选择。

不能把“已经登记任务”当成“已经解决问题”。完成前必须有真实检查结果和对用户原始现象的验证。
```

- [ ] **Step 2: Check every required lifecycle call**

Run:

```powershell
rg -n "butler_open_case|butler_next_action|butler_record_context|butler_assign|butler_record_attempt|butler_request_approval|butler_record_change|butler_record_audit|butler_record_validation|butler_complete_case" AGENTS.md
```

Expected: every name appears at least once.

- [ ] **Step 3: Commit**

```powershell
git add -- AGENTS.md
git commit -m "feat: enforce Butler-first project entry"
```

### Task 2: Add regression tests for the entry contract

**Files:**
- Create: `study-hub/backend/tests/test_butler_entry_contract.py`

- [ ] **Step 1: Write the contract tests**

```python
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[3]


def test_workspace_contract_requires_butler_for_project_operations():
    contract = (WORKSPACE / "AGENTS.md").read_text(encoding="utf-8")
    required = (
        "mcp__study_hub__butler_open_case",
        "mcp__study_hub__butler_next_action",
        "mcp__study_hub__butler_record_context",
        "mcp__study_hub__butler_assign",
        "mcp__study_hub__butler_record_attempt",
        "mcp__study_hub__butler_request_approval",
        "mcp__study_hub__butler_record_change",
        "mcp__study_hub__butler_record_audit",
        "mcp__study_hub__butler_record_validation",
        "mcp__study_hub__butler_complete_case",
    )
    assert all(name in contract for name in required)
    assert "纯概念解释" in contract
    assert "用户不需要选择页面" in contract


def test_butler_runtime_still_exposes_entry_and_completion_gates():
    from butler.mcp_tools import butler_tool_names

    names = set(butler_tool_names())
    assert {"butler_open_case", "butler_next_action", "butler_request_approval", "butler_record_validation", "butler_complete_case"} <= names
```

- [ ] **Step 2: Run the new test**

```powershell
python -m pytest backend/tests/test_butler_entry_contract.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit**

```powershell
git add -- study-hub/backend/tests/test_butler_entry_contract.py
git commit -m "test: protect Butler entry contract"
```

### Task 3: Verify the real Codex-to-MCP path

**Files:**
- Read-only: `.codex/config.toml`, `study-hub/backend/mcp_server.py`
- Test: `study-hub/backend/tests/`

- [ ] **Step 1: Run all Butler tests**

```powershell
python -m pytest study-hub/backend/tests -q
```

Expected: all tests pass; existing Pydantic deprecation warnings may remain.

- [ ] **Step 2: Verify project server registration**

```powershell
codex mcp get study-hub
```

Expected: Python command, absolute server path, and Study-Hub working directory are shown.

- [ ] **Step 3: Verify stdio initialization and entry response**

Send an MCP `initialize` request to `backend/mcp_server.py`, then call `mcp__study_hub__butler_open_case` with a disposable bug description and call `mcp__study_hub__butler_next_action` with its returned id. Expected: stdio reports `study-hub`; the next action is `locate_context`; no source file is changed.

### Task 4: Final audit and handoff

- [ ] **Step 1: Check repository state**

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only explicitly preserved local runtime files may remain untracked.

- [ ] **Step 2: Report the technical boundary honestly**

State that entry is enforced by Codex project guidance plus runtime gates, not by an operating-system-level interceptor. A future hard-interceptor phase requires a separate design.
