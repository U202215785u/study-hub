# STUDYHUB-7 Grid Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `test-driven-development` task-by-task. Every production behavior begins with a focused failing test.

**Goal:** Let users freely place homepage modules in a controlled eight-column grid, with deterministic placement, local persistence, and responsive mobile reading order.

**Architecture:** A DOM-free layout engine owns legal widget dimensions, v1-to-v2 migration, reading order, collision resolution, placement, and validation. `useDashboardLayout` owns saved and draft state. The homepage renders explicit grid coordinates on desktop; a pointer-events composable translates drag gestures into grid targets. Mobile derives a single-column reading order from the same layout rather than replaying desktop coordinates.

**Tech Stack:** Vue 3, CSS Grid, Pointer Events, existing GSAP FLIP integration when present, Vitest, Vue Test Utils, Playwright.

---

## Scope and invariants

- Reuse the existing `study-hub:dashboard-layout:v1` storage key and migrate its v1 payload in place.
- Persist only `id`, `visible`, `x`, `y`, and `order`; derive width and height from `SIZE_RULES`.
- `order` is always the stable reading order sorted by `(y, x, previousOrder)`.
- Every saved visible widget has legal coordinates, no overlap, and `x + width <= 8`.
- Placement is deterministic: conflict resolution scans same-column downward first, then row-major free positions, then appends rows.
- Desktop editing starts only on a dedicated handle. Card content remains clickable.
- Desktop is explicit CSS Grid placement, never `grid-auto-flow: dense`.
- Mobile is one column with automatic card height; each affected widget must have a narrow-width overflow assertion.

## File map

- `study-hub/frontend/src/design-system/layout/dashboardLayout.js`: pure layout model and algorithms.
- `study-hub/frontend/src/design-system/layout/dashboardLayout.test.js`: migration, ordering, placement and collision contracts.
- `study-hub/frontend/src/design-system/layout/dashboardRegistry.js`: v2 normalization boundary.
- `study-hub/frontend/src/composables/home/useDashboardLayout.js`: drafts, persistence, undo and layout mutation API.
- `study-hub/frontend/src/composables/home/useDashboardLayout.test.js`: save/cancel/undo/reinsert behavior.
- `study-hub/frontend/src/composables/home/useGridDrag.js`: Pointer Events gesture adapter.
- `study-hub/frontend/src/composables/home/useGridDrag.test.js`: click threshold and grid-target mapping.
- `study-hub/frontend/src/design-system/patterns/BentoDashboardGrid.vue`: desktop grid and mobile rendering contract.
- `study-hub/frontend/src/views/Home.vue`: explicit coordinates, edit handles and drag integration.
- `study-hub/frontend/tests/home-layout-persistence.mjs`, `home-responsive.mjs`: browser acceptance checks.
- `study-hub/frontend/docs/study-ui/README.md`: public layout behavior and accessibility documentation.

## Task 1: Prove and implement layout engine behavior

- [ ] Add failing unit tests for v1 migration, `(y,x,order)` reading order, illegal coordinate recovery, same-column collision, row-major fallback, appended rows, and hidden-widget reinsertion.
- [ ] Run `npm run test:unit -- src/design-system/layout/dashboardLayout.test.js`; confirm each new behavior fails because the API is absent.
- [ ] Implement `getWidgetSpan`, `sortByReadingOrder`, `normalizeV2Layout`, `placeWidget`, `reinsertWidget`, and `layoutStyle` as pure functions.
- [ ] Re-run the focused test file until green; then run the existing layout and registry tests.

## Task 2: Migrate persistence and draft mutations

- [ ] Add failing composable tests that load a v1 payload from the existing storage key, save v2 at that same key, restore a hidden widget to a deterministic location, and undo a placement.
- [ ] Implement v2 normalization in the registry and draft APIs `move`, `reinsert`, `undo`; retain `hide`, `show`, `save`, `cancelEdit`, and `restoreDefault`.
- [ ] Run the focused composable tests, then the home composable suite.

## Task 3: Add pointer drag adapter

- [ ] Add failing tests for thresholded pointer movement, non-handle click protection, conversion of pointer coordinates to bounded grid targets, and pointer-cancel cleanup.
- [ ] Implement `useGridDrag` without HTML5 drag-and-drop or a grid framework dependency.
- [ ] Run focused tests and verify no document listeners remain after cancel or unmount.

## Task 4: Render explicit desktop placement

- [ ] Add component/browser tests that require `grid-column-start` and `grid-row-start` from saved v2 coordinates, prohibit overlap after a drag, and preserve default Figma geometry before editing.
- [ ] Replace implicit `grid-auto-flow: row dense` placement in `Home.vue` with `layoutStyle(widget)` output and add edit-only drag handles.
- [ ] Keep existing card events and any available FLIP transition optional: layout correctness must not depend on animation.
- [ ] Run unit tests, home persistence browser test, visual overlay test and motion test.

## Task 5: Deliver narrow-screen behavior

- [ ] Add failing browser checks at 390×844 and 942×638 for a single main flow, no horizontal overflow, automatic card height, and all visible card content within bounds.
- [ ] Make `BentoDashboardGrid` use a desktop eight-column explicit grid and a mobile one-column grid; mobile edit operations use the accessible editor list instead of two-dimensional dragging.
- [ ] Add targeted narrow-width CSS adjustments for any widget that overflows (heatmap, calendar, creation entry and workflow are inspected first).
- [ ] Run responsive Playwright checks and capture screenshots.

## Task 6: Document, validate and hand off

- [ ] Update Study UI documentation with storage migration, keyboard fallback, drag-handle behavior, and responsive rules.
- [ ] Run `npm run test:unit`, `npm run build`, `npm run build:storybook`, and all `home-*.mjs` browser checks against the running dashboard.
- [ ] Add a taskboard comment with files, verification, risks and result; move `STUDYHUB-7` to `in_review` only after all checks pass.

## Review checklist

- No persisted width/height bypasses `SIZE_RULES`.
- No `grid-auto-flow: dense` remains on the editable homepage grid.
- No Pointer Events listener leaks or ordinary card clicks converted into drags.
- Default layout still matches the Figma 8×4 geometry.
- Existing uncommitted homepage work is preserved or deliberately integrated after diff review; no broad reformatting.
