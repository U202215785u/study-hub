# Study Hub Dual Environment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the main Study Hub as the stable use version on port 8741 and provide an isolated development worktree on port 8742.

**Architecture:** The main project directory remains the stable entry point. A dedicated Git worktree and branch outside the repository at `F:/360MoveData/Users/Administrator/Desktop/代码项目/study-hub-dev` provide the development copy. Each copy starts from its own backend directory, so code, PID files, logs, and backend data remain isolated.

**Tech Stack:** Git worktrees, Windows batch files, PowerShell, Uvicorn.

---

### Task 1: Inspect the current repository state

**Files:** None

- [x] Confirm the main worktree path, branch, existing worktrees, and uncommitted changes.
- [x] Do not overwrite or reset unrelated user changes.

### Task 2: Create the development worktree

**Files:** Create the Git worktree at `F:/360MoveData/Users/Administrator/Desktop/代码项目/study-hub-dev` on branch `codex/study-hub-dev` from the current `master` HEAD.

- [x] Verify the new worktree reports branch `codex/study-hub-dev` and has its own `study-hub/backend/data` directory.

### Task 3: Add the development launch entry

**Files:**
- Create: `study-hub/backend/start-development.ps1` in the development worktree
- Create: `study-hub/打开 Study Hub 开发版.bat` in the development worktree

- [x] Configure the development launcher to use port `8742`, the development worktree's own `backend/data`, and URL `http://127.0.0.1:8742/`.
- [x] Keep the stable launcher's existing port `8741` unchanged.

### Task 4: Verify both environments

**Files:** None

- [x] Parse both PowerShell launchers without errors.
- [x] Confirm the stable and development launchers resolve to different directories, ports, PID files, log files, and data directories.
- [x] Start the development backend and confirm port `8742` listens without disturbing port `8741`.
- [x] Report all existing unrelated changes separately.
