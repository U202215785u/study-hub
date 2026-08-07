# WB-07 Workbench Overview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only `GET /workbench/overview` endpoint that returns one stable server-side summary of workbench cases, approvals, versions, environment health, and roadmap data.

**Architecture:** Keep aggregation in `backend/workbench/overview.py` and reuse the existing case, approval, version, and environment read services. Add one top-level router that mounts the four existing child routers exactly once; make `main.py` include only that top-level router so `/api` middleware behavior remains unchanged.

**Tech Stack:** FastAPI, pytest, SQLite-backed Butler read services, existing `VersionService` and environment projections.

---

### Task 1: Define overview behavior with failing integration tests

**Files:**
- Create: `backend/tests/test_workbench_overview.py`

- [ ] **Step 1: Write the failing tests**

Add tests that exercise the application through `main.app`, create Butler cases and formal/test versions through existing services, and assert that one overview response contains:

```python
assert response.json()["data"]["pending_cases"]
assert response.json()["data"]["verification_cases"]
assert response.json()["data"]["pending_approvals"] == 1
assert response.json()["data"]["current_version"]["version"] == "1.0.0"
assert response.json()["data"]["latest_test_version"]["version"] == "1.1.0-rc.1"
assert response.json()["data"]["health"]["status"] in {"ok", "degraded", "error"}
assert "roadmap" in response.json()["data"]
```

Also cover an empty database and `/api/workbench/overview`; assert `pending_cases == []`, `verification_cases == []`, `pending_approvals == 0`, `current_version is None`, `latest_test_version is None`, and a stable roadmap/environment shape.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run `py -3 -m pytest backend/tests/test_workbench_overview.py -q` from the repository root.

Expected result: the overview request is `404` because the top-level workbench router and endpoint do not exist yet.

### Task 2: Implement the read-model aggregation

**Files:**
- Create: `backend/workbench/overview.py`

- [ ] **Step 1: Add the minimal read-only aggregation**

Implement a `build_overview()` function that:

1. Reads all case summaries with `list_case_summaries(..., include_archived=True)` and derives counts from the existing `STATUS_LABELS` keys, without introducing a second Butler status map.
2. Exposes non-terminal case summaries as `pending_cases`, `verifying` summaries as `verification_cases`, and the five most recently updated summaries as `recent_cases`.
3. Reads pending approvals through `list_approvals(status="pending")` and returns only their count.
4. Uses `VersionService.list_versions(version_type="formal", current_only=True)` and `list_versions(version_type="test", current_only=True)` to select the newest current formal/test record, returning `None` when absent.
5. Reuses `get_environment_info()` and `get_roadmap()` and keeps missing/partial values as `None`, `[]`, or the existing service object rather than inventing records.
6. Includes the contract fields `case_counts`, `pending_approvals`, `recent_cases`, `active_versions`, `environments`, and `roadmap`, plus the direct summary fields required by WB-07.

### Task 3: Add the top-level router and minimal application wiring

**Files:**
- Create: `backend/endpoints/workbench.py`
- Modify: `backend/main.py` at the router import and include-router sections only

- [ ] **Step 1: Mount the overview and child routers once**

Define an unprefixed `APIRouter` in `endpoints/workbench.py`, register `GET /workbench/overview`, and include `workbench_cases.router`, `workbench_approvals.router`, `workbench_versions.router`, and `workbench_environment.router`. Then import it in `main.py` and call `app.include_router(workbench_router)` once.

- [ ] **Step 2: Run focused tests and verify the green result**

Run `py -3 -m pytest backend/tests/test_workbench_overview.py backend/tests/test_workbench_cases.py backend/tests/test_workbench_approvals.py backend/tests/test_workbench_versions.py backend/tests/test_workbench_environment.py -q`.

Expected result: all focused workbench tests pass, including overview aggregation, empty/partial data, `/api` compatibility, and child route mounting.

### Task 4: Run regression verification and record evidence

**Files:**
- No additional source files.

- [ ] **Step 1: Run the complete backend test suite**

Run `py -3 -m pytest backend/tests -q` and confirm there are no regressions.

- [ ] **Step 2: Check the final diff and route table**

Run `git diff --check` and inspect the FastAPI route table to confirm `/workbench/overview`, `/workbench/cases`, `/workbench/approvals`, `/workbench/versions`, `/workbench/environment`, and `/workbench/roadmap` each occur once.
