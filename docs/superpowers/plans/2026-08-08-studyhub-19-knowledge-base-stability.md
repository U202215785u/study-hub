# STUDYHUB-19 Knowledge Base Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate duplicate active documents, let users browse every document, and make ASR/reparse status accurate and traceable.

**Architecture:** SQLite remains the source of truth and Chroma remains a derived index. A stable platform content key controls document identity; the existing `task_queue` records each recognition outcome; a cursor-paginated API provides the UI with every active document without breaking the legacy list endpoint.

**Tech Stack:** FastAPI, SQLite, ChromaDB, Python pytest/httpx, Vue 3, Pinia, Vitest.

---

## Delivery order and safety gates

Implement in the order below. Do not run the historical reconciliation task until the backup, dry-run report, and user approval gate have all succeeded. Do not delete documents or summary files; “cleanup” means reversible archival.

| Phase | User-visible outcome | Release gate |
|---|---|---|
| A | Stable data model and read-only audit | migration tests pass |
| B | All active documents are browsable | pagination API and UI tests pass |
| C | Reparse status is truthful | worker + UI tests pass |
| D | Startup can no longer duplicate sources | recovery idempotence test passes |
| E | Existing duplicates are archived safely | backup, dry-run report, explicit approval |

### Task 1: Add a focused document-identity module and schema migration

**Files:**

- Create: `study-hub/backend/knowledge_identity.py`
- Modify: `study-hub/backend/database.py`
- Create: `study-hub/backend/tests/test_knowledge_identity.py`

- [ ] **Step 1: Write failing identity tests.** Cover identical Douyin short links resolving to the same short-key, identical long video URLs resolving to the same video-key, a short key being distinct from a video key, an unsupported URL returning `None`, and a title-only document never receiving a guessed key.

```python
def test_douyin_short_and_long_urls_use_distinct_namespaces():
    assert source_identity("douyin-summary", "https://v.douyin.com/ZWW0XlOlwdM/") == "douyin:short:ZWW0XlOlwdM"
    assert source_identity("douyin-summary", "https://www.douyin.com/video/7634595063334554889") == "douyin:7634595063334554889"
```

- [ ] **Step 2: Implement `source_identity(source, url)` and `extract_source_url(content)`.** Long URLs return a video-ID key; short URLs return `douyin:short:<code>`; they are never equated during historical migration. Keep all parsing in `knowledge_identity.py`, return `None` for unsafe formats, and do not perform network requests or follow short links in migration code.

- [ ] **Step 3: Extend `init_db()` with idempotent columns and tables.** Add these nullable/defaulted fields to `documents`: `source_key TEXT`, `source_url TEXT`, `document_status TEXT NOT NULL DEFAULT 'active'`, `duplicate_of_document_id INTEGER`, `asr_status TEXT NOT NULL DEFAULT 'not_applicable'`, `asr_error TEXT DEFAULT ''`, and `updated_at TIMESTAMP`. Extend `task_queue` with `document_id`, `reparse_mode`, `asr_status`, and `asr_error`; do not create a competing attempt table.

- [ ] **Step 4: Add indexes and an immediate identity claim.** Create `idx_documents_active_source_key` on `(source, source_key, document_status)` and `idx_documents_active_created_id` on `(document_status, created_at DESC, id DESC)`. Create `document_source_claims(source, source_key, document_id UNIQUE)` so new imports have a database-level claim even before historical duplicates are archived. Build the partial unique index on active `documents` only after reconciliation has removed collisions.

- [ ] **Step 5: Run tests.**

```powershell
py -3 -m pytest study-hub/backend/tests/test_knowledge_identity.py -q
```

Expected: all identity and idempotent-migration tests pass.

### Task 2: Build a dry-run reconciliation service before any archival

**Files:**

- Create: `study-hub/backend/knowledge_reconciliation.py`
- Create: `study-hub/backend/tests/test_knowledge_reconciliation.py`
- Modify: `study-hub/backend/endpoints/automation.py`

- [ ] **Step 1: Write failing tests using a temporary SQLite database.** Seed two active documents with the same known `source_key`, one document with no detectable key, and fake Chroma calls. Assert dry-run makes no writes and returns a group containing `keep_id`, `archive_ids`, content-hash comparison, and an `unresolved` entry.

- [ ] **Step 2: Implement `build_reconciliation_report(conn)`.** The keeper is the newest successfully transcribed document; otherwise choose the newest active document. Never select an `archived_duplicate` row. Include source URLs and document IDs in the report so a user can review it.

- [ ] **Step 3: Implement `archive_duplicates(conn, approved_keys)`.** It may only change rows whose source key appears in the approved set. Set `document_status='archived_duplicate'` and `duplicate_of_document_id=keep_id`; do not delete content. Return a manifest of actual changes.

- [ ] **Step 4: Add protected maintenance endpoints.** `POST /documents/reconciliation/dry-run` returns the report. `POST /documents/reconciliation/archive` accepts only reviewed `source_key` values and must be called only after the project approval flow authorizes the archival operation.

- [ ] **Step 5: Synchronize vectors.** After an archival transaction commits, delete only the archived rows’ vectors; after restore, enqueue a vector rebuild for the restored row. A vector failure must be reported, not silently treated as a successful reconciliation.

- [ ] **Step 6: Run tests.**

```powershell
py -3 -m pytest study-hub/backend/tests/test_knowledge_reconciliation.py -q
```

Expected: dry-run has no data writes; archive is scoped, reversible, and produces a manifest.

### Task 3: Provide a stable, full-pagination document API

**Files:**

- Modify: `study-hub/backend/endpoints/upload.py`
- Modify: `study-hub/backend/tests/test_main.py`
- Create: `study-hub/backend/tests/test_document_pagination.py`

- [ ] **Step 1: Write endpoint tests.** Seed 53 active documents, including several with the identical `created_at`. Request two pages with `page_size=50`; assert 53 unique IDs are returned, archived duplicates never appear, `total == 53`, and repeated requests return the same order.

- [ ] **Step 2: Add `GET /documents/page`.** Accept existing filters plus `page_size` (1–100) and optional opaque `cursor`. Query only `document_status='active'` and order by `created_at DESC, id DESC`. Encode the final `(created_at, id)` tuple as the cursor; reject malformed cursors with HTTP 400.

```json
{
  "items": [{ "id": 327, "title": "…" }],
  "next_cursor": "eyJjcmVhdGVkX2F0Ijoi…",
  "total": 101
}
```

- [ ] **Step 3: Preserve `GET /documents`.** Keep its array response for MCP and older callers, but add `document_status='active'` and the secondary `id` sort. Do not change its response shape in this release.

- [ ] **Step 4: Preserve the legacy state field in Phase B.** Pagination returns stored `asr_status`/`asr_error`, but legacy `/documents` retains `asr_failed` until the Task 5 backfill, `list_reparseable()` conversion, and frontend badge migration land in the same release. Do not remove any content scan in this phase.

- [ ] **Step 5: Run tests.**

```powershell
py -3 -m pytest study-hub/backend/tests/test_document_pagination.py study-hub/backend/tests/test_main.py -q
```

Expected: 53 documents are reachable across pages, order is stable, and legacy consumers still receive an array.

### Task 4: Make importer and startup recovery idempotent by source key

**Files:**

- Modify: `study-hub/backend/endpoints/automation.py`
- Modify: `study-hub/backend/watcher.py`
- Create: `study-hub/backend/tests/test_orphan_recovery.py`

- [ ] **Step 1: Write recovery idempotence tests.** Place two Markdown files with different titles/body wording but the same Douyin source URL in a temporary summaries directory. Run recovery twice. Assert one active document exists, the second run creates zero records, and the audit names the existing document.

- [ ] **Step 2: Add a shared import/upsert helper.** The helper receives `source`, `source_url`, `source_key`, content, and metadata. It atomically creates or claims one active document for a key; otherwise it updates the known same-source document only if the incoming content is an intended newer result. For a newly parsed Douyin import, use `_extract_douyin_raw()`'s `video_id` and canonical long URL, never its submitted short link.

- [ ] **Step 3: Refactor `recover_orphan_summaries()`.** It must use the helper, record every `created`, `updated`, `skipped`, and `unresolved` decision, and leave unresolved files out of the active list. Historical short links remain in the `douyin:short:*` namespace and are reported as possible cross-namespace matches rather than being guessed into a video-ID key. The function must remain safe when called multiple times at startup.

- [ ] **Step 4: Refactor automated import and inbox import.** Populate source identity at the initial insert rather than trying to infer it only when an error occurs.

- [ ] **Step 5: Run tests.**

```powershell
py -3 -m pytest study-hub/backend/tests/test_orphan_recovery.py -q
```

Expected: restart recovery is idempotent and source-equivalent imports do not create second active documents.

### Task 5: Separate task completion from ASR outcome

**Files:**

- Modify: `study-hub/backend/endpoints/automation.py`
- Create: `study-hub/backend/tests/test_document_processing_status.py`

- [ ] **Step 1: Write worker tests for four outcomes.** Mock extraction for `succeeded`, `fallback`, `failed`, and a still-running reparse. Assert the document row and the associated `task_queue` row receive the expected explicit statuses.

- [ ] **Step 2: Create an in-place reparse task before queuing.** `POST /automation/reparse/{doc_id}` must set the target document to `pending`, create/update its `task_queue` row with `document_id=doc_id` and `reparse_mode='in_place'`, and return `{ status: 'queued', task_id, document_id }`. It must not create a placeholder document or schedule `_delete_replaced_doc`.

- [ ] **Step 3: Split worker import paths explicitly.** A new import may retain the existing placeholder flow. An in-place reparse is selected from `task['reparse_mode']`: preserve the target row and its old content until the new result is valid; on success, `UPDATE` that target row, delete its existing Chroma vectors, add chunks for the new body, then mark the task/document `succeeded` or `fallback`; on failure, retain the old body and set only the target’s `asr_status='failed'` plus sanitized error. `_delete_replaced_doc` must never run for in-place reparse.

- [ ] **Step 4: Add a single-task status endpoint.** `GET /automation/tasks/{task_id}` returns the task lifecycle and the associated document’s `asr_status`, never raw credentials or unrestricted tracebacks.

- [ ] **Step 5: Backfill and cut over atomically.** Add a one-time migration that assigns `fallback` or `failed` for known historical marker patterns, writes a migration audit count, and never re-runs after a stored value exists. In the same pull request, change `list_reparseable()` to query `asr_status IN ('fallback','failed')`, change list/detail responses to use stored state, and remove legacy `asr_failed` only after the frontend no longer reads it.

- [ ] **Step 6: Run tests.**

```powershell
py -3 -m pytest study-hub/backend/tests/test_document_processing_status.py -q
```

Expected: a fallback article is never reported as ASR success, and the UI has a task ID to follow.

### Task 6: Replace the 50-document UI with a paginated, status-aware experience

**Files:**

- Modify: `study-hub/frontend/src/views/KnowledgeBase.vue`
- Modify: `study-hub/frontend/src/composables/home/useKnowledgeDocuments.js`
- Modify: `study-hub/frontend/src/composables/home/useKnowledgeDocuments.test.js`
- Create: `study-hub/frontend/src/views/KnowledgeBase.pagination.test.js`

- [ ] **Step 1: Write composable tests.** Mock `{items: first50, next_cursor, total: 101}` then a final page. Assert `loadMore()` appends without duplicate IDs, preserves active category/sort, and displays `101` as the total rather than `50`.

- [ ] **Step 2: Add pagination state.** Keep `documents`, `nextCursor`, `totalDocuments`, `isLoadingMore`, and `hasMore` in the composable. `reload()` resets cursor and data; `loadMore()` uses the returned cursor and is ignored while another request is active.

- [ ] **Step 3: Update the KnowledgeBase view.** Show `“已显示 50 / 101 篇”`, a “加载更多” button, and an empty state that distinguishes “no documents” from “no matching filter”. Do not fetch all pages eagerly.

- [ ] **Step 4: Display structured processing status.** Replace the existing `v-if="doc.asr_failed"` control with clear badges for `处理中`, `转写完成`, `仅元数据摘要`, and `识别失败`; show `asr_error` only for failure/fallback. Do not inspect Markdown text in Vue to determine this badge. This change ships with Task 5 Step 5, not before it.

- [ ] **Step 5: Follow reparse tasks.** After a queued response, disable the repeat button for that document and poll the single-task endpoint with bounded backoff until terminal state. Reload the relevant page after terminal status, then show the exact success/fallback/failure message.

- [ ] **Step 6: Run frontend tests.**

```powershell
Set-Location study-hub/frontend
npm run test -- --run src/composables/home/useKnowledgeDocuments.test.js src/views/KnowledgeBase.pagination.test.js
```

Expected: all 101 documents are reachable through paging, and a queued reparse does not immediately present stale failure state as a new result.

### Task 7: Safely execute the historical reconciliation only after approval

**Files:**

- Create: `study-hub/backend/scripts/reconcile_knowledge_base.py`
- Create: `study-hub/backend/tests/test_reconciliation_script.py`
- Create at runtime: `study-hub/backend/data/backups/study_hub-before-reconciliation-<timestamp>.db`
- Create at runtime: `study-hub/backend/data/operations/reconciliation-<timestamp>.json`

- [ ] **Step 1: Write dry-run script tests.** Verify the script defaults to dry-run, writes no document status changes, and emits a report containing pre-run counts and the candidate list.

- [ ] **Step 2: Implement backup-first execution.** The script must reject `--apply` without `--approved-report <path>`, create a timestamped database backup, run `PRAGMA integrity_check`, write the manifest, then archive only report-approved keys.

- [ ] **Step 3: Request explicit high-impact approval.** Present the generated report to the user, including every `source_key`, keeper, archived IDs, unresolved count, and backup path. Do not run `--apply` until the approval tool and the user both approve the exact scope.

- [ ] **Step 4: Rebuild/validate Chroma.** Verify archived IDs have no active vectors and all active IDs have the expected chunk count. Report failures as a blocked rollout, not a successful cleanup.

- [ ] **Step 5: Run final verification.**

```powershell
py -3 -m pytest study-hub/backend/tests/test_reconciliation_script.py -q
Invoke-RestMethod 'http://127.0.0.1:8741/documents/page?page_size=100'
```

Expected: the report reconciles counts, no duplicate active source key remains, and a restore from backup is documented and tested on a copy.

### Task 8: Regression suite and release checklist

**Files:**

- Modify: `study-hub/backend/tests/test_main.py`
- Modify: `study-hub/frontend/src/composables/home/useKnowledgeDocuments.test.js`
- Create: `study-hub/docs/knowledge-base-reconciliation-runbook.md`

- [ ] **Step 1: Add end-to-end API regression coverage.** Test import → duplicate source URL → reparse fallback → restart recovery → paginated list; assert only one active source key and correct explicit status at each step.

- [ ] **Step 2: Write the operator runbook.** Include backup location, dry-run command, approval checkpoint, apply command, vector validation, restore procedure, and the exact signals that require rollback.

- [ ] **Step 3: Run the focused suites.**

```powershell
py -3 -m pytest study-hub/backend/tests/test_knowledge_identity.py study-hub/backend/tests/test_knowledge_reconciliation.py study-hub/backend/tests/test_document_pagination.py study-hub/backend/tests/test_orphan_recovery.py study-hub/backend/tests/test_document_processing_status.py -q
Set-Location study-hub/frontend
npm run test -- --run src/composables/home/useKnowledgeDocuments.test.js src/views/KnowledgeBase.pagination.test.js
```

Expected: all suites pass before any historical archival is requested.

- [ ] **Step 4: Commit only the scoped implementation.** Before any branch switch, merge, or worktree operation, run `bash scripts/check-uncommitted.sh` where available (or record the equivalent Git status on Windows). Stage only files in this plan; never sweep up unrelated existing changes.

## Plan self-review

- Coverage: identity, migration safety, pagination, recovery, reparse truthfulness, vector consistency, archival approval, and regression checks each have a dedicated task.
- No destructive operation occurs automatically; archival is report-scoped, backup-first, and approval-gated.
- Compatibility: legacy `/documents` remains an array endpoint; the new UI adopts `/documents/page` separately.
