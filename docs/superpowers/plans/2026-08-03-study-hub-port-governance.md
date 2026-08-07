# Study Hub Port Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce one documented port allocation so the stable app, development environment, and frontend tests can run without accidental port drift.

**Architecture:** A small frontend port-policy module provides constants for Vite and Node-based browser tests. Vite uses `strictPort` to fail instead of silently selecting a nearby port. Backend launch scripts retain their fixed ports and identify a non-Study-Hub listener as a conflict. User-facing documentation exposes only the stable `8741` address as the normal entry point.

**Tech Stack:** Vite 5, Node.js ESM, Playwright, PowerShell, Markdown.

---

### Task 1: Add a shared frontend port policy

**Files:**
- Create: `study-hub/frontend/src/config/ports.js`
- Create: `study-hub/frontend/tests/port-policy.mjs`
- Modify: `study-hub/frontend/vite.config.js`

- [ ] **Step 1: Write the failing policy test**

```js
import assert from 'node:assert/strict'
import { FRONTEND_DEV_PORT, TEST_PORTS, testOrigin } from '../src/config/ports.js'

assert.equal(FRONTEND_DEV_PORT, 5173)
assert.deepEqual(TEST_PORTS, Object.freeze({ workbench: 5180, dashboard: 5181 }))
assert.equal(testOrigin(TEST_PORTS.dashboard), 'http://127.0.0.1:5181')
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `node study-hub/frontend/tests/port-policy.mjs`

Expected: failure because `src/config/ports.js` does not exist.

- [ ] **Step 3: Add the minimal port-policy module and wire Vite to it**

```js
export const FRONTEND_DEV_PORT = 5173
export const TEST_PORTS = Object.freeze({ workbench: 5180, dashboard: 5181 })
export const testOrigin = (port) => `http://127.0.0.1:${port}`
```

Update Vite's server block to use `port: FRONTEND_DEV_PORT` and `strictPort: true`.

- [ ] **Step 4: Run the policy test and build**

Run: `node study-hub/frontend/tests/port-policy.mjs; npm run build`

Expected: policy check and Vite production build pass.

### Task 2: Move browser checks into the test-only range

**Files:**
- Modify: `study-hub/frontend/tests/workbench-api-routing.mjs`
- Modify: `study-hub/frontend/tests/home-visual-overlay.mjs`
- Modify: `study-hub/frontend/tests/home-responsive.mjs`
- Modify: `study-hub/frontend/tests/home-layout-persistence.mjs`
- Test: `study-hub/frontend/tests/port-policy.mjs`

- [ ] **Step 1: Extend the failing policy test with source assertions**

```js
const testSources = await Promise.all([
  'workbench-api-routing.mjs',
  'home-visual-overlay.mjs',
  'home-responsive.mjs',
  'home-layout-persistence.mjs',
].map((file) => readFile(new URL(`./${file}`, import.meta.url), 'utf8')))

for (const source of testSources) {
  assert.doesNotMatch(source, /127\\.0\\.0\\.1:517[48]/)
  assert.match(source, /TEST_PORTS|testOrigin/)
}
```

- [ ] **Step 2: Run the policy test and verify it fails**

Run: `node study-hub/frontend/tests/port-policy.mjs`

Expected: failure because the browser checks still hard-code `5174` or `5178`.

- [ ] **Step 3: Replace hard-coded origins**

Use `WORKBENCH_FRONTEND_ORIGIN || testOrigin(TEST_PORTS.workbench)` for the workbench check. Use `STUDY_UI_ORIGIN || testOrigin(TEST_PORTS.dashboard)` for the three dashboard checks.

- [ ] **Step 4: Run the policy test**

Run: `node study-hub/frontend/tests/port-policy.mjs`

Expected: pass and no source retains the retired default ports.

### Task 3: Make the development backend reject foreign port ownership

**Files:**
- Modify: `study-hub/backend/start-development.ps1`
- Create: `study-hub/backend/tests/test_start_development.ps1`

- [ ] **Step 1: Write a static PowerShell contract test**

```powershell
$script = Get-Content (Join-Path $PSScriptRoot '..\start-development.ps1') -Raw
if ($script -notmatch 'Test-StudyHubBackendProcess') { throw 'development launcher must validate the existing listener' }
if ($script -notmatch 'Port 8742 occupied by another process') { throw 'development launcher must explain foreign port conflicts' }
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File study-hub/backend/tests/test_start_development.ps1`

Expected: failure because the launcher currently treats every listener on `8742` as the development backend.

- [ ] **Step 3: Validate the existing listener before reuse**

Load the process owning `8742` with `Get-CimInstance`, call the existing `Test-StudyHubBackendProcess` helper, reuse only a matching `main:app` process rooted in `$ProjectDir`, otherwise write `[ERROR] Port 8742 occupied by another process` and exit `1`.

- [ ] **Step 4: Run the PowerShell contract test**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File study-hub/backend/tests/test_start_development.ps1`

Expected: exit code `0`.

### Task 4: Publish the operational port reference

**Files:**
- Create: `study-hub/docs/端口规范.md`
- Modify: `study-hub/README.md`
- Modify: `study-hub/启动.bat`

- [ ] **Step 1: Add a documentation check**

```js
assert.match(portGuide, /http:\/\/localhost:8741/)
assert.match(portGuide, /8742.*开发/)
assert.match(portGuide, /5173.*前端开发/)
assert.match(portGuide, /5180-5189/)
```

- [ ] **Step 2: Run the check and verify it fails**

Run: `node study-hub/frontend/tests/port-policy.mjs`

Expected: failure because the user-facing port guide does not exist.

- [ ] **Step 3: Add the guide and align startup wording**

Create a concise Chinese port table. In `启动.bat`, label `8741` as the stable Study Hub entry point only. Add a README link to the guide beside its current local access section.

- [ ] **Step 4: Run documentation and build validation**

Run: `node study-hub/frontend/tests/port-policy.mjs; npm run build`

Expected: the port-policy suite and production build pass.

### Task 5: Verify running environments without changing them

**Files:**
- Test: `study-hub/backend/tests/test_start_development.ps1`
- Test: `study-hub/frontend/tests/port-policy.mjs`

- [ ] **Step 1: Check listeners and process commands**

Run: `Get-NetTCPConnection -State Listen -LocalPort 8741,8742 | Select-Object LocalAddress,LocalPort,OwningProcess`

Expected: both ports are present and can be mapped to their separate Study Hub backend processes.

- [ ] **Step 2: Run all focused checks**

Run: `node study-hub/frontend/tests/port-policy.mjs; powershell -NoProfile -ExecutionPolicy Bypass -File study-hub/backend/tests/test_start_development.ps1; npm run build`

Expected: all commands exit successfully, with no process stopped or restarted.

- [ ] **Step 3: Commit the implementation**

```bash
git add study-hub/frontend/src/config/ports.js study-hub/frontend/vite.config.js study-hub/frontend/tests study-hub/backend/start-development.ps1 study-hub/backend/tests/test_start_development.ps1 study-hub/docs/端口规范.md study-hub/README.md study-hub/启动.bat docs/superpowers/plans/2026-08-03-study-hub-port-governance.md
git commit -m "feat: enforce Study Hub port governance"
```
