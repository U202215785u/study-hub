# Taskboard Git Delivery Gate Design

Date: 2026-08-04
Status: Approved design; implementation not started
Scope: `dashi-taskboard` server, local/cloud companion, web UI, `taskctl`, and `manage-taskboard` skill

## 1. Problem

The taskboard can currently bind an issue to a branch or worktree, but status transitions only validate the issue version and status enum. A task can therefore say that a fix passed tests and move to review or done while:

- the fix exists only as an uncommitted working-tree change;
- the claimed commit does not contain the fix;
- the commit exists on an isolated branch but never reaches `main` or `master`;
- a worktree contains unrelated pre-existing changes that are accidentally included;
- the bound worktree has disappeared or the task is checked from a different repository;
- a comment reports test success without durable, reproducible evidence.

The `STUDYHUB-5` article-parser title regression is the reference failure: the board recorded a successful fix, but Git still contained the old committed implementation and the working copy later lost a required component import.

## 2. Goals

1. A code task bound to a Git development context cannot enter `in_review` until its task changes are committed and configured validation passes.
2. It cannot enter `done` until the reviewed commit is reachable from the project's target branch.
3. Dirty files that existed before the task do not block it when they remain byte-for-byte unchanged.
4. New changes to those files, or newly dirty files, do block review.
5. The same gate applies to the web UI, CLI, Codex skill, and workflow automation.
6. Git inspection failure is fail-closed, with a user-only, permanently audited override.
7. Local paths and file contents are not uploaded to cloud storage.

## 3. Non-goals

- Replacing human review of whether a commit actually satisfies the requirement.
- Requiring a remote push before `done`.
- Running arbitrary commands supplied by an Agent or issue comment.
- Continuously watching every repository in the first version.
- Retrofactively invalidating existing `done` issues.
- Solving deployment or release approval; this gate proves source delivery only.

## 4. Chosen Architecture

Add a server-side `GitGateService`. Every status mutation path calls the same service before writing the new issue status. The React UI, `taskctl`, workflow nodes, and future integrations do not implement independent policy logic.

The service has four bounded components:

| Component | Responsibility |
|---|---|
| `GitInspector` | Resolve the bound repository/context and collect Git facts using argument arrays, timeouts, and output limits. |
| `BaselineStore` | Persist the immutable snapshot captured when work starts. |
| `DeliveryGateEvaluator` | Compare the current snapshot to the baseline and return stable check codes. |
| `ValidationRunner` | Run only user-configured validation profiles in the bound context. |

Local mode runs `GitInspector` in the taskboard service. Cloud mode requires the local companion to run the inspection; the cloud service never fabricates Git results when the companion is offline.

## 5. Delivery Policy

The gate is mandatory when an issue has a bound `developmentContext` as it enters `in_progress`. Unbound issues keep the existing workflow and show `No Git delivery policy` in the UI.

Once a baseline exists:

- an Agent cannot clear or replace the development context to bypass the gate;
- a user may reset the context, but this invalidates all current evidence and captures a new baseline;
- moving back to `in_progress` preserves the baseline unless the user explicitly resets it;
- moving from `in_review` back to active work marks review evidence stale but keeps it in history.

Projects gain two settings:

```text
targetBranch: explicit branch, otherwise auto-detect main then master
validationProfileIds: ordered list of user-managed validation profiles
```

Remote push state is reported as a warning only. The local target branch is authoritative for `done` in version one.

## 6. Baseline Model

Capture a baseline synchronously during the transition to `in_progress`:

```text
taskId
repositoryId              stable hash of canonical repository root and Git common dir
contextType               branch | worktree
contextBranch
baselineHeadSha
capturedAt
capturedByDeviceId
dirtyEntries[]
```

Each dirty entry stores metadata and hashes, never file contents:

```text
relativePathHash          HMAC on cloud; clear relative path locally
statusCode                Git porcelain v2 status
fileType and mode
indexObjectId             when tracked/staged
worktreeSha256            for regular files
size
submoduleHead and dirty flag
```

Ignored files are excluded. Untracked regular files are hashed. Untracked directories are expanded with configurable file-count and byte limits; exceeding a limit blocks baseline capture instead of silently omitting data. Symlinks hash their link target. File contents and absolute paths never enter cloud evidence.

Path-only snapshots are insufficient: a file already dirty at task start can be edited again without changing its porcelain status. Content fingerprints are therefore required.

## 7. Review Evaluation

Before `in_progress -> in_review`, the server refreshes Git facts and evaluates all checks atomically.

Required pass conditions:

1. The repository identity and bound context still match the baseline.
2. The worktree exists, is not detached, and reports the expected branch.
3. `HEAD` differs from `baselineHeadSha` and is a descendant of it.
4. At least one commit exists in `baselineHeadSha..HEAD`.
5. No current dirty entry is new or has a fingerprint different from its baseline fingerprint.
6. Every configured validation command exits successfully in the bound context.
7. Evidence was generated during this transition attempt and persisted before the status update.

Baseline dirt is handled explicitly:

- unchanged baseline dirty entry: warning, not blocking;
- baseline dirty entry changed and remains dirty: block as `TASK_DELTA_UNCOMMITTED`;
- baseline dirty entry becomes clean and the current committed blob equals the baseline committed blob: treated as restored;
- baseline dirty entry becomes clean and the committed blob changed: block as `BASELINE_DIRTY_ABSORBED` until a user acknowledges that the pre-existing change was intentionally included.

The reviewed commit is the current `HEAD`, stored as `reviewCommitSha`. A rebase that makes the new head no longer descend from the baseline invalidates the baseline; a user must reset it rather than allowing the service to guess ancestry.

## 8. Done Evaluation

Before `in_review -> done`, the server performs a fresh, lightweight evaluation:

1. Existing review evidence is present and not stale.
2. `reviewCommitSha` still exists.
3. The configured target branch exists locally.
4. `git merge-base --is-ancestor reviewCommitSha targetBranch` succeeds.
5. No blocking override or context reset occurred after review evidence was created.

The worktree does not need to remain clean after review if later dirt is unrelated to the immutable reviewed commit. New work on the same issue must first return it to `in_progress`, which invalidates the prior review evidence.

## 9. Stable Check Codes

The API returns machine-readable checks. Initial blocking codes are:

```text
GIT_CONTEXT_REQUIRED
GIT_CONTEXT_MISMATCH
GIT_CONTEXT_MISSING
GIT_DETACHED_HEAD
BASELINE_CAPTURE_FAILED
BASELINE_LIMIT_EXCEEDED
BASELINE_INVALIDATED
NO_TASK_COMMIT
NON_DESCENDANT_HEAD
TASK_DELTA_UNCOMMITTED
BASELINE_DIRTY_ABSORBED
VALIDATION_FAILED
VALIDATION_TIMEOUT
REVIEW_EVIDENCE_STALE
REVIEW_COMMIT_MISSING
TARGET_BRANCH_MISSING
REVIEW_COMMIT_NOT_IN_TARGET
COMPANION_OFFLINE
EVIDENCE_SIGNATURE_INVALID
EVIDENCE_EXPIRED
```

Warnings use separate codes such as `BASELINE_DIRTY_UNCHANGED`, `NO_UPSTREAM`, and `LOCAL_COMMITS_NOT_PUSHED`.

## 10. Validation Profiles

Validation commands are project settings managed by a user. Store each command as structured data rather than a shell string:

```json
{
  "name": "Frontend checks",
  "steps": [
    { "program": "npm", "args": ["run", "test:unit"], "cwd": "study-hub/frontend", "timeoutMs": 120000 },
    { "program": "npm", "args": ["run", "build"], "cwd": "study-hub/frontend", "timeoutMs": 120000 }
  ]
}
```

Rules:

- use process spawning without a shell;
- resolve the executable through a platform-specific allowlisted resolver;
- constrain `cwd` to the repository root;
- cap output and runtime;
- redact configured secret patterns before persistence;
- store exit code, duration, bounded output digest, and timestamps;
- prohibit issue text, comments, Agents, and workflow payloads from defining commands.

Projects with no configured profile may enter review only if a user explicitly sets `validationNotRequired`. This decision is a project setting, not an Agent-provided assertion.

## 11. Data Model

Add the following tables or equivalent normalized storage:

### `project_delivery_policies`

```text
project_id primary key
target_branch nullable
validation_not_required boolean
validation_profile_ids json
updated_by_actor
updated_at
```

### `task_git_baselines`

```text
id primary key
task_id
repository_id
context_snapshot json
head_sha
dirty_fingerprints json
device_id
created_at
invalidated_at nullable
invalidation_reason nullable
```

### `task_delivery_evidence`

```text
id primary key
task_id
baseline_id
head_sha
target_branch
checks json
validation_runs json
device_id
signature nullable
created_at
stale_at nullable
```

### `task_gate_events`

Append-only audit records for baseline capture, failed gate attempts, evidence creation, context reset, acknowledgement, override, and successful transition. Events contain actor identity and thread attribution where available.

No absolute worktree path or clear relative file path is synchronized to cloud storage.

## 12. API Contract

Add these endpoints:

```text
GET  /api/tasks/:id/delivery-gate
POST /api/tasks/:id/delivery-gate/baseline
POST /api/tasks/:id/delivery-gate/check
POST /api/tasks/:id/delivery-gate/acknowledgements
POST /api/tasks/:id/delivery-gate/override
GET  /api/projects/:id/delivery-policy
PUT  /api/projects/:id/delivery-policy
```

Normal issue move/update endpoints remain the only way to change status. They call the evaluator internally and return HTTP `409` with code `DELIVERY_GATE_BLOCKED` when checks fail:

```json
{
  "error": {
    "code": "DELIVERY_GATE_BLOCKED",
    "message": "Git delivery checks did not pass",
    "details": {
      "requestedStatus": "in_review",
      "checks": [],
      "evidenceVersion": 4
    }
  }
}
```

The status update and evidence write occur in one database transaction after external checks complete. Optimistic issue version checking still runs immediately before the transaction commits; a concurrent update returns the existing `VERSION_CONFLICT` response and leaves the evidence as an unsuccessful audit attempt.

## 13. User-only Override

Git inspection is fail-closed. Override is available only to a user actor, never to `codex-agent` or an automation actor.

An override requires:

- selecting each blocking check being accepted;
- a non-empty reason of at least 20 characters;
- confirmation that the exception will be permanent in task history;
- the latest task version and gate evidence version.

The override is scoped to one requested transition and one evidence snapshot. Any Git/context change invalidates it. The audit event records actor, reason, failed checks, evidence digest, device, timestamp, and target status. There is intentionally no generic `--force` option in `taskctl`.

`BASELINE_DIRTY_ABSORBED` uses a narrower user acknowledgement but the same immutable audit mechanism. It does not waive other checks.

## 14. Web UI

Add an unframed `Delivery gate` section to issue details when a development context is bound. It shows one compact state:

```text
Not started -> Baseline captured -> Changes uncommitted -> Ready for review
-> Reviewed at <short SHA> -> Included in <target branch>
```

The section displays:

- bound branch/worktree and baseline time;
- current and reviewed short SHA;
- changed-since-baseline summary;
- validation steps and latest results;
- unchanged pre-existing dirt as a warning group;
- blocking checks with direct remediation text;
- evidence freshness and refresh action.

Dragging or selecting `in_review` runs the gate. On failure, the card returns to its original column and a focused dialog lists blockers; no optimistic success state is shown. Moving to `done` uses the same interaction and explains which target branch lacks the reviewed commit.

Only signed-in/local user identity sees override controls. Agent-attributed sessions see the blockers but no override action.

## 15. CLI and Skill

Add:

```text
taskctl gate status ISSUE_ID --json
taskctl gate check ISSUE_ID --target in_review|done --json
taskctl gate baseline ISSUE_ID --if-version N --json
```

`taskctl issue move` automatically invokes the server gate; callers do not need to run `gate check` first. Gate commands are diagnostic and baseline-management tools, not an alternate status path.

Update `manage-taskboard` so an Agent must:

1. bind a development context before claiming a code issue;
2. treat successful baseline capture as part of the claim;
3. commit task changes before requesting review;
4. report structured gate failures instead of claiming completion;
5. never request or perform a user override;
6. confirm the reviewed SHA is in the target branch before asking to mark the issue done.

## 16. Cloud Companion

The cloud worker cannot inspect a local repository. Cloud gate evidence therefore uses a challenge-response flow:

1. Cloud issues a short-lived nonce for the task, transition, task version, and evidence version.
2. The registered local companion inspects Git and runs validation.
3. It submits normalized evidence without absolute paths or file contents.
4. It signs the nonce and evidence digest with a device key registered to the user.
5. Cloud verifies signature, actor permission, nonce, freshness, and evidence completeness before applying the same evaluator result.

This proves which registered device supplied the evidence; it does not make a compromised device trustworthy. If the companion is offline, the key is unregistered, evidence is expired, or signature validation fails, the gate is blocked. Version one does not fall back to comment-based evidence.

## 17. Security and Reliability

- Invoke Git and validation tools through argument arrays; never concatenate shell commands.
- Canonicalize every repository, worktree, and validation `cwd`; reject paths outside the mapped repository.
- Apply timeouts and output limits to every process.
- Hash file contents in streaming mode and cap baseline expansion.
- Do not follow symlinks while hashing.
- Redact secrets before storing validation output; store digests when full output is unnecessary.
- Keep gate events append-only at the application layer.
- Recheck issue version immediately before committing a transition.
- Cache no successful result across a changed `HEAD`, index, worktree fingerprint, task version, policy version, or validation profile version.

## 18. Migration and Compatibility

1. Add new tables without changing existing task status values.
2. Existing issues start with no baseline and are not retroactively blocked.
3. Existing `done` issues remain done.
4. An existing active issue becomes gated only after it has a development context and explicitly captures a baseline.
5. Reopening a legacy issue with a bound context captures a new baseline before further work.
6. Older CLI/UI clients receive `DELIVERY_GATE_BLOCKED` from the server and cannot bypass it, even if they cannot render the detailed panel.
7. Cloud migrations add evidence tables and device-key metadata before enabling policy enforcement.

## 19. Test Strategy

### Unit tests

- porcelain-v2 parsing for staged, unstaged, untracked, renamed, deleted, symlink, and submodule states;
- fingerprint comparison, including edits to a file dirty at baseline;
- descendant and target-branch reachability evaluation;
- evidence invalidation and stable check-code mapping;
- actor authorization for acknowledgement and override.

### Server integration tests

- baseline capture is atomic with `todo -> in_progress`;
- uncommitted task delta blocks `in_review`;
- unchanged baseline dirt does not block;
- changed baseline dirt blocks;
- absorbed baseline dirt requires user acknowledgement;
- committed clean task with passing validation enters review;
- stale issue versions still return `VERSION_CONFLICT`;
- missing worktree, timeout, and Git failure fail closed;
- reviewed commit not in target branch blocks `done`;
- reviewed commit in target branch allows `done`;
- Agent override attempts return `403`;
- user override produces immutable audit evidence.

### CLI and skill tests

- JSON output preserves stable gate codes and remediation fields;
- `issue move` cannot bypass the server gate;
- no CLI force flag exists;
- skill text requires commit evidence and prohibits Agent override.

### UI tests

- gate states and warnings render from API data;
- failed drag/move restores the original status;
- blockers receive focus and are keyboard accessible;
- override controls appear only for a user actor;
- stale evidence refreshes before transition.

### Cloud tests

- nonce replay, expired evidence, wrong device signature, wrong task version, and offline companion all fail closed;
- normalized evidence contains no absolute path or raw file content.

## 20. Rollout

Implement in five independently testable slices:

1. Git inspector, fingerprints, schema, and baseline API behind a disabled project flag.
2. Review gate and validation profiles, enabled for one local test project.
3. Done gate, audit events, acknowledgements, and user override.
4. Web UI, CLI diagnostics, and skill update.
5. Cloud companion signing and cloud enforcement.

After slices 1-4 pass locally, enable the gate for Study-Hub code issues. Cloud enforcement remains disabled until slice 5 passes its replay and privacy tests. Rollback disables the project flag; it never deletes baselines, evidence, or audit events.

## 21. Acceptance Criteria

The feature is complete only when all of the following are demonstrated against real temporary Git repositories and the taskboard API:

1. A bound issue with an uncommitted title fix cannot enter `in_review`.
2. Committing that fix and passing the configured validation allows `in_review` and records the exact SHA.
3. Pre-existing dirty files remain visible but do not block when unchanged.
4. Editing a pre-existing dirty file after baseline blocks review.
5. Accidentally committing a pre-existing dirty file requires explicit user acknowledgement.
6. A reviewed commit absent from the target branch cannot enter `done`.
7. Merging the reviewed commit into the target branch allows `done` without requiring a remote push.
8. Missing worktrees and unavailable Git/companion checks fail closed.
9. Codex Agent cannot bypass or override any failed gate.
10. User override is scoped, reasoned, versioned, and permanently auditable.
11. Web, CLI, and automation paths produce the same decision for identical evidence.
12. Cloud evidence exposes no absolute paths or file contents and rejects replayed or unsigned submissions.

## 22. Final Decision

Use a server-enforced, baseline-aware Git delivery gate. Capture content fingerprints at task start, require a committed descendant with user-configured validation for review, require target-branch reachability for done, and fail closed when evidence cannot be verified. Preserve a narrowly scoped, user-only audited override. Do not rely on comments, Agent assertions, client-side checks, or worktree cleanliness alone.
