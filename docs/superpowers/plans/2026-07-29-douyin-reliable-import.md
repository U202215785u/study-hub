# Douyin Reliable Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fragile Douyin HTML scraping with F2-backed preflight, encrypted optional Cookie support, bounded access, local-file recovery, and quality-gated document replacement while preserving existing transcription and LLM models.

**Architecture:** Add a dedicated Douyin import router and focused resolver, secure-settings, access-gate, and preflight services. Confirmed items enter the existing persistent automation queue with normalized source metadata; the existing transcription and summary pipeline remains the only model path. Additive SQLite tables hold preflight, secure settings, access state, and replacement audit records.

**Tech Stack:** FastAPI, SQLite, Python standard-library Windows DPAPI, F2 0.0.1.7 in project-local `.vendor`, Vue 3, Pinia, Vitest, pytest.

---

### Task 1: Add Additive Database Contracts

**Files:**
- Modify: `study-hub/backend/database.py`
- Create: `study-hub/backend/tests/test_douyin_database.py`

- [ ] **Step 1: Write failing schema tests**

Create a temporary database through the existing test fixture and assert that
`secure_settings`, `douyin_preflight_batches`, `douyin_preflight_items`,
`automation_runtime_state`, and `document_replacement_audit` exist. Assert that
one work ID cannot appear twice in the same batch and that the task queue accepts
the new processing states after migration.

- [ ] **Step 2: Run the schema test and verify RED**

Run: `python -m pytest backend/tests/test_douyin_database.py -q`

Expected: failure because the new tables do not exist.

- [ ] **Step 3: Implement additive schema and compatible task migration**

Add the five tables with foreign keys, status checks, timestamps, and unique
constraints. Rebuild `task_queue` only when its status check lacks
`transcribing` or `validating`, copying all existing rows without changing IDs.

- [ ] **Step 4: Verify GREEN and run existing database tests**

Run: `python -m pytest backend/tests/test_douyin_database.py backend/tests/test_deployment_recovery.py -q`

- [ ] **Step 5: Commit**

```bash
git add study-hub/backend/database.py study-hub/backend/tests/test_douyin_database.py
git commit -m "feat: add Douyin preflight storage"
```

### Task 2: Add Windows-Bound Cookie Encryption

**Files:**
- Create: `study-hub/backend/services/__init__.py`
- Create: `study-hub/backend/services/secure_settings.py`
- Create: `study-hub/backend/tests/test_secure_settings.py`

- [ ] **Step 1: Write failing secure-setting tests**

Define the desired functions:

```python
save_secret(conn, "douyin_cookie", "sessionid=secret", protector)
status = secret_status(conn, "douyin_cookie")
value = load_secret(conn, "douyin_cookie", protector)
delete_secret(conn, "douyin_cookie")
```

Assert ciphertext does not contain plaintext, status never exposes a value,
replacement works, deletion works, and values over 20,000 characters fail.

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m pytest backend/tests/test_secure_settings.py -q`

- [ ] **Step 3: Implement DPAPI and injectable protector contract**

Use `CryptProtectData` and `CryptUnprotectData` through `ctypes` on Windows.
Persist base64 ciphertext only. Keep an injectable protector in service tests so
tests prove persistence behavior independently of operating-system state.

- [ ] **Step 4: Verify GREEN**

Run: `python -m pytest backend/tests/test_secure_settings.py -q`

- [ ] **Step 5: Commit**

```bash
git add study-hub/backend/services study-hub/backend/tests/test_secure_settings.py
git commit -m "feat: encrypt local Douyin Cookie"
```

### Task 3: Add F2 Resolver and Access Protection

**Files:**
- Create: `study-hub/requirements-f2.txt`
- Create: `study-hub/scripts/install_f2.ps1`
- Modify: `.gitignore`
- Modify: `THIRD_PARTY_NOTICES.md` if present; otherwise create `study-hub/THIRD_PARTY_NOTICES.md`
- Create: `study-hub/backend/services/douyin_resolver.py`
- Create: `study-hub/backend/services/douyin_access.py`
- Create: `study-hub/backend/tests/test_douyin_resolver.py`
- Create: `study-hub/backend/tests/test_douyin_access.py`

- [ ] **Step 1: Write failing resolver tests**

Test complete share text, direct short links, direct work links, duplicate input,
F2 response normalization, subtitles, audio candidates, explicit download
permission, and the stable errors `cookie_required`, `access_forbidden`,
`rate_limited`, `risk_verification`, `work_unavailable`, `contract_changed`, and
`network_timeout`.

- [ ] **Step 2: Write failing access-gate tests**

Use zero-delay injected sleep and deterministic random values. Assert one active
operation at a time, quota consumption, one retry for timeout, no retry for 403
or 429, and persisted 30-minute circuit behavior.

- [ ] **Step 3: Run both tests and verify RED**

Run: `python -m pytest backend/tests/test_douyin_resolver.py backend/tests/test_douyin_access.py -q`

- [ ] **Step 4: Implement the minimal resolver and access gate**

Pin `f2==0.0.1.7`; install with `--no-deps --target study-hub/.vendor`. Load F2
only from that directory. Normalize F2 data into a `ResolvedWork` dataclass and
never expose response bodies or Cookie values in exceptions or logs.

- [ ] **Step 5: Verify GREEN and install isolated F2**

Run tests, then:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_f2.ps1
```

Verify: `python -c "from backend.services.douyin_resolver import f2_available; assert f2_available()"`

- [ ] **Step 6: Commit**

```bash
git add .gitignore study-hub/requirements-f2.txt study-hub/scripts study-hub/THIRD_PARTY_NOTICES.md study-hub/backend/services study-hub/backend/tests
git commit -m "feat: add bounded F2 Douyin resolver"
```

### Task 4: Add Preflight, Confirmation, Cookie, and Local-File Routes

**Files:**
- Create: `study-hub/backend/services/douyin_preflight.py`
- Create: `study-hub/backend/endpoints/douyin.py`
- Modify: `study-hub/backend/main.py`
- Create: `study-hub/backend/tests/test_douyin_endpoints.py`

- [ ] **Step 1: Write failing endpoint tests**

Cover:

```text
POST   /automation/douyin/preflight
GET    /automation/douyin/preflight/{batch_id}
POST   /automation/douyin/confirm
POST   /automation/douyin/items/{item_id}/local-file
PUT    /automation/douyin/cookie
GET    /automation/douyin/cookie/status
DELETE /automation/douyin/cookie
```

Assert preflight creates no document, confirmation is idempotent, non-ready
items are rejected, Cookie responses contain no plaintext, and invalid local
files are rejected by signature.

- [ ] **Step 2: Run endpoint tests and verify RED**

Run: `python -m pytest backend/tests/test_douyin_endpoints.py -q`

- [ ] **Step 3: Implement preflight service and router**

Enforce 20,000 input characters, ten unique works, server-side URL validation,
replacement-document ownership, stable error payloads, and local upload storage
outside the repository. Confirm ready items by creating existing queue tasks with
`preflight_item_id` and `replace_doc_id`.

- [ ] **Step 4: Verify GREEN and route regression tests**

Run: `python -m pytest backend/tests/test_douyin_endpoints.py backend/tests/test_main.py -q`

- [ ] **Step 5: Commit**

```bash
git add study-hub/backend/services/douyin_preflight.py study-hub/backend/endpoints/douyin.py study-hub/backend/main.py study-hub/backend/tests/test_douyin_endpoints.py
git commit -m "feat: add Douyin preflight endpoints"
```

### Task 5: Feed Confirmed Sources into Existing Models

**Files:**
- Create: `study-hub/backend/services/douyin_content.py`
- Modify: `study-hub/backend/endpoints/automation.py`
- Create: `study-hub/backend/tests/test_douyin_content.py`
- Create: `study-hub/backend/tests/test_douyin_replacement.py`

- [ ] **Step 1: Write failing content-priority tests**

Assert source selection order: inline subtitle, subtitle URL, independent audio,
explicitly permitted media, local upload. Assert unavailable sources return
`local_file_required` rather than metadata-only success.

- [ ] **Step 2: Write failing replacement tests**

Assert fewer than 20 non-whitespace transcript characters, failure markers,
write failure, or reread failure retain the old document. Assert a valid new
document is inserted and reread before old-document removal, and the audit row
records the decision.

- [ ] **Step 3: Run tests and verify RED**

Run: `python -m pytest backend/tests/test_douyin_content.py backend/tests/test_douyin_replacement.py -q`

- [ ] **Step 4: Implement content acquisition and queue integration**

When a task contains `preflight_item_id`, load normalized candidates, update
`transcribing` and `validating` states, invoke the current transcription and
summary functions unchanged, and run replacement quality validation. Keep the
legacy parser behind an internal switch for rollback only.

- [ ] **Step 5: Verify GREEN and automation regressions**

Run: `python -m pytest backend/tests/test_douyin_content.py backend/tests/test_douyin_replacement.py backend/tests/test_main.py -q`

- [ ] **Step 6: Commit**

```bash
git add study-hub/backend/services/douyin_content.py study-hub/backend/endpoints/automation.py study-hub/backend/tests
git commit -m "feat: safely process preflighted Douyin works"
```

### Task 6: Add Preflight and Recovery UI

**Files:**
- Create: `study-hub/frontend/src/components/DouyinImportPanel.vue`
- Create: `study-hub/frontend/src/components/DouyinCookieControl.vue`
- Modify: `study-hub/frontend/src/views/Home.vue`
- Create: `study-hub/frontend/src/tests/douyin-import.test.js`

- [ ] **Step 1: Write failing component tests**

Assert the panel starts preflight instead of direct processing, renders ready,
duplicate, blocked, needs-file, and failed items, submits selected ready IDs,
uploads local media to the same item, and never displays a saved Cookie.

- [ ] **Step 2: Run test and verify RED**

Run: `npm test -- src/tests/douyin-import.test.js`

- [ ] **Step 3: Implement focused components and integrate Home**

Keep existing Bilibili and Xiaohongshu cards unchanged. The Douyin card opens a
preflight panel with stable dimensions, progress, selection, confirmation,
Cookie status/update/clear, local upload, and actionable error states.

- [ ] **Step 4: Verify GREEN and all frontend tests**

Run: `npm test`

- [ ] **Step 5: Commit**

```bash
git add study-hub/frontend/src/components study-hub/frontend/src/views/Home.vue study-hub/frontend/src/tests/douyin-import.test.js
git commit -m "feat: add Douyin preflight workflow"
```

### Task 7: End-to-End Verification and Recovery Check

**Files:**
- Modify only files required by failures found in this task, with a failing test first.

- [ ] **Step 1: Run complete automated verification**

```powershell
python -m pytest backend/tests -q
Set-Location frontend
npm test
npm run build
```

- [ ] **Step 2: Run service smoke checks on a non-production port**

Start the isolated backend on port `8742`. Verify health, Cookie status,
preflight validation, and that preflight does not change document count.

- [ ] **Step 3: Verify the previously failing share text**

Submit the known `f5NZQ93-4aw` share text through preflight. Accept either a
ready result or a precise classified platform/Cookie/risk error; generic
`从HTML中解析视频信息失败` is a failure.

- [ ] **Step 4: Verify local-file recovery and safe replacement**

Use a small local fixture video. Confirm it resumes the same item, passes through
the existing model path when credentials are available, and that a forced
quality failure retains the old document.

- [ ] **Step 5: Review diff and commit verification fixes**

Run `git diff --check`, inspect only this branch's changes, and commit any
test-driven corrections separately.

