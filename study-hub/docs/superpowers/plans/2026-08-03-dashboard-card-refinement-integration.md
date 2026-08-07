# Dashboard Card Refinement Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved Figma-faithful V2 dashboard shell and unified card interior rules to the real Study Hub homepage without changing its data flows or module editing behavior.

**Architecture:** `WorkbenchFrame` owns one fixed 1440×980 design stage and scales it uniformly to the viewport with `ResizeObserver`. `BentoDashboardGrid` remains an 8×4 logical grid with fixed reference geometry. `DashboardModuleCard` owns the single 16px content inset, while individual widgets own only their internal layout.

**Tech Stack:** Vue 3, scoped CSS, Vitest, Node assertions, Playwright, Vite.

---

### Task 1: Lock the responsive and card contracts with failing tests

**Files:**
- Modify: `study-hub/frontend/src/design-system/patterns/FaithfulDashboardPatterns.test.js`
- Create: `study-hub/frontend/tests/home-card-contract.mjs`
- Modify: `study-hub/frontend/tests/home-responsive.mjs`

- [ ] **Step 1: Add a failing public card-inset assertion**

Mount `DashboardModuleCard` in content state and assert that its slot is wrapped by `.dashboard-module-card__content[data-card-inset="16"]`.

- [ ] **Step 2: Add a failing static widget contract**

Read the nine widget source files and assert that none contains `@container`. Read `DashboardModuleCard.vue` and assert that the shared content class contains `padding: 16px`.

- [ ] **Step 3: Replace width-fill assertions with uniform-stage assertions**

For each existing PC viewport, measure `[data-dashboard-stage]`. Compute `scale = Math.min(width / 1440, height / 980)` and assert the rendered stage is centered with width `1440 * scale` and height `980 * scale`. Keep the 1440×980 Figma anchor assertions.

- [ ] **Step 4: Run the focused tests and confirm RED**

Run:

```powershell
npm run test:unit -- src/design-system/patterns/FaithfulDashboardPatterns.test.js
node tests/home-card-contract.mjs
```

Expected: failures because the stage wrapper, public 16px content wrapper, and removal of compact container rules are not implemented yet.

### Task 2: Implement the proportional page stage

**Files:**
- Modify: `study-hub/frontend/src/design-system/patterns/WorkbenchFrame.vue`
- Modify: `study-hub/frontend/src/design-system/patterns/CapsuleNavigation.vue`
- Modify: `study-hub/frontend/src/design-system/patterns/GreetingBar.vue`
- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `study-hub/frontend/src/design-system/patterns/BentoDashboardGrid.vue`

- [ ] **Step 1: Add the viewport and 1440×980 stage**

Wrap the existing frame in `.workbench-viewport`, expose `data-dashboard-stage`, and set the stage transform from a scale computed by `Math.min(viewportWidth / 1440, viewportHeight / 980)`.

- [ ] **Step 2: Fix the reference geometry**

Use fixed reference values: navigation `1320×72` at `(60,33)`, main `1356px` wide at `x=42`, greeting at `y=155`, grid `1368×656` at `(36,244)`, and footer ending at `y=980`.

- [ ] **Step 3: Remove viewport-dependent compact navigation and greeting styles**

Replace viewport clamps and media queries with the Figma reference dimensions because the entire stage now scales as one unit.

- [ ] **Step 4: Keep the grid modular**

Retain `grid-auto-flow: row dense`, widget span variables, saved visibility, and saved order. Use fixed four reference rows and the existing 14.31px gap.

- [ ] **Step 5: Run the frame unit tests**

Run:

```powershell
npm run test:unit -- src/design-system/patterns/FaithfulDashboardPatterns.test.js src/design-system/patterns/BentoDashboardGrid.test.js
```

Expected: PASS.

### Task 3: Move the unified inset into the card shell

**Files:**
- Modify: `study-hub/frontend/src/design-system/patterns/DashboardModuleCard.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/AutomationQueueWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/KnowledgeWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/DailyMemoryWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/QuickCommandWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CreationWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/WorkflowWidget.vue`

- [ ] **Step 1: Add the shared content wrapper**

Wrap the content slot in `.dashboard-module-card__content`, set `height: 100%`, `box-sizing: border-box`, and `padding: 16px`, and expose `data-card-inset="16"`.

- [ ] **Step 2: Convert automation queue from absolute percentages to flow layout**

Keep the three Figma rows, top breathing room, queue link, input surface, and primary action. Use a seven-row grid and preserve retry and open events.

- [ ] **Step 3: Normalize knowledge actions**

Use equal-height rows and a fixed action lane. Keep Copy visible; reveal Delete only for an error row on hover/focus without changing the row width.

- [ ] **Step 4: Center memory and balance commands**

Keep the cover/title identity and two equal command actions, removing all container-query branches.

- [ ] **Step 5: Tighten creation and workflow groups**

Keep their Figma content and interactions while aligning titles, tabs/steps, content rows, thumbnails, and input surfaces to the shared inset.

- [ ] **Step 6: Run widget unit and static contract tests**

Run:

```powershell
npm run test:unit -- src/design-system/widgets/AutomationQueueWidget.test.js src/design-system/widgets/KnowledgeWidget.test.js src/design-system/widgets/CompactWidgets.test.js src/design-system/widgets/CreationWidget.test.js src/design-system/widgets/WorkflowWidget.test.js
node tests/home-card-contract.mjs
```

Expected: PASS.

### Task 4: Adapt the three primary widgets to the shared shell

**Files:**
- Modify: `study-hub/frontend/src/design-system/widgets/WorkHeatmapWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CalendarAgendaWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue`

- [ ] **Step 1: Remove local outer padding and compact branches**

Let the shared card wrapper provide the 16px inset. Preserve the existing Figma colors, timeline, calendar panel, heat cells, and stacked task card.

- [ ] **Step 2: Recalculate internal fixed rows against the reference card sizes**

Keep every title, label, and control within its content box at 677×321, 331×321, and 331×489 reference sizes.

- [ ] **Step 3: Run primary widget tests**

Run:

```powershell
npm run test:unit -- src/design-system/widgets/WorkHeatmapWidget.test.js src/design-system/widgets/DashboardCompositeWidgets.test.js
```

Expected: PASS.

### Task 5: Verify the real homepage

**Files:**
- Verify: `study-hub/frontend/src/**`
- Verify: `study-hub/frontend/tests/**`

- [ ] **Step 1: Run all unit tests and build**

Run `npm run test:unit` and `npm run build`. Expected: both exit 0.

- [ ] **Step 2: Start the frontend on the registered dashboard test port**

Use the configured `TEST_PORTS.dashboard` port in the 5180–5189 range; do not allocate a random port.

- [ ] **Step 3: Run geometry, persistence, and overlay tests**

Run `node tests/home-responsive.mjs`, `node tests/home-visual-overlay.mjs`, and `node tests/home-layout-persistence.mjs`. Expected: all exit 0 and screenshots are larger than 10KB.

- [ ] **Step 4: Inspect the generated screenshots**

Compare the 1440×980 screenshot with Figma node `349:96`, then inspect 1366×768, 1920×1080, and 2560×1440 for uniform scaling and coherent letterboxing. Reject any overlap, clipping, stretched card, or inconsistent inset.
