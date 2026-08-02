# Study Hub Faithful Modular Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Study Hub home page so its default PC presentation matches Figma node `349:96` at `1440 x 980`, while preserving real Study Hub operations and enabling constrained add/hide/reorder dashboard modules.

**Architecture:** Keep the existing foundations, primitives, composables, API clients, and route behavior, but replace the old shell/grid/widget assumptions with a Figma-calibrated `WorkbenchFrame`, `CapsuleNavigation`, `GreetingBar`, eight-column `BentoDashboardGrid`, and nine purpose-built widgets. A versioned layout registry owns module identity, legal sizes, visibility, ordering, and local persistence; the page owns data fetching and maps API results into stable widget contracts.

**Tech Stack:** Vue 3 `<script setup>`, CSS custom properties, Vitest + Vue Test Utils, Storybook 8, Playwright, `vuedraggable` 4.

---

### Task 1: Establish the Figma geometry and preserve existing behavior

**Files:**
- Create: `study-hub/frontend/src/design-system/layout/dashboardLayout.js`
- Create: `study-hub/frontend/src/design-system/layout/dashboardLayout.test.js`
- Modify: `study-hub/frontend/tests/home-responsive.mjs`
- Create: `study-hub/frontend/tests/home-behavior.mjs`
- Reference: `study-hub/docs/superpowers/specs/2026-08-03-study-hub-home-fidelity-modular-dashboard-design.md`

- [ ] **Step 1: Write the failing geometry and behavior tests**

```js
import { describe, expect, it } from 'vitest'
import { DEFAULT_DASHBOARD_LAYOUT, GRID_COLUMNS, GRID_ROW_HEIGHT, GRID_GAP, getWidgetGeometry } from './dashboardLayout.js'

describe('Figma dashboard geometry', () => {
  it('maps the 1440px reference to eight columns and the nine approved sizes', () => {
    expect(GRID_COLUMNS).toBe(8)
    expect(GRID_ROW_HEIGHT).toBeCloseTo(153.36, 1)
    expect(GRID_GAP).toBeCloseTo(14.31, 1)
    expect(DEFAULT_DASHBOARD_LAYOUT.widgets.map((widget) => widget.id)).toEqual([
      'work-heatmap', 'calendar-agenda', 'today-focus', 'automation-queue',
      'knowledge', 'daily-memory', 'quick-command', 'creation-entry', 'quick-workflow',
    ])
    expect(getWidgetGeometry('work-heatmap', 1440).width).toBeCloseTo(677, 0)
    expect(getWidgetGeometry('today-focus', 1440).height).toBeCloseTo(484, 0)
  })
})
```

```js
import { chromium } from 'playwright'
import assert from 'node:assert/strict'

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } })
await page.goto(process.env.STUDY_UI_ORIGIN || 'http://127.0.0.1:5173/', { waitUntil: 'networkidle' })
assert.equal(await page.locator('[data-figma-node]').count(), 9)
assert.equal(await page.getByRole('heading', { level: 1, name: '学习中枢' }).count(), 1)
assert.equal(await page.getByRole('navigation', { name: '主导航' }).count(), 1)
await browser.close()
```

- [ ] **Step 2: Run the new tests and confirm the intended failure**

Run: `npm run test:unit -- src/design-system/layout/dashboardLayout.test.js`

Expected: FAIL because the geometry module and nine-widget page contract do not exist yet.

- [ ] **Step 3: Implement the minimal geometry model**

```js
export const GRID_COLUMNS = 8
export const GRID_ROW_HEIGHT = 153.36
export const GRID_GAP = 14.31
export const DEFAULT_DASHBOARD_LAYOUT = {
  version: 1,
  widgets: [
    { id: 'work-heatmap', visible: true, order: 0, size: '4x2' },
    { id: 'calendar-agenda', visible: true, order: 1, size: '2x2' },
    { id: 'today-focus', visible: true, order: 2, size: '2x3' },
    { id: 'automation-queue', visible: true, order: 3, size: '2x2' },
    { id: 'knowledge', visible: true, order: 4, size: '2x1' },
    { id: 'daily-memory', visible: true, order: 5, size: '1x1' },
    { id: 'quick-command', visible: true, order: 6, size: '1x1' },
    { id: 'creation-entry', visible: true, order: 7, size: '2x2' },
    { id: 'quick-workflow', visible: true, order: 8, size: '2x1' },
  ],
}
export const SIZE_RULES = {
  'work-heatmap': ['4x2'], 'calendar-agenda': ['2x2'], 'today-focus': ['2x3'],
  'automation-queue': ['2x2'], knowledge: ['2x1'], 'daily-memory': ['1x1'],
  'quick-command': ['1x1'], 'creation-entry': ['2x2'], 'quick-workflow': ['2x1'],
}
export function getWidgetGeometry(id, viewportWidth) {
  const size = DEFAULT_DASHBOARD_LAYOUT.widgets.find((widget) => widget.id === id)?.size || '1x1'
  const [columns, rows] = size.split('x').map(Number)
  const width = Math.min(1356, viewportWidth - 84)
  const cell = (width - GRID_GAP * 7) / GRID_COLUMNS
  return { width: cell * columns + GRID_GAP * (columns - 1), height: GRID_ROW_HEIGHT * rows + GRID_GAP * (rows - 1) }
}
```

- [ ] **Step 4: Run the focused tests and the existing composable suite**

Run: `npm run test:unit -- src/design-system/layout/dashboardLayout.test.js src/composables/home`

Expected: geometry tests pass; existing composable tests remain green.

- [ ] **Step 5: Commit the baseline contract**

```bash
git add study-hub/frontend/src/design-system/layout/dashboardLayout.js study-hub/frontend/src/design-system/layout/dashboardLayout.test.js study-hub/frontend/tests/home-behavior.mjs study-hub/frontend/tests/home-responsive.mjs
git commit -m "test(ui): define faithful dashboard geometry and behavior baseline"
```

### Task 2: Calibrate foundations and shared primitives

**Files:**
- Modify: `study-hub/frontend/src/design-system/foundations/tokens.css`
- Modify: `study-hub/frontend/src/design-system/foundations/tokens.js`
- Modify: `study-hub/frontend/src/design-system/components/general/UiButton.vue`
- Modify: `study-hub/frontend/src/design-system/components/general/UiIconButton.vue`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiBadge.vue`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiProgress.vue`
- Modify: `study-hub/frontend/src/design-system/foundations/tokens.test.js`
- Modify: `study-hub/frontend/src/design-system/components/general/UiButton.test.js`

- [ ] **Step 1: Add failing assertions for Figma token values and primitive states**

```js
it('exposes the Figma surface, accent, spacing, and widget radius tokens', () => {
  expect(semanticTokens.color.surface).toBe('#1b1d1a')
  expect(semanticTokens.color.action).toBe('#d7ff63')
  expect(semanticTokens.radius.widget).toBe('22px')
})
it('keeps button width and focus state stable across variants', () => {
  const wrapper = mount(UiButton, { props: { variant: 'primary', size: 'md' }, slots: { default: '开始' } })
  expect(wrapper.attributes('data-variant')).toBe('primary')
  expect(wrapper.attributes('data-size')).toBe('md')
})
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `npm run test:unit -- src/design-system/foundations/tokens.test.js src/design-system/components/general/UiButton.test.js`

Expected: FAIL on missing semantic aliases or missing state attributes.

- [ ] **Step 3: Implement only the token aliases and primitive state attributes needed by the dashboard**

Map the existing raw values to semantic `canvas`, `shell`, `surface`, `surfaceRaised`, `textStrong`, `text`, `textMuted`, `action`, `purple`, `orange`, `peach`, `cream`, `border`, `borderStrong`, `widgetRadius`, `widgetShadow`, `focusRing`, and add `data-variant`/`data-size` to button primitives without changing existing event behavior.

- [ ] **Step 4: Run all primitive tests**

Run: `npm run test:unit -- src/design-system`

Expected: all foundation, general, data-display, feedback, and pattern tests pass.

- [ ] **Step 5: Commit the calibrated primitive layer**

```bash
git add study-hub/frontend/src/design-system/foundations study-hub/frontend/src/design-system/components
git commit -m "fix(ui): calibrate study dashboard design tokens and primitives"
```

### Task 3: Rebuild the desktop shell, navigation, greeting, and eight-column grid

**Files:**
- Create: `study-hub/frontend/src/design-system/patterns/WorkbenchFrame.vue`
- Create: `study-hub/frontend/src/design-system/patterns/CapsuleNavigation.vue`
- Create: `study-hub/frontend/src/design-system/patterns/GreetingBar.vue`
- Create: `study-hub/frontend/src/design-system/patterns/BentoDashboardGrid.vue`
- Create: `study-hub/frontend/src/design-system/patterns/BentoDashboardGrid.test.js`
- Modify: `study-hub/frontend/src/design-system/patterns/UiAppShell.vue`
- Modify: `study-hub/frontend/src/design-system/patterns/UiDashboardGrid.vue`
- Modify: `study-hub/frontend/src/design-system/patterns/UiDashboardItem.vue`
- Modify: `study-hub/frontend/src/design-system/index.js`
- Modify: `study-hub/frontend/src/App.vue`
- Modify: `study-hub/frontend/src/components/NavBar.vue`

- [ ] **Step 1: Write failing tests for the 1440 reference anchors**

```js
it('renders an anchored 1320px capsule nav and an eight-column bento grid', async () => {
  const wrapper = mount(BentoDashboardGrid, { slots: { default: '<div data-span="4x2" />' } })
  expect(wrapper.classes()).toContain('bento-dashboard-grid')
  expect(wrapper.attributes('data-columns')).toBe('8')
})
```

```js
const anchors = {
  nav: { x: 60, y: 33, width: 1320, height: 72 },
  greeting: { x: 42, y: 155, width: 1356, height: 69 },
  grid: { x: 36, y: 244 },
}
for (const [name, expected] of Object.entries(anchors)) {
  const actual = await page.locator(`[data-visual-anchor="${name}"]`).boundingBox()
  assert.ok(actual, `${name} anchor must exist`)
  for (const key of Object.keys(expected)) {
    assert.ok(Math.abs(actual[key] - expected[key]) <= 4, `${name}.${key}: ${actual[key]} !== ${expected[key]}`)
  }
}
```

- [ ] **Step 2: Run tests and confirm the old shell/grid fails the anchors**

Run: `npm run test:unit -- src/design-system/patterns/BentoDashboardGrid.test.js; node tests/home-responsive.mjs`

Expected: FAIL because the current shell is sticky full-width and the current grid has four columns.

- [ ] **Step 3: Implement the constrained desktop shell and grid**

`WorkbenchFrame` must center a `min(1356px, calc(100vw - 84px))` workspace on the dark canvas, reserve the `60px/33px/1320px/72px` navigation capsule, and keep the greeting and grid in normal flow. `BentoDashboardGrid` must use `grid-template-columns: repeat(8, minmax(0, 1fr))`, `grid-auto-rows: 153.36px`, and `14.31px` gaps at PC widths. `UiDashboardItem` must only accept the nine registered sizes and set `grid-column`/`grid-row` spans without whole-page scaling.

- [ ] **Step 4: Run geometry tests at 1440, 1366, 1920, and 2560 widths**

Run: `npm run test:unit -- src/design-system/patterns/BentoDashboardGrid.test.js; node tests/home-responsive.mjs`

Expected: the reference anchors are within 4px at `1440 x 980`, and all three 16:9 widths have no horizontal overflow.

- [ ] **Step 5: Commit the shell and grid**

```bash
git add study-hub/frontend/src/design-system/patterns study-hub/frontend/src/design-system/index.js study-hub/frontend/src/App.vue study-hub/frontend/src/components/NavBar.vue
git commit -m "feat(ui): rebuild faithful desktop workbench shell and bento grid"
```

### Task 4: Build the nine Figma-specific widgets

**Files:**
- Create: `study-hub/frontend/src/design-system/widgets/WorkHeatmapWidget.vue`
- Create: `study-hub/frontend/src/design-system/widgets/CalendarAgendaWidget.vue`
- Create: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue`
- Create: `study-hub/frontend/src/design-system/widgets/DailyMemoryWidget.vue`
- Create: `study-hub/frontend/src/design-system/widgets/QuickCommandWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/AutomationQueueWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/KnowledgeWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CreationWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/WorkflowWidget.vue`
- Modify: `study-hub/frontend/src/design-system/patterns/UiWidgetFrame.vue`
- Create/modify: matching `*.test.js` and `*.stories.js` files for all nine widgets
- Modify: `study-hub/frontend/src/design-system/index.js`

- [ ] **Step 1: Write failing tests for each widget's fixed-size structure and states**

```js
it('keeps the heatmap node and card metadata stable while data changes', () => {
  const wrapper = mount(WorkHeatmapWidget, { props: { cells: Array(28).fill(0).map((_, index) => ({ index, value: index % 5 })) } })
  expect(wrapper.find('[data-figma-node="349:169"]').exists()).toBe(true)
  expect(wrapper.findAll('[data-heatmap-cell]').length).toBe(28)
})
```

```js
const widgetContracts = [
  [CalendarAgendaWidget, '349:516', { days: [{ date: '2026-08-03', label: '3', selected: true }], agenda: [] }],
  [TodayFocusWidget, '349:405', { tasks: [{ id: 't1', title: '真实任务', status: 'running', progress: 35 }] }],
  [AutomationQueueWidget, '349:369', { items: [{ id: 'q1', title: '解析', status: 'running', progress: 55 }] }],
  [KnowledgeWidget, '349:471', { items: [{ id: 1, title: '真实文档', meta: '今天', status: 'ready' }] }],
  [DailyMemoryWidget, '349:484', { entry: { title: '今日手账', subtitle: 'Memories' } }],
  [QuickCommandWidget, '349:510', { commands: [{ id: 'c1', title: '打开知识库' }] }],
  [CreationWidget, '349:493', { items: [{ id: 'p1', title: '继续创作', kind: 'article' }] }],
  [WorkflowWidget, '349:459', { steps: [{ id: 's1', label: '收集', status: 'done' }] }],
]
for (const [component, nodeId, props] of widgetContracts) {
  const wrapper = mount(component, { props })
  expect(wrapper.find(`[data-figma-node="${nodeId}"]`).exists()).toBe(true)
}
```

For every widget component, add explicit cases with `loading: true`, `error: '加载失败'`, an empty collection, and an input collection larger than its visible capacity; assert the root node remains mounted and the rendered item count is capped.

- [ ] **Step 2: Run widget tests and confirm failure**

Run: `npm run test:unit -- src/design-system/widgets`

Expected: FAIL because four widgets do not exist and the six old widgets have the wrong internal layouts.

- [ ] **Step 3: Implement the widget internals from Figma structure, not generic card templates**

Use `UiWidgetFrame` only for shared border/radius/state semantics. Build each widget's distinctive internals: heatmap cells and legend; calendar date strip and agenda panel; layered Today Focus task timeline; queue rows; knowledge list; diary cover stack; command tile; creation entry; and workflow row. Clamp visible rows to the specified card capacity and emit existing operation events.

- [ ] **Step 4: Run all widget tests and Storybook stories**

Run: `npm run test:unit -- src/design-system/widgets; npm run build:storybook`

Expected: all nine widgets pass default/loading/empty/error/overflow tests and Storybook builds successfully.

- [ ] **Step 5: Commit the widget layer**

```bash
git add study-hub/frontend/src/design-system/widgets study-hub/frontend/src/design-system/patterns/UiWidgetFrame.vue study-hub/frontend/src/design-system/index.js
git commit -m "feat(ui): add Figma-faithful dashboard widgets"
```

### Task 5: Map real Study Hub data and preserve home interactions

**Files:**
- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `study-hub/frontend/src/composables/home/useAutomationQueue.js`
- Modify: `study-hub/frontend/src/composables/home/useKnowledgeDocuments.js`
- Modify: `study-hub/frontend/src/composables/home/useDailyReview.js`
- Modify: `study-hub/frontend/src/composables/home/useHomeSearch.js`
- Create: `study-hub/frontend/src/composables/home/useHomeDashboardData.js`
- Create: `study-hub/frontend/src/composables/home/useHomeDashboardData.test.js`
- Modify: `study-hub/frontend/tests/home-behavior.mjs`

- [ ] **Step 1: Write failing data-mapping and interaction tests**

```js
it('maps existing API results to stable widget contracts without fake examples', () => {
  const { mapDocuments, mapQueue, mapCommands } = createHomeDashboardData()
  expect(mapDocuments([{ id: 3, title: '真实文档', created_at: '2026-08-03T10:00:00' }])[0]).toMatchObject({ id: 3, title: '真实文档' })
  expect(mapQueue([{ task_id: 'q1', title: '解析', status: 'running', progress: 55 }])[0]).toMatchObject({ id: 'q1', progress: 55 })
  expect(mapCommands([{ name: '打开知识库', url: '/kb' }])[0].title).toBe('打开知识库')
})
```

Playwright must click a knowledge item, submit an automation link, retry a failed queue task, open the review dialog, trigger search, open the calendar route, and activate creation/workflow entries.

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `npm run test:unit -- src/composables/home/useHomeDashboardData.test.js; node tests/home-behavior.mjs`

Expected: FAIL because the new mapping composable and nine-widget Home composition do not exist.

- [ ] **Step 3: Implement stable page-owned mapping and preserve the existing user change**

Move only data normalization into `useHomeDashboardData`; keep API calls and operation callbacks in Home. Preserve the current `copyDocContent()` implementation exactly as `return copyDocument(activeDocument.value)`. Use real current date/time in GreetingBar, real documents/queue/review/launcher data, and route existing operations through their current composables.

- [ ] **Step 4: Run all home and composable tests**

Run: `npm run test:unit -- src/composables/home; node tests/home-behavior.mjs`

Expected: all existing composable tests and new end-to-end behavior checks pass.

- [ ] **Step 5: Commit the real data integration**

```bash
git add study-hub/frontend/src/views/Home.vue study-hub/frontend/src/composables/home
git commit -m "feat(ui): connect faithful dashboard widgets to real home data"
```

### Task 6: Add the module registry, edit mode, and constrained drag ordering

**Files:**
- Create: `study-hub/frontend/src/design-system/layout/dashboardRegistry.js`
- Create: `study-hub/frontend/src/design-system/layout/dashboardRegistry.test.js`
- Create: `study-hub/frontend/src/composables/home/useDashboardLayout.js`
- Create: `study-hub/frontend/src/composables/home/useDashboardLayout.test.js`
- Create: `study-hub/frontend/src/design-system/patterns/DashboardEditor.vue`
- Create: `study-hub/frontend/src/design-system/patterns/DashboardEditor.test.js`
- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `study-hub/frontend/src/design-system/index.js`

- [ ] **Step 1: Write failing tests for registry validation and editor operations**

```js
it('rejects unknown modules and illegal sizes while preserving default order', () => {
  const layout = normalizeDashboardLayout({ version: 999, widgets: [{ id: 'missing', size: '7x7' }] })
  expect(layout).toEqual(DEFAULT_DASHBOARD_LAYOUT)
})
it('supports hide, add, reorder, save, cancel, and restore-default operations', () => {
  const dashboard = useDashboardLayout({ storage: memoryStorage() })
  dashboard.beginEdit(); dashboard.hide('knowledge'); dashboard.reorder('quick-command', 0)
  expect(dashboard.draft.value.widgets.find((item) => item.id === 'knowledge').visible).toBe(false)
  dashboard.cancelEdit(); expect(dashboard.layout.value).toEqual(DEFAULT_DASHBOARD_LAYOUT)
  dashboard.beginEdit(); dashboard.hide('knowledge'); dashboard.save()
  expect(dashboard.layout.value.widgets.find((item) => item.id === 'knowledge').visible).toBe(false)
  dashboard.restoreDefault(); expect(dashboard.layout.value).toEqual(DEFAULT_DASHBOARD_LAYOUT)
})
```

- [ ] **Step 2: Run the tests and confirm failure**

Run: `npm run test:unit -- src/design-system/layout/dashboardRegistry.test.js src/composables/home/useDashboardLayout.test.js src/design-system/patterns/DashboardEditor.test.js`

Expected: FAIL because the registry, storage composable, and editor do not exist.

- [ ] **Step 3: Implement registry, versioned local persistence, and editor UI**

Register each widget with `id`, label, component, default size, legal sizes, and Figma node. `normalizeDashboardLayout` must ignore unknown IDs, reject illegal sizes, and fall back to the full default when version migration cannot produce a valid layout. `useDashboardLayout` must store `{ version, widgets }` under a namespaced key, expose `layout`, `draft`, `isEditing`, `beginEdit`, `hide`, `show`, `reorder`, `save`, `cancel`, and `restoreDefault`. Use `vuedraggable` in `DashboardEditor`; normal mode must not show handles or edit affordances.

- [ ] **Step 4: Wire the top-right menu to edit mode and verify persistence**

Run: `npm run test:unit -- src/design-system/layout src/composables/home/useDashboardLayout.test.js; node tests/home-behavior.mjs`

Expected: entering edit mode exposes add/hide/reorder/save/cancel/restore controls, refreshing keeps a saved layout, and cancel restores the pre-edit layout.

- [ ] **Step 5: Commit dashboard customization**

```bash
git add study-hub/frontend/src/design-system/layout study-hub/frontend/src/composables/home/useDashboardLayout* study-hub/frontend/src/design-system/patterns/DashboardEditor* study-hub/frontend/src/views/Home.vue study-hub/frontend/src/design-system/index.js
git commit -m "feat(ui): add constrained modular dashboard editing and persistence"
```

### Task 7: Rebuild Storybook as a categorized component library

**Files:**
- Create: `study-hub/frontend/src/design-system/README.md`
- Modify: every `*.stories.js` under `study-hub/frontend/src/design-system`
- Create: `study-hub/frontend/src/design-system/patterns/DashboardEditor.stories.js`
- Create: `study-hub/frontend/src/design-system/layout/dashboardRegistry.stories.js`
- Modify: `study-hub/frontend/.storybook/preview.js`
- Modify: `study-hub/frontend/src/design-system/documentation.test.js`

- [ ] **Step 1: Add failing documentation assertions**

```js
it('documents the Ant-style categories and every Figma widget state', async () => {
  const stories = await collectStoryFiles()
  expect(stories.some((file) => file.includes('WorkHeatmapWidget'))).toBe(true)
  expect(stories.some((file) => file.includes('DashboardEditor'))).toBe(true)
  expect(await readme()).toContain('通用')
  expect(await readme()).toContain('Study Hub Widgets')
})
```

- [ ] **Step 2: Run the documentation test and confirm failure**

Run: `npm run test:unit -- src/design-system/documentation.test.js`

Expected: FAIL because the README and nine-widget/editor stories are incomplete.

- [ ] **Step 3: Implement categorized stories and usage documentation**

Organize stories under `通用`, `导航`, `数据录入`, `数据展示`, `反馈`, `布局`, and `Study Hub Widgets`. Each story must show default/loading/empty/error/overflow or legal-size states, list props/events/accessibility notes, and include the Figma node reference. Document design tokens and the module registry without creating a second fake Home page.

- [ ] **Step 4: Build Storybook and run documentation tests**

Run: `npm run test:unit -- src/design-system/documentation.test.js; npm run build:storybook`

Expected: tests pass and Storybook builds with all categories and stories.

- [ ] **Step 5: Commit the library documentation**

```bash
git add study-hub/frontend/src/design-system study-hub/frontend/.storybook/preview.js
git commit -m "docs(ui): present Study Hub library with categorized Storybook stories"
```

### Task 8: Perform visual overlay, PC regression, and production verification

**Files:**
- Modify: `study-hub/frontend/tests/home-responsive.mjs`
- Create: `study-hub/frontend/tests/home-visual-overlay.mjs`
- Create: `study-hub/frontend/tests/home-layout-persistence.mjs`
- Modify: `study-hub/frontend/tests/home-visual-baseline.md`

- [ ] **Step 1: Write failing overlay and persistence checks**

```js
const expected = { nav: { x: 60, y: 33, width: 1320, height: 72 }, greeting: { x: 42, y: 155, width: 1356, height: 69 }, grid: { x: 36, y: 244 } }
for (const [name, anchor] of Object.entries(expected)) {
  const actual = await page.locator(`[data-visual-anchor="${name}"]`).boundingBox()
  assert.ok(actual)
  assert.ok(Math.abs(actual.x - anchor.x) <= 4)
  assert.ok(Math.abs(actual.y - anchor.y) <= 4)
}
```

```js
const nodeIds = ['349:169', '349:516', '349:405', '349:369', '349:471', '349:484', '349:510', '349:493', '349:459']
for (const viewport of [{ width: 1366, height: 768 }, { width: 1920, height: 1080 }, { width: 2560, height: 1440 }]) {
  await page.setViewportSize(viewport)
  await page.reload({ waitUntil: 'networkidle' })
  const metrics = await page.evaluate(() => ({ width: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth }))
  assert.ok(metrics.scrollWidth <= metrics.width, `horizontal overflow at ${viewport.width}`)
  assert.deepEqual(await page.locator('[data-figma-node]').evaluateAll((nodes) => nodes.map((node) => node.dataset.figmaNode)), nodeIds)
}
await page.getByRole('button', { name: '编辑首页' }).click()
await page.getByRole('button', { name: '隐藏知识库' }).click()
await page.getByRole('button', { name: '保存布局' }).click()
await page.reload({ waitUntil: 'networkidle' })
assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 0)
```

- [ ] **Step 2: Run the checks and confirm any remaining visual failures**

Run: `node tests/home-responsive.mjs; node tests/home-visual-overlay.mjs; node tests/home-layout-persistence.mjs`

Expected before final tuning: failures identify exact anchor or module-boundary offsets rather than generic screenshot failures.

- [ ] **Step 3: Tune CSS and widget internals until the overlay passes**

Use Figma screenshot/node geometry as the authority. Adjust only tokens, shell spacing, grid math, and widget internals; do not add whole-page transforms or alter the approved module order/sizes. Keep dynamic dates and real data within fixed card geometry.

- [ ] **Step 4: Run the complete verification suite**

Run: `npm run test:unit; npm run build:storybook; npm run build; node tests/home-responsive.mjs; node tests/home-visual-overlay.mjs; node tests/home-layout-persistence.mjs`

Expected: all unit, Storybook, production build, visual overlay, persistence, and three 16:9 PC checks pass.

- [ ] **Step 5: Commit the verified implementation**

```bash
git add study-hub/frontend/src study-hub/frontend/tests
git commit -m "feat(ui): complete faithful modular Study Hub home dashboard"
```

### Self-review checklist

- [ ] The plan covers all nine Figma node IDs and their exact legal grid sizes.
- [ ] The plan preserves the existing real API operations and `copyDocContent` user change.
- [ ] Every production change starts with a failing test and includes an expected command result.
- [ ] Every implementation instruction names the exact behavior, file, command, and expected result.
- [ ] No task requires mobile visual parity before the approved PC scope.
- [ ] The final verification proves both behavior and visual geometry; passing unit tests alone is insufficient.
