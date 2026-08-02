# Butler Nonblocking Collaboration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the Study-Hub Butler assist and audit Codex work without blocking ordinary investigation, while completing recommendation and handoff-result capabilities.

**Architecture:** Keep the existing SQLite task and event stream as the audit record. Normalize natural-language task input at the runtime boundary, expose recommendations as read-only runtime tools, and store task-card snapshots plus handoff state in the existing per-case context. MCP errors carry an explicit fail-open or fail-closed policy; the written entry rule follows the same policy.

**Tech Stack:** Python 3, SQLite, MCP Python SDK, pytest.

---

### Task 1: Define nonblocking input and progress semantics

**Files:**
- Modify: `study-hub/backend/butler/models.py`
- Modify: `study-hub/backend/butler/runtime.py`
- Test: `study-hub/backend/tests/test_butler_runtime.py`

- [x] **Step 1: Write failing tests** for `investigate` and Chinese task labels resolving to canonical types, context being appendable while investigating, and `error`/`timeout` exhausting the same three-no-progress limit as `failed`.
- [x] **Step 2: Run** `pytest tests/test_butler_runtime.py -q` and confirm the new tests fail because normalization, context updates, and result classification do not exist.
- [x] **Step 3: Implement** `normalize_task_type`, append-only context updates, and a named no-progress result set in the runtime boundary.
- [x] **Step 4: Run** `pytest tests/test_butler_runtime.py -q` and confirm all runtime tests pass.

### Task 2: Make recommendations real runtime capabilities

**Files:**
- Modify: `study-hub/backend/butler/catalog.py`
- Modify: `study-hub/backend/butler/runtime.py`
- Modify: `study-hub/backend/butler/mcp_tools.py`
- Test: `study-hub/backend/tests/test_butler_runtime.py`
- Test: `study-hub/backend/tests/test_butler_mcp.py`

- [x] **Step 1: Write failing tests** for a case-specific expert and task-chain recommendation, including ASR selecting the automation expert.
- [x] **Step 2: Run** the focused runtime and MCP tests and confirm the recommendation APIs are absent.
- [x] **Step 3: Implement** read-only `butler_recommend_experts` and `butler_recommend_chain` tools backed by `catalog.py`; do not auto-assign roles or create agents.
- [x] **Step 4: Run** the focused tests and confirm they pass.

### Task 3: Add auditable task-card collaboration

**Files:**
- Modify: `study-hub/backend/butler/runtime.py`
- Modify: `study-hub/backend/butler/mcp_tools.py`
- Test: `study-hub/backend/tests/test_butler_task_cards.py`
- Test: `study-hub/backend/tests/test_butler_mcp.py`

- [x] **Step 1: Write failing tests** for immutable card snapshot metadata, one-agent acceptance, and a matching agent reporting a compact execution result.
- [x] **Step 2: Run** `pytest tests/test_butler_task_cards.py tests/test_butler_mcp.py -q` and confirm failure.
- [x] **Step 3: Implement** snapshot metadata (`captured_at`, memory sources, freshness), `butler_accept_task_card`, and `butler_report_execution_result` in existing case context/events.
- [x] **Step 4: Run** the focused tests and confirm they pass.

### Task 4: Publish recovery policy and one authoritative behavior rule

**Files:**
- Modify: `study-hub/backend/butler/mcp_tools.py`
- Modify: `AGENTS.md`
- Modify: `.claude/skills/butler/SKILL.md`
- Test: `study-hub/backend/tests/test_butler_mcp.py`
- Test: `study-hub/backend/tests/test_butler_entry_contract.py`

- [x] **Step 1: Write failing tests** for MCP ordinary-tool errors returning explicit `fail_open` recovery guidance and protected approval errors returning `fail_closed`.
- [x] **Step 2: Run** the focused tests and confirm the legacy generic error response fails the new expectation.
- [x] **Step 3: Implement** policy-bearing MCP errors, nonblocking `AGENTS.md` rules, and a Claude skill that defers behavior rules to `AGENTS.md`.
- [x] **Step 4: Run** the focused tests and confirm they pass.

### Task 5: Verify the complete workflow

**Files:**
- Test: `study-hub/backend/tests/test_butler_*.py`

- [x] **Step 1: Run** `pytest tests/test_butler_*.py -q` from `study-hub/backend`.
- [x] **Step 2: Exercise** the actual MCP adapter with an `investigate` ASR report, recommendation lookup, task-card acceptance, result reporting, and a malformed ordinary registration request.
- [x] **Step 3: Record** changed files, audit checklist, and validation evidence in the active Butler case; complete it only after the test and adapter evidence pass.
