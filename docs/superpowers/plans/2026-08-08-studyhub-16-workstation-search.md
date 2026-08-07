# STUDYHUB-16 工作站内部搜索 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the homepage Bing/AI search with a grouped internal Study-Hub search that safely opens internal pages and homepage documents.

**Architecture:** A shared JSON catalog owns feature names, aliases and route navigation. A new FastAPI endpoint searches the catalog plus SQLite-backed documents, Wiki pages, Butler tasks, DDL tasks, journal entries, saved workflows and workflow templates, returning three independently-statused groups. The homepage composable requests that endpoint; a separate panel component renders results and emits only validated route or document actions.

**Tech Stack:** Vue 3, Pinia, Vue Router, Vitest, FastAPI, SQLite, pytest.

---

### Task 1: Shared catalog and backend response contract

**Files:**

- Create: `study-hub/shared/workstation-search-catalog.json`
- Create: `study-hub/backend/tests/test_workstation_search.py`
- Create: `study-hub/backend/endpoints/workstation_search.py`
- Modify: `study-hub/backend/main.py`

- [ ] **Step 1: Write the failing backend contract tests**

  Add tests that seed documents, Wiki, Butler task, DDL task, journal entry and workflow rows; request `GET /workstation/search?q=设计`; assert three groups named `features`, `knowledge`, `records`, each has `status`, document results use `{"kind":"document","document_id":...}`, Wiki results use `/wiki/<slug>`, and record results use only list routes. Add a provider-failure test that monkeypatches one provider to raise and asserts HTTP 200 with that group `status == "unavailable"` and a message.

- [ ] **Step 2: Run the backend test to verify it fails**

  Run: `pytest backend/tests/test_workstation_search.py -q`

  Expected: FAIL because `endpoints.workstation_search` and `/workstation/search` do not exist.

- [ ] **Step 3: Create the single-source feature catalog**

  Create JSON entries with `id`, `title`, `aliases`, `summary`, and `navigation`. Cover `/`, `/kb`, `/wiki`, `/workflow`, `/ddl`, `/journal`, `/workbench`, `/learning`, `/memory`, `/heatmap`, `/sop`, `/creator`, `/skills`, and `/settings`. Every navigation object must be `{ "kind": "route", "path": "<known route>", "query": {} }`.

- [ ] **Step 4: Implement the minimal endpoint**

  In `endpoints/workstation_search.py`, load the catalog from `study-hub/shared/workstation-search-catalog.json`; define pure provider functions for features, documents, Wiki, records and workflow templates; normalize every item to `id`, `kind`, `title`, `summary`, `navigation`; truncate generated summaries; cap each group at five. Return `status: "ready"` for completed group providers. Catch provider exceptions individually, return `status: "unavailable"`, `message`, and empty items for the affected group. Reject blank `q` with HTTP 422. Register the router in `main.py`.

- [ ] **Step 5: Run the backend test to verify it passes**

  Run: `pytest backend/tests/test_workstation_search.py -q`

  Expected: PASS.

### Task 2: Frontend search state and navigation validation

**Files:**

- Modify: `study-hub/frontend/src/composables/home/useHomeSearch.js`
- Modify: `study-hub/frontend/src/composables/home/useHomeSearch.test.js`

- [ ] **Step 1: Write failing composable tests**

  Replace tests for `ai`, `web`, `cmd`, and `kb` modes with tests that assert: focus opens the panel with catalog-backed common features and no API call; a non-empty query calls `apiGet('/workstation/search?q=<encoded>')`; a later response cannot overwrite a newer query; retry repeats the last failed query; and `isSafeNavigation` accepts catalog route targets and document IDs while rejecting an external URL or unknown route.

- [ ] **Step 2: Run the composable test to verify it fails**

  Run: `npm run test:unit -- --run src/composables/home/useHomeSearch.test.js`

  Expected: FAIL because the legacy composable exposes only modes and calls `/ai-search`.

- [ ] **Step 3: Implement the internal-only composable**

  Import the shared catalog JSON. Replace `apiPost`, external opener, commands, modes, RAG and AI state with `apiGet`, `query`, `expanded`, `groups`, `loading`, `error`, `lastQuery`, `assistant`, `open`, `close`, `searchNow`, `scheduleSearch`, and `retry`. Debounce input changes, use a monotonically increasing request ID to ignore stale responses, skip requests for whitespace-only input, and expose a pure `isSafeNavigation` helper that only permits `kind: "route"` catalog paths and positive integer `kind: "document"` IDs.

- [ ] **Step 4: Run the composable test to verify it passes**

  Run: `npm run test:unit -- --run src/composables/home/useHomeSearch.test.js`

  Expected: PASS.

### Task 3: Search input and result panel components

**Files:**

- Modify: `study-hub/frontend/src/design-system/patterns/CapsuleNavigation.vue`
- Create: `study-hub/frontend/src/components/home/WorkstationSearchPanel.vue`
- Create: `study-hub/frontend/src/components/home/WorkstationSearchPanel.test.js`

- [ ] **Step 1: Write failing panel tests**

  Test the panel renders `功能入口`, `文章与知识`, and `工作记录`; renders a group `message` when `status` is `unavailable`; emits `navigate` for a route item and `open-document` for a document item; emits `retry`; and renders the AI assistant row disabled with `暂未开放` and no click emission.

- [ ] **Step 2: Run the panel test to verify it fails**

  Run: `npm run test:unit -- --run src/components/home/WorkstationSearchPanel.test.js`

  Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement the panel and input contract**

  Implement `WorkstationSearchPanel.vue` as a presentational component with props for `query`, `groups`, `loading`, `error`, and `assistant`; emit only `navigate`, `open-document`, `retry`, and `close`. In `CapsuleNavigation.vue`, replace the string-only `search` event with `search-input`, `search-focus`, `search-submit`, and `search-close` events while keeping it free of search results and API calls. Provide accessible roles, labels and disabled semantics.

- [ ] **Step 4: Run component and existing navigation tests**

  Run: `npm run test:unit -- --run src/components/home/WorkstationSearchPanel.test.js src/views/Home.test.js`

  Expected: PASS after Home is wired in Task 4; before that, only the panel test is expected to pass.

### Task 4: Wire the homepage and preserve document reading

**Files:**

- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `study-hub/frontend/src/views/Home.test.js`

- [ ] **Step 1: Write failing homepage interaction tests**

  Mount Home with a mock `apiGet`. Assert focus renders common features without `/workstation/search`; input `设计` requests the new endpoint; a document result calls `/documents/<id>` through the existing `viewDocument` path and shows the DocumentReader modal; a Wiki result pushes `/wiki/<slug>`; a DDL or workflow result pushes only `/ddl` or `/workflow`; an external navigation object does not route; Enter performs the same search; and retry repeats the failed request.

- [ ] **Step 2: Run the homepage test to verify it fails**

  Run: `npm run test:unit -- --run src/views/Home.test.js`

  Expected: FAIL because Home destructures legacy search answer state and passes the old navigation callback.

- [ ] **Step 3: Wire search events and safe actions**

  Instantiate `useHomeSearch({ apiGet: settings.apiGet })`. Render `WorkstationSearchPanel` next to the navigation slot only while `expanded` is true. Handle route items through `router.push` only after `isSafeNavigation`; handle document items through existing `viewDocument(documentId)`; close the panel after a successful navigation or document open. Keep Escape/focus restoration integrated with the current surface handling.

- [ ] **Step 4: Run homepage tests to verify they pass**

  Run: `npm run test:unit -- --run src/views/Home.test.js src/composables/home/useHomeSearch.test.js src/components/home/WorkstationSearchPanel.test.js`

  Expected: PASS.

### Task 5: Remove the retired internet search surface

**Files:**

- Delete: `study-hub/backend/endpoints/ai_search.py`
- Delete: `study-hub/backend/tests/test_ai_error_contract.py`
- Modify: `study-hub/backend/main.py`
- Modify: `study-hub/README.md`
- Modify: `study-hub/frontend/src/views/Home.test.js`

- [ ] **Step 1: Write failing regression checks**

  Add a backend test asserting `/workstation/search` is registered and `/ai-search` returns 404. Add a frontend test asserting no call to `/ai-search` occurs when searching from the homepage.

- [ ] **Step 2: Run the regression tests to verify they fail**

  Run: `pytest backend/tests/test_workstation_search.py -q; npm run test:unit -- --run src/views/Home.test.js`

  Expected: the `/ai-search` assertion fails while the old router remains registered.

- [ ] **Step 3: Remove only the unused external-search endpoint**

  Delete `ai_search.py` and its dedicated error-contract test, remove `ai_search_router` import and `include_router` call from `main.py`, replace README API references with `/workstation/search`, and remove legacy `/ai-search` mocks/assertions from Home tests. Do not remove `/rag/query`; it remains a separate knowledge-base API.

- [ ] **Step 4: Run retirement tests to verify they pass**

  Run: `pytest backend/tests/test_workstation_search.py -q; npm run test:unit -- --run src/views/Home.test.js`

  Expected: PASS, and `rg -n "/ai-search|_bing_search" study-hub/backend study-hub/frontend` returns no runtime code references.

### Task 6: Full verification and task evidence

**Files:**

- Modify: `docs/superpowers/specs/2026-08-04-studyhub-16-workstation-search-design.md` only if verification reveals a genuine contract correction.

- [ ] **Step 1: Run focused backend and frontend suites**

  Run: `pytest backend/tests/test_workstation_search.py -q; npm run test:unit -- --run src/composables/home/useHomeSearch.test.js src/components/home/WorkstationSearchPanel.test.js src/views/Home.test.js`

  Expected: all selected tests pass.

- [ ] **Step 2: Run production build and static search checks**

  Run: `npm run build; rg -n "/ai-search|_bing_search|bing.com/search" backend frontend/src -g '!node_modules'`

  Expected: build succeeds; static search returns no production runtime references.

- [ ] **Step 3: Perform a browser smoke check**

  Verify focus, default features, internal result groups, unavailable-group message, disabled AI row, document modal opening, Wiki/list-page navigation, and retry state in the running homepage.

- [ ] **Step 4: Record evidence and finish the task**

  Record changed files, tests, build result and original-user-phenomenon validation with the Study-Hub butler; leave STUDYHUB-16 in review rather than done unless the user explicitly accepts completion.
