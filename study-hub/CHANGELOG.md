# Changelog

## 0.6.0 - 2026-08-09

### Added

- Configurable home dashboard layout with persisted module visibility and drag positions.
- Today-task category cards with click, drag, and keyboard rotation, plus category-aware task creation.
- Internal workstation search for product routes, documents, Wiki pages, tasks, reviews, and workflows.
- Content-parser workspace restoration and configurable heatmap taskboard view.
- Douyin video and image-note classification, bounded image validation, and visual-summary fallback support.

### Changed

- Knowledge-base document identity, duplicate handling, pagination, processing state, and recovery are more stable.
- Today-task category counts use all selected-day tasks while the visible list remains intentionally capped.
- Frontend, backend, and Electron application metadata now report the same 0.6.0 version.

### Fixed

- Local Douyin parsing now loads the repository-backed 1.3.0 parser, reports incompatible runtime versions clearly, and keeps background restarts from being blocked by an existing service on port 8741.
- Dashboard Flip animations now use the GSAP Flip `onEnter` and `onLeave` callbacks, avoiding invalid tween-property warnings after layout changes.
- Pagination regression coverage is isolated from the session-shared test database and no longer depends on test execution order.
- Electron production dependencies override `fast-uri` to 3.1.5, clearing the audited production dependency advisory.

### Release Scope and Known Limits

- This is a release candidate only. No deployment, distribution, or production release is performed by this change.
- Six knowledge documents with insufficient source identity remain unresolved rather than being automatically archived. The active collection contains 79 documents; 23 duplicates remain recoverable as `archived_duplicate`.
- Douyin image-note summaries require the validated source image URLs to remain reachable while analysis runs.
- `STUDYHUB-13` is explicitly excluded from this candidate: the Dashi Taskboard Git delivery-gate branch `codex/taskboard-git-delivery-gate` requires its own audit and validation before release inclusion.
- Electron's development and packaging toolchain still reports 12 high and 1 critical dependency advisories. Their available automated remediation requires breaking Electron and electron-builder major-version upgrades, so it is deliberately outside this candidate.
