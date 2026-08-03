# Taskboard Git Delivery Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent a Git-bound issue from entering review with uncommitted task changes or entering done before its reviewed commit reaches the project target branch.

**Architecture:** Add a server-owned `GitGateService` composed of a Git inspector, baseline fingerprint comparator, configured validation runner, and transition evaluator. Persist immutable baselines/evidence/events in SQLite; expose one API contract consumed by the existing status routes, React UI, CLI, workflow automation, and cloud companion.

**Tech Stack:** Node.js ESM, SQLite (`node:sqlite`), Git CLI with `execFile`, React/TypeScript, Node test runner, Cloudflare Worker/D1 for cloud mode.

**Design:** `docs/superpowers/specs/2026-08-04-taskboard-git-delivery-gate-design.md`

---

## File Map

Create focused server modules instead of expanding `server/app.mjs` and `server/database.mjs` with Git policy logic:

```text
dashi-taskboard/server/git-inspector.mjs       Git resolution, porcelain parsing, fingerprints
dashi-taskboard/server/git-gate.mjs            stable checks and transition decisions
dashi-taskboard/server/validation-runner.mjs   configured argv-based validation
dashi-taskboard/server/gate-evidence.mjs       evidence normalization/digests/signatures
dashi-taskboard/web/src/components/DeliveryGate.tsx
dashi-taskboard/web/src/components/delivery-gate.css
```

Modify existing files only for persistence, routing, shared types, and integration:

```text
dashi-taskboard/server/database.mjs
dashi-taskboard/server/app.mjs
dashi-taskboard/server/cloud-proxy.mjs
dashi-taskboard/cli/taskctl.mjs
dashi-taskboard/web/src/types.ts
dashi-taskboard/web/src/api.ts
dashi-taskboard/web/src/components/TaskDetail.tsx
dashi-taskboard/skills/manage-taskboard/SKILL.md
dashi-taskboard/skills/manage-taskboard/references/cli.md
```

## Task 1: Persistence and shared gate vocabulary

**Files:**
- Modify: `dashi-taskboard/server/database.mjs`
- Modify: `dashi-taskboard/web/src/types.ts`
- Test: `dashi-taskboard/test/server.test.mjs`

- [ ] **Step 1: Write failing migration and round-trip tests**

Add a server test that creates a project policy, baseline, evidence, and event, restarts the database, and asserts all records survive. Assert legacy tasks still load with no gate state.

```js
test("delivery gate records survive restart without changing legacy tasks", () => {
  const first = openTemporaryDatabase();
  const task = first.createTask(taskInput({ developmentContext: { type: "branch", branch: "feature/gate" } }));
  first.saveProjectDeliveryPolicy("local", {
    targetBranch: "master",
    validationNotRequired: false,
    validationProfileIds: ["frontend"],
  }, userActor);
  const baseline = first.createTaskGitBaseline(task.id, baselineFixture());
  first.createTaskDeliveryEvidence(task.id, evidenceFixture({ baselineId: baseline.id }));
  first.appendTaskGateEvent(task.id, gateEventFixture("baseline.captured"));
  first.close();

  const second = reopenTemporaryDatabase();
  assert.equal(second.getTask(task.id).deliveryGate, undefined);
  assert.equal(second.getActiveTaskGitBaseline(task.id).headSha, baseline.headSha);
  assert.equal(second.listTaskGateEvents(task.id).length, 1);
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `node --test test/server.test.mjs --test-name-pattern="delivery gate records"`

Expected: FAIL because the policy/baseline/evidence/event database methods do not exist.

- [ ] **Step 3: Add tables and database methods**

Create `project_delivery_policies`, `task_git_baselines`, `task_delivery_evidence`, and `task_gate_events` in `#migrate()`. Add CRUD methods named exactly as used by the test. Keep events append-only; expose no update/delete method.

```sql
CREATE TABLE IF NOT EXISTS task_git_baselines (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  repository_id TEXT NOT NULL,
  context_snapshot TEXT NOT NULL,
  head_sha TEXT NOT NULL,
  dirty_fingerprints TEXT NOT NULL,
  device_id TEXT,
  created_at TEXT NOT NULL,
  invalidated_at TEXT,
  invalidation_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_gate_baseline
ON task_git_baselines(task_id) WHERE invalidated_at IS NULL;
```

- [ ] **Step 4: Add TypeScript contracts**

Define `GateCheckCode`, `GateCheck`, `DeliveryGateSnapshot`, `TaskGitBaseline`, `TaskDeliveryEvidence`, `ProjectDeliveryPolicy`, and `ValidationProfile`. Use the stable codes from the design document verbatim.

- [ ] **Step 5: Run tests and commit**

Run: `node --test test/server.test.mjs --test-name-pattern="delivery gate records"`

Expected: PASS.

```bash
git add dashi-taskboard/server/database.mjs dashi-taskboard/web/src/types.ts dashi-taskboard/test/server.test.mjs
git commit -m "feat(taskboard): persist delivery gate evidence"
```

## Task 2: Git inspector and baseline fingerprints

**Files:**
- Create: `dashi-taskboard/server/git-inspector.mjs`
- Create: `dashi-taskboard/test/git-inspector.test.mjs`

- [ ] **Step 1: Write table-driven porcelain and fingerprint tests**

Use real temporary repositories. Cover staged, unstaged, untracked, rename, delete, symlink where supported, and a file already dirty at baseline that changes again.

```js
test("detects a second edit to a file already dirty at baseline", async () => {
  const repo = await createRepo({ "note.txt": "committed\n" });
  await writeFile(join(repo.path, "note.txt"), "dirty before task\n");
  const baseline = await inspectGitContext({ type: "worktree", path: repo.path, branch: "master" });
  await writeFile(join(repo.path, "note.txt"), "changed by task\n");
  const current = await inspectGitContext({ type: "worktree", path: repo.path, branch: "master" });
  assert.notEqual(current.dirtyEntries[0].worktreeSha256, baseline.dirtyEntries[0].worktreeSha256);
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test test/git-inspector.test.mjs`

Expected: FAIL because `inspectGitContext` is missing.

- [ ] **Step 3: Implement bounded inspection**

Export:

```js
export async function inspectGitContext(context, options = {}) { /* returns GitSnapshot */ }
export function parsePorcelainV2Z(buffer) { /* returns normalized entries */ }
export async function fingerprintDirtyEntries(root, entries, limits) { /* hashes without following symlinks */ }
export function repositoryId(root, commonDir) { /* sha256 of canonical identities */ }
```

Use `execFile("git", ["-C", root, ...])`, `git status --porcelain=v2 -z --untracked-files=all`, streaming SHA-256, a 4-second Git timeout, and configurable untracked file/byte limits. Return stable failures rather than raw process errors.

- [ ] **Step 4: Verify GREEN and commit**

Run: `node --test test/git-inspector.test.mjs`

Expected: all inspector cases PASS and no temporary repository remains open.

```bash
git add dashi-taskboard/server/git-inspector.mjs dashi-taskboard/test/git-inspector.test.mjs
git commit -m "feat(taskboard): inspect Git delivery state"
```

## Task 3: Baseline comparator and review/done decisions

**Files:**
- Create: `dashi-taskboard/server/git-gate.mjs`
- Create: `dashi-taskboard/test/git-gate.test.mjs`

- [ ] **Step 1: Write failing evaluator tests**

Cover every blocking code and the four baseline-dirt outcomes. Keep the evaluator pure by passing snapshots and command-result facts.

```js
test("unchanged baseline dirt warns while changed baseline dirt blocks", () => {
  const unchanged = evaluateReviewGate({ baseline, current: baselineLikeCurrent(), commits: [commit], validations: [pass] });
  assert.equal(unchanged.blocking.length, 0);
  assert.deepEqual(unchanged.warnings.map((item) => item.code), ["BASELINE_DIRTY_UNCHANGED"]);

  const changed = evaluateReviewGate({ baseline, current: changedDirtyCurrent(), commits: [commit], validations: [pass] });
  assert.deepEqual(changed.blocking.map((item) => item.code), ["TASK_DELTA_UNCOMMITTED"]);
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test test/git-gate.test.mjs`

Expected: FAIL because evaluator exports are missing.

- [ ] **Step 3: Implement pure evaluators**

Export:

```js
export function compareDirtyState(baselineEntries, currentEntries, committedBlobs) { /* categorized delta */ }
export function evaluateReviewGate(input) { /* {blocking,warnings,reviewCommitSha} */ }
export function evaluateDoneGate(input) { /* {blocking,warnings} */ }
export function gateDigest(value) { /* canonical JSON sha256 */ }
```

Never infer success from a missing fact. Missing or stale facts map to a blocking code.

- [ ] **Step 4: Verify GREEN and commit**

Run: `node --test test/git-gate.test.mjs`

Expected: PASS for all stable code mappings.

```bash
git add dashi-taskboard/server/git-gate.mjs dashi-taskboard/test/git-gate.test.mjs
git commit -m "feat(taskboard): evaluate Git delivery gates"
```

## Task 4: User-configured validation runner

**Files:**
- Create: `dashi-taskboard/server/validation-runner.mjs`
- Create: `dashi-taskboard/test/validation-runner.test.mjs`
- Modify: `dashi-taskboard/server/database.mjs`

- [ ] **Step 1: Write failing process-safety tests**

Assert argv execution succeeds, a shell metacharacter remains a literal argument, `cwd` escape is rejected, output is bounded/redacted, and timeout returns `VALIDATION_TIMEOUT`.

```js
test("validation never evaluates shell metacharacters", async () => {
  const result = await runValidationProfile(profile({
    program: process.execPath,
    args: ["-e", "console.log(process.argv[1])", "$(should-not-run)"],
  }), context);
  assert.equal(result.steps[0].status, "passed");
  assert.match(result.steps[0].output, /\$\(should-not-run\)/);
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test test/validation-runner.test.mjs`

Expected: FAIL because the runner is missing.

- [ ] **Step 3: Implement structured profiles**

Export `validateProfile`, `runValidationProfile`, and `redactOutput`. Use `spawn`/`execFile` with `shell: false`, repository-contained cwd resolution, timeout, output byte caps, and process-tree termination.

- [ ] **Step 4: Verify GREEN and commit**

Run: `node --test test/validation-runner.test.mjs`

Expected: PASS with no child processes left running.

```bash
git add dashi-taskboard/server/validation-runner.mjs dashi-taskboard/server/database.mjs dashi-taskboard/test/validation-runner.test.mjs
git commit -m "feat(taskboard): run configured delivery validation"
```

## Task 5: Enforce the gate in server status transitions

**Files:**
- Modify: `dashi-taskboard/server/app.mjs`
- Modify: `dashi-taskboard/server/database.mjs`
- Test: `dashi-taskboard/test/server.test.mjs`

- [ ] **Step 1: Write failing API transition tests**

Use real temporary repositories and the existing HTTP harness. Test atomic baseline capture on claim, review block/pass, done block/pass, version conflict, context reset invalidation, and fail-closed Git errors.

```js
test("bound issue cannot enter review with an uncommitted task delta", async () => {
  const repo = await createRepo({ "card.vue": "old title\n" });
  const task = await createBoundIssue(repo);
  await move(task, "in_progress");
  await writeFile(join(repo.path, "card.vue"), "new title\n");
  const result = await move(task, "in_review");
  assert.equal(result.response.status, 409);
  assert.equal(result.body.error.code, "DELIVERY_GATE_BLOCKED");
  assert.deepEqual(result.body.error.details.checks.map((item) => item.code), ["TASK_DELTA_UNCOMMITTED"]);
});
```

- [ ] **Step 2: Verify RED**

Run: `node --test test/server.test.mjs --test-name-pattern="bound issue|delivery gate|reviewed commit"`

Expected: FAIL because status routes do not call the gate.

- [ ] **Step 3: Integrate one service into PATCH and move routes**

Construct `GitGateService` in server startup and call:

```js
await gitGate.beforeTransition({ task, requestedStatus, actor, taskVersion, threadId });
```

Capture a baseline for a bound `in_progress` claim. For `in_review`, inspect, validate, evaluate, and persist evidence. For `done`, check target-branch reachability. Re-read the task version immediately before the database transaction commits.

- [ ] **Step 4: Add gate endpoints and user authorization**

Implement the routes in the design. Reject Agent acknowledgement/override with `403 ACTOR_NOT_ALLOWED`. Require selected check codes, reason length, task version, and evidence version.

- [ ] **Step 5: Verify GREEN and commit**

Run: `node --test test/server.test.mjs`

Expected: all existing and gate server tests PASS.

```bash
git add dashi-taskboard/server/app.mjs dashi-taskboard/server/database.mjs dashi-taskboard/test/server.test.mjs
git commit -m "feat(taskboard): enforce delivery status gates"
```

## Task 6: CLI contract and Codex skill

**Files:**
- Modify: `dashi-taskboard/cli/taskctl.mjs`
- Modify: `dashi-taskboard/skills/manage-taskboard/SKILL.md`
- Modify: `dashi-taskboard/skills/manage-taskboard/references/cli.md`
- Modify: `dashi-taskboard/test/cli.test.mjs`
- Modify: `dashi-taskboard/test/manage-taskboard-skill.test.mjs`

- [ ] **Step 1: Write failing CLI and skill tests**

Assert `gate status`, `gate check`, and `gate baseline` request the exact endpoints, JSON errors retain check details, no force/override option exists, and skill text requires commit evidence while prohibiting Agent override.

- [ ] **Step 2: Verify RED**

Run: `node --test test/cli.test.mjs test/manage-taskboard-skill.test.mjs`

Expected: FAIL on missing gate commands and requirements.

- [ ] **Step 3: Implement CLI dispatch and documentation**

Add command handlers:

```js
async function gateStatus(api, issueId) { return api.request("GET", `${taskPath(issueId)}/delivery-gate`); }
async function gateCheck(api, issueId, options) {
  return api.request("POST", `${taskPath(issueId)}/delivery-gate/check`, { target: requiredOption(options, "target") });
}
async function gateBaseline(api, issueId, options) {
  return api.request("POST", `${taskPath(issueId)}/delivery-gate/baseline`, {
    version: await resolveVersion(api, issueId, options["if-version"]),
  });
}
```

Do not add `--force` or an override command.

- [ ] **Step 4: Verify GREEN and commit**

Run: `node --test test/cli.test.mjs test/manage-taskboard-skill.test.mjs`

Expected: PASS.

```bash
git add dashi-taskboard/cli/taskctl.mjs dashi-taskboard/skills/manage-taskboard dashi-taskboard/test/cli.test.mjs dashi-taskboard/test/manage-taskboard-skill.test.mjs
git commit -m "feat(taskboard): expose delivery gate diagnostics"
```

## Task 7: Delivery gate UI and blocked status interactions

**Files:**
- Create: `dashi-taskboard/web/src/components/DeliveryGate.tsx`
- Create: `dashi-taskboard/web/src/components/delivery-gate.css`
- Modify: `dashi-taskboard/web/src/types.ts`
- Modify: `dashi-taskboard/web/src/api.ts`
- Modify: `dashi-taskboard/web/src/components/TaskDetail.tsx`
- Modify: `dashi-taskboard/web/src/App.tsx`
- Modify: `dashi-taskboard/test/board-interactions.test.mjs`
- Create: `dashi-taskboard/test/delivery-gate-ui.test.mjs`

- [ ] **Step 1: Write failing component and interaction tests**

Assert compact states render, blockers receive focus, failed drag restores the original column, user-only override visibility is enforced, and stale evidence is refreshed before transition.

- [ ] **Step 2: Verify RED**

Run: `node --test test/delivery-gate-ui.test.mjs test/board-interactions.test.mjs`

Expected: FAIL because the component and blocked-move handling are absent.

- [ ] **Step 3: Add typed API functions**

```ts
export async function getDeliveryGate(taskId: string): Promise<DeliveryGateSnapshot>;
export async function checkDeliveryGate(taskId: string, target: "in_review" | "done"): Promise<DeliveryGateSnapshot>;
export async function acknowledgeDeliveryGate(taskId: string, input: GateAcknowledgementInput): Promise<DeliveryGateSnapshot>;
export async function overrideDeliveryGate(taskId: string, input: GateOverrideInput): Promise<DeliveryGateSnapshot>;
```

- [ ] **Step 4: Build the detail section and blocked dialog**

Use the existing detail property language and icon system. Keep the section unframed. Render a stable-height checklist with success/warning/blocking tones, short SHAs, timestamps, remediation, and a refresh icon button. Put acknowledgement/override controls behind `actor.type === "user"`.

- [ ] **Step 5: Verify GREEN, typecheck, and commit**

Run: `node --test test/delivery-gate-ui.test.mjs test/board-interactions.test.mjs`

Run: `npm run typecheck`

Expected: all tests PASS and TypeScript reports no errors.

```bash
git add dashi-taskboard/web/src dashi-taskboard/test/delivery-gate-ui.test.mjs dashi-taskboard/test/board-interactions.test.mjs
git commit -m "feat(taskboard): show Git delivery gate status"
```

## Task 8: Cloud companion signed evidence

**Files:**
- Create: `dashi-taskboard/server/gate-evidence.mjs`
- Modify: `dashi-taskboard/server/cloud-proxy.mjs`
- Modify: `dashi-taskboard/server/cloud-config.mjs`
- Modify: `dashi-taskboard/cloud/src/index.mjs`
- Create: `dashi-taskboard/cloud/migrations/0002_delivery_gate.sql`
- Modify: `dashi-taskboard/test/cloud-companion.test.mjs`
- Modify: `dashi-taskboard/test/cloud-shared-worker.test.mjs`

- [ ] **Step 1: Write failing privacy/replay tests**

Test nonce binding, signature verification, replay rejection, expiry, task/evidence version mismatch, offline companion, and absence of absolute paths/raw content. Assert the D1 migration creates policy, baseline, evidence, event, device-key, and consumed-nonce storage.

- [ ] **Step 2: Verify RED**

Run: `node --test test/cloud-companion.test.mjs test/cloud-shared-worker.test.mjs`

Expected: FAIL because gate challenge/evidence routes are absent.

- [ ] **Step 3: Implement canonical evidence and device signatures**

Export canonical JSON encoding, SHA-256 digesting, nonce generation/consumption, and Ed25519 sign/verify helpers. Bind a signature to task id, requested target status, task version, evidence version, nonce, issued/expiry times, and evidence digest.

- [ ] **Step 4: Enforce cloud fail-closed behavior**

The companion performs local inspection and validation. The Worker verifies signed normalized evidence and calls the same logical evaluator. No companion or invalid/expired evidence returns the appropriate blocking code; never fall back to comments.

- [ ] **Step 5: Verify GREEN and commit**

Run: `node --test test/cloud-companion.test.mjs test/cloud-shared-worker.test.mjs`

Expected: PASS, including replay and privacy assertions.

```bash
git add dashi-taskboard/server dashi-taskboard/cloud dashi-taskboard/test/cloud-companion.test.mjs dashi-taskboard/test/cloud-shared-worker.test.mjs
git commit -m "feat(taskboard): verify cloud Git gate evidence"
```

## Task 9: End-to-end acceptance and guarded rollout

**Files:**
- Create: `dashi-taskboard/test/git-delivery-gate.e2e.test.mjs`
- Modify: `dashi-taskboard/README.md`
- Modify: `dashi-taskboard/docs/cloud-collaboration.md`
- Modify: `dashi-taskboard/package.json`

- [ ] **Step 1: Encode the twelve specification acceptance cases**

Build temporary repositories and drive the public HTTP/CLI interfaces. Include the original failure shape: change a visible component title without committing, claim tests passed, and verify review remains blocked.

- [ ] **Step 2: Run the end-to-end test**

Run: `node --test test/git-delivery-gate.e2e.test.mjs`

Expected: PASS for all twelve acceptance cases.

- [ ] **Step 3: Document enablement and rollback**

Document project target branch, validation profiles, local/cloud evidence, user acknowledgement/override, diagnostic commands, and the feature flag. State that disabling enforcement preserves all baseline/evidence/event rows.

- [ ] **Step 4: Run the complete quality gate**

Run: `npm run check`

Expected: typecheck, production build, and all Node tests PASS.

- [ ] **Step 5: Enable only for the local Study-Hub project and smoke test**

Configure `targetBranch=master`, the Study-Hub validation profiles, and local enforcement. Create a disposable issue/worktree and demonstrate blocked uncommitted review, successful committed review, blocked unmerged done, and successful merged done. Do not enable cloud enforcement until Task 8 evidence tests pass.

- [ ] **Step 6: Commit documentation and acceptance coverage**

```bash
git add dashi-taskboard/test/git-delivery-gate.e2e.test.mjs dashi-taskboard/README.md dashi-taskboard/docs/cloud-collaboration.md dashi-taskboard/package.json
git commit -m "test(taskboard): verify Git delivery gate workflow"
```

## Final Verification

- [ ] Run `npm run check` from `dashi-taskboard` and confirm exit code 0.
- [ ] Run `git diff --check` and confirm no whitespace errors.
- [ ] Confirm every stable check code in the design has a unit or integration assertion.
- [ ] Confirm no API route can update a gated status without calling `GitGateService`.
- [ ] Confirm Agent identity receives `403` for acknowledgement and override.
- [ ] Confirm cloud evidence contains neither an absolute path nor raw file content.
- [ ] Confirm the feature flag can disable enforcement without deleting audit data.
- [ ] Leave the implementation issue in `in_review`; only the user may move it to `done`.
