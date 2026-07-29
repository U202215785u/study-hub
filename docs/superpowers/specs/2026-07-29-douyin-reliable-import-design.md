# Study Hub Douyin Reliable Import Design

## Goal

Upgrade Study Hub's Douyin ingestion so it has TokBrain-style preflight,
bounded platform access, optional encrypted Cookie support, multiple content
sources, local-file recovery, explicit errors, and safe document replacement.
The existing speech-recognition models, LLMs, prompts, and knowledge-search
behavior remain unchanged.

## Scope

Included:

- Parse full Douyin share text and public links.
- Resolve work metadata through an isolated F2 runtime.
- Optionally use a manually supplied Douyin Cookie encrypted for the current
  Windows user.
- Preflight every work before processing or replacing a document.
- Prefer subtitles, then independent audio, then permitted full media.
- Accept a local video as recovery when public media cannot be processed.
- Classify platform, network, media, transcription, summary, and quality errors.
- Protect existing documents until replacement content passes validation.
- Expose batch progress, actionable failures, retry, cancellation, and upload.

Excluded:

- Changes to the current speech-recognition models or LLMs.
- Changes to summary prompts.
- Browser automation, automatic login, browser Cookie extraction, CAPTCHA
  handling, or platform-risk bypass.
- Changes to Bilibili, Xiaohongshu, ordinary uploads, search, or RAG behavior.
- Background account scanning or unattended resumption of platform access.

## Dependency Decision

Use F2 `0.0.1.7`, licensed under Apache-2.0, as a non-official Douyin work
resolver. Install it with `--no-deps` into a project-local ignored vendor
directory. Its obsolete exact dependency pins must not alter Study Hub's main
Python environment; compatible runtime dependencies are declared and installed
separately.

This dependency may stop working when Douyin changes its behavior. Study Hub
must expose that as `contract_changed`, retain the local-file recovery path,
and never present F2 as an official or permanently reliable service.

## System Blueprint

```text
Share text
  -> input normalization and deduplication
  -> bounded F2 preflight <- encrypted optional Cookie
  -> preflight result
       -> ready
       -> duplicate
       -> needs local file
       -> actionable failure
  -> user selection and confirmation
  -> content acquisition
       -> inline subtitle
       -> subtitle URL
       -> independent audio
       -> permitted full video
       -> uploaded local video
  -> existing transcription
  -> existing LLM summary
  -> quality validation
       -> valid: insert new document, then replace requested old document
       -> invalid: retain old document and failed task
```

## Module Boundaries

### Douyin Resolver

Owns input URL normalization, short-link resolution, F2 response validation,
metadata normalization, subtitle/audio/media candidates, download permission,
and stable resolver errors. It does not write documents or call an LLM.

### Access Gate

Owns serialized Douyin access, daily quota, random cooldown, bounded retry, and
the persisted risk circuit. It does not interpret content or task results.

### Secure Settings

Owns current-Windows-user encryption, encrypted Cookie persistence, status,
replacement, and deletion. Plaintext Cookie values never appear in responses or
logs.

### Preflight Service

Owns batches, normalized candidate items, duplicate detection, selection
eligibility, replacement intent, and local-file requirements. Preflight never
creates or deletes a knowledge document.

### Content Acquisition

Owns the ordered content-source policy and temporary local assets. It returns
text or a local media path to the existing transcription pipeline and cleans up
temporary files after the terminal task state.

### Existing Automation Pipeline

Continues to own transcription, summary generation, document rendering, and
task persistence. It receives normalized source material rather than scraping
Douyin itself.

### Replacement Guard

Owns quality validation and the atomic sequence for inserting a replacement,
verifying it can be read, and only then removing the old document. It records
the decision and retains the old document on every failure path.

### Frontend

Owns share-text entry, preflight status, selection and confirmation, progress,
Cookie status and manual update, local-file upload, actionable errors, retry,
cancel, and replacement warnings.

## Critical User Journeys

### New Import

1. The user pastes up to ten share texts or links.
2. Study Hub preflights each unique work without creating documents.
3. The user reviews metadata and available content sources.
4. The user confirms selected ready items.
5. Study Hub acquires the best allowed source, uses the existing transcription
   and summary pipeline, validates the result, and inserts the document.

### Restricted Platform Access

1. F2 reports Cookie, permission, rate-limit, or risk-verification failure.
2. Study Hub maps it to a stable error code and actionable Chinese message.
3. A 403, 429, or risk-verification response opens a 30-minute circuit and
   prevents queued platform access from continuing.
4. No failed article is created. The user may update the Cookie, retry after
   cooldown, or provide a local file when appropriate.

### Safe Re-identification

1. A failed existing article starts preflight with `replace_doc_id`.
2. The old article remains visible through preflight and processing.
3. New source text and summary must pass the quality rules.
4. Study Hub inserts and rereads the new article before removing the old one.
5. Any error retains the old article and records an actionable failed task.

## Interface Contracts

### Create Preflight

`POST /automation/douyin/preflight`

Input:

```json
{
  "input": "full share text or URL",
  "replace_doc_id": null
}
```

Constraints:

- `input` is required, nonblank, and at most 20,000 characters.
- A request may contain at most ten unique Douyin works.
- `replace_doc_id` is optional and must identify an existing Douyin summary.
- The server extracts and validates links independently of the frontend.

Output:

```json
{
  "batch_id": "string",
  "items": [
    {
      "item_id": "string",
      "work_id": "string or null",
      "title": "string",
      "author": "string or null",
      "duration_seconds": 30.0,
      "status": "ready",
      "content_sources": ["subtitle", "audio"],
      "replace_doc_id": null,
      "error_code": null,
      "error_message": null
    }
  ]
}
```

Side effects are limited to preflight records, quota accounting, and risk-state
updates. This operation never creates, replaces, or deletes a knowledge article.

### Confirm Preflight Items

`POST /automation/douyin/confirm`

Input:

```json
{
  "batch_id": "string",
  "item_ids": ["string"]
}
```

Only items in `ready` may be confirmed. Confirmation is idempotent: repeated
confirmation returns the existing task identifiers and does not consume model
usage twice. Empty, unknown, expired, duplicate, or non-ready selections return
a validation error without creating tasks.

### Upload Local Recovery Media

`POST /automation/douyin/items/{item_id}/local-file`

Accept one `mp4`, `mov`, `mkv`, or `webm` file up to 1 GiB. Validate actual
container signatures and reject extension-only spoofing. The item must belong
to an active preflight and be `needs_local_file` or `failed`. The file remains
local, is bound to that item, and is deleted after the terminal processing
state unless cleanup itself fails and is reported.

### Cookie Management

- `PUT /automation/douyin/cookie` accepts a nonblank Cookie up to 20,000
  characters and replaces the previous encrypted value.
- `GET /automation/douyin/cookie/status` returns only `configured` and
  `updated_at`.
- `DELETE /automation/douyin/cookie` removes the encrypted value.

Plaintext Cookie values are never returned. Cookie mutations are audited
without logging the value.

## State Model

Preflight item states:

```text
preflighting
ready
duplicate
needs_local_file
blocked
failed
cancelled
```

Confirmed task states:

```text
queued
extracting
transcribing
summarizing
validating
done
error
cancelled
```

`done` means a quality-valid result is durable and readable. It never means
merely that a worker stopped running.

## Stable Error Codes

```text
invalid_input
cookie_required
cookie_expired
access_forbidden
rate_limited
risk_verification
work_unavailable
contract_changed
network_timeout
media_expired
media_missing
local_file_required
transcription_failed
summary_failed
quality_check_failed
```

Every error includes a stable code, an actionable Chinese message, and a retry
classification. Sensitive URLs, Cookie values, response bodies, and local paths
must not appear in user-facing errors or ordinary logs.

## Content-Source Policy

Use the first viable source in this order:

1. Inline subtitle text.
2. Allowed subtitle URL.
3. Independent audio candidate.
4. Full media only when the work explicitly permits download.
5. User-supplied local media.

If none is viable, set `local_file_required`; do not create a metadata-only
article and call it successfully recognized.

## Replacement Quality Rules

A replacement is eligible only when all conditions hold:

1. Subtitle or transcription text exists.
2. It contains at least 20 non-whitespace characters.
3. The rendered summary contains no recognized failure marker.
4. The new document is committed successfully.
5. The new document can be read back successfully.

Only after all five checks may the old document be removed. The insertion and
replacement decision use a database transaction where possible; failures roll
back and retain the old article. Replacement decisions are written to an audit
log without storing secrets.

## Access Policy

- Serialize all short-link resolution, F2 detail access, and public media
  requests through one access gate.
- Wait a random four to eight seconds after every platform request.
- Retry network timeout or upstream server error at most once after a random
  15-to-30-second delay.
- Do not retry 403, 429, CAPTCHA, or risk-verification responses.
- Persist a 30-minute circuit for those risk responses.
- Limit each batch to ten works and each Asia/Shanghai calendar day to 150 F2
  detail attempts.
- Never automatically resume platform access after application restart when a
  persisted risk circuit is active.

## Three-Layer Defense

### Input and UI

- Enforce input count, length, file type, and file-size feedback before submit.
- Require explicit confirmation before processing and before destructive
  removal.
- Provide loading, empty, blocked, needs-file, error, cancel, and success states.
- Never render or retrieve the saved Cookie value after submission.

### Service Logic

- Revalidate all links and identifiers server-side.
- Make confirmation idempotent and reject stale or non-ready items.
- Keep plaintext Cookie scope limited to the resolver call.
- Enforce serialized platform access, quota, cooldown, retry, and circuit rules.
- Roll back replacement on failure and retain the existing article.
- Validate local media before binding it to a task.

### Data and Infrastructure

- Use parameterized queries and foreign keys for preflight, task, and document
  relationships.
- Add uniqueness for platform plus work ID and for confirmed preflight items.
- Encrypt Cookie data with current-Windows-user protection.
- Audit Cookie mutations and document replacement decisions without secrets.
- Keep temporary media outside the repository and remove it at terminal state.

## Data Changes

Use Study Hub's existing SQLite database. Add focused storage for:

- Douyin preflight batches and items.
- Platform work ID, normalized URL, source availability, stable error code, and
  replacement intent.
- Encrypted secure settings and their timestamps.
- Persisted access circuit and daily attempt counter.
- Replacement audit records.

The existing `task_queue` remains the confirmed processing queue. It receives
new processing states and a reference to the confirmed preflight item. Existing
task records remain readable after migration.

## Verification Strategy

### Unit Tests

- Full share-text extraction, direct links, duplicates, and invalid input.
- F2 response normalization and every stable error classification.
- Cookie encryption round trip, wrong-user failure, status, replacement, and
  deletion without plaintext leakage.
- Access serialization, quota, cooldown, bounded retry, and circuit persistence.
- Content-source priority and local-file validation.
- Replacement quality pass, fail, rollback, and idempotency.

### Integration Tests

- Preflight does not create a document.
- Confirmation creates one task once.
- Cookie-required failure becomes ready after a configured resolver succeeds.
- Local upload resumes the same item.
- Failed re-identification retains the old article.
- Valid re-identification inserts and rereads the new article before removal.

### User-Visible Verification

- Paste the previously failing share text and receive a preflight result or a
  precise platform error instead of generic HTML failure.
- Process one F2-resolved work through the unchanged models.
- Force a platform failure and complete it through local upload.
- Restart the service and verify task, circuit, and Cookie status recovery.
- Build the frontend and run existing backend and frontend checks without new
  errors.

## Recovery and Rollback

- Keep the old Douyin parser available behind an internal switch during initial
  verification, but do not silently fall back after a classified F2 risk error.
- Database migrations are additive until the new path is verified.
- Back up the SQLite database before the migration is applied.
- Removing the feature consists of disabling the new route path, restoring the
  prior frontend entry, and leaving additive records untouched until an
  explicitly confirmed cleanup.
- Uninstalling F2 means removing only the project-local vendor directory; it
  does not alter the main Python environment.

## Acceptance Criteria

- Existing models and prompts are unchanged.
- The previously failing share text no longer fails because Study Hub attempted
  to parse the initial HTML shell.
- Preflight never creates or deletes a knowledge article.
- A failed recognition never replaces an existing article.
- Cookie content is encrypted at rest and never returned or logged.
- Platform risk responses pause further access instead of causing a retry storm.
- A failed public-link item can continue with a valid local video.
- Existing Bilibili, Xiaohongshu, upload, search, and knowledge workflows pass
  their current checks.
