# STUDYHUB-11 Task Count Regression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore correct task totals in the Today Focus card while retaining category-card counts and mapping each task's `category_id` for category-card grouping.

**Architecture:** `TodayFocusWidget` owns display-count selection. A fallback "all tasks" card uses the totals supplied by `Home.vue`; explicit category cards calculate their own counts from their assigned tasks. As part of STUDYHUB-11, the dashboard data mapper preserves each task's `category_id` and supports an optional result limit so `Home.vue` can keep five visible tasks while building category cards from the complete selected-day mapping.

**Tech Stack:** Vue 3, Vitest, Vite.

---

### Task 1: Repair Today Focus count selection

**Files:**
- Modify: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.test.js`
- Modify: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue`
- Modify: `study-hub/frontend/src/composables/home/useHomeDashboardData.js`
- Modify: `study-hub/frontend/src/composables/home/useHomeDashboardData.test.js`
- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `docs/superpowers/plans/2026-08-08-studyhub-11-count-regression.md`

- [x] **Step 1: Add an explicit category-count regression test**

```js
it('uses the active category task counts when category cards are supplied', () => {
  const wrapper = mount(TodayFocusWidget, {
    props: {
      totalTaskCount: 8,
      completedTaskCount: 3,
      categories: [{ id: 'work', name: '工作', tasks: [{ id: 'a', status: 'done' }, { id: 'b', status: 'pending' }] }],
    },
    global: { stubs: { RouterLink: true } },
  })
  expect(wrapper.findAllComponents(AnimatedNumber).map((component) => component.props('value'))).toEqual([1, 2])
})
```

- [x] **Step 2: Run the widget test to verify the existing fallback failure**

Run: `npm run test:unit -- src/design-system/widgets/TodayFocusWidget.test.js`

Expected: the existing fallback test fails with received `[0, 0]` rather than `[3, 8]`; the explicit-category test passes because category counts already render from category tasks.

- [x] **Step 3: Implement the minimum fallback-aware count helpers**

```js
function completedFor(category) {
  return category.id === 'all' ? completedCount.value : category.tasks.filter((task) => task.status === 'done').length
}
function totalFor(category) {
  return category.id === 'all' ? totalCount.value : category.tasks.length
}
```

Use `totalFor(category)` for the second `AnimatedNumber` in the task-card header. Do not change task rotation, drag interaction, routing, or category-card layout.

The mapper keeps its default five-task limit for `taskItems`; add an optional `limit` argument so `mapTodayTasks(..., Infinity)` returns every selected-day task. `Home.vue` must use that complete mapping only for `todayTaskCategories`, leaving the visible `taskItems` list capped at five.

- [x] **Step 4: Run the focused tests**

Run: `npm run test:unit -- src/design-system/widgets/TodayFocusWidget.test.js src/design-system/widgets/DashboardCompositeWidgets.test.js src/composables/home/useHomeDashboardData.test.js src/views/Home.test.js src/views/DDL.test.js`

Expected: all listed tests pass.

- [x] **Step 5: Validate the task-owned mapping and full frontend gate**

Run: `npm run test:unit && npm run build && git diff --check`

Expected: all frontend tests pass, production build exits 0, and the task diff has no whitespace errors. Confirm `mapTodayTasks` preserves an input task's `category_id` in `useHomeDashboardData.test.js`; do not add unrelated files.

Current evidence (2026-08-08): the focused command passes with 5 files and 21 tests; the Home integration regression passes independently with 1 test (6 skipped by the name filter), confirming six category tasks and five visible tasks. The full frontend gate passes: `npm run test:unit` reports 73 files and 178 tests passed; `npm run build` exits 0 with only existing large-chunk warnings; `git diff --check` passes.

- [x] **Step 6: Commit only STUDYHUB-11 files**

Run: `git add study-hub/frontend/src/composables/home/useHomeDashboardData.js study-hub/frontend/src/composables/home/useHomeDashboardData.test.js study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue study-hub/frontend/src/design-system/widgets/TodayFocusWidget.test.js study-hub/frontend/src/views/Home.vue docs/superpowers/plans/2026-08-08-studyhub-11-count-regression.md && git commit -m "fix(ddl): restore today task card counts"`

Actual: commit `e168f0c` (`fix(ddl): restore today task card counts`) contains only the listed STUDYHUB-11 files and plan; no unrelated root changes were staged.
