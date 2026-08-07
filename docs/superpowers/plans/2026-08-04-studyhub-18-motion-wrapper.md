# Study-Hub Phase 1B MotionWrapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real `MotionWrapper` based on `motion-v` for the approved Phase 1B entrance, hover, and press motion while preserving all homepage widget props and events.

**Architecture:** `MotionWrapper` is the only motion-v consumer exposed by the design system. It renders one `motion.div`, forwards ordinary attributes and slot content, resolves timing and gesture props from the user reduced-motion preference, and marks the final state for tests. Existing GSAP Flip continues to own dashboard layout changes; Vue `Transition` continues to own modal, drawer, and card-state transitions.

**Tech Stack:** Vue 3.5, motion-v 2.3.0, @vueuse/core 14.4.0, Vitest, Storybook 8.6, existing GSAP integration.

---

### Task 1: Install and verify the approved motion dependencies

**Files:**
- Modify: `study-hub/frontend/package.json`
- Modify: `study-hub/frontend/package-lock.json`

- [x] **Step 1: Install the pinned dependencies**

Run `npm install motion-v@2.3.0 @vueuse/core@14.4.0` in `study-hub/frontend`.

- [x] **Step 2: Verify package metadata and dependency tree**

Run `npm ls motion-v @vueuse/core --depth=0` and confirm both versions are present without peer-dependency errors.

### Task 2: Lock the MotionWrapper contract with failing tests

**Files:**
- Create: `study-hub/frontend/src/design-system/patterns/MotionWrapper.test.js`
- Create: `study-hub/frontend/src/design-system/patterns/MotionWrapper.vue`

- [x] **Step 1: Write the object-prop and attribute forwarding test**

Mount `MotionWrapper` with `class`, `data-module-id`, `whileHover: { y: -2 }`, and `whilePress: { scale: 0.98 }`; assert the real rendered element has the ordinary attributes and the component props retain the objects.

- [x] **Step 2: Write the reduced-motion final-state test**

Mount with `reducedMotion: 'always'`; assert `data-motion-state="final"`, no hover/press motion is passed to the rendered motion element, and the slot content remains present.

- [x] **Step 3: Write the media-query change test**

Provide a controllable `matchMedia` object whose `matches` value changes and whose `change` listener can be invoked; assert the wrapper changes from `animated` to `final` and back without remounting.

- [x] **Step 4: Run the focused test and verify the expected RED failure**

Run `npm run test:unit -- src/design-system/patterns/MotionWrapper.test.js`. The test must fail because the component does not yet exist or lacks the requested contract, not because of a test typo.

### Task 3: Implement the minimal MotionWrapper

**Files:**
- Modify: `study-hub/frontend/src/design-system/patterns/MotionWrapper.vue`

- [x] **Step 1: Implement the user reduced-motion state**

Use `window.matchMedia('(prefers-reduced-motion: reduce)')`, read the initial `matches` value, subscribe to `change`, remove the listener on unmount, and resolve `always` or `user` to the final state.

- [x] **Step 2: Implement the single motion-v render target**

Use `motion.div` with `v-bind="$attrs"`, object-valued `:while-hover` and `:while-press`, `:initial`, `:animate`, `:exit`, and a transition derived from `timing` and `delay`; pass `false` for initial and gestures when reduced.

- [x] **Step 3: Run the focused tests and verify GREEN**

Run `npm run test:unit -- src/design-system/patterns/MotionWrapper.test.js`; all wrapper tests must pass before touching the homepage.

### Task 4: Add design-system export and Storybook coverage

**Files:**
- Modify: `study-hub/frontend/src/design-system/index.js`
- Create: `study-hub/frontend/src/design-system/patterns/MotionWrapper.stories.js`
- Modify: `study-hub/frontend/docs/study-ui/component-status.md`

- [x] **Step 1: Export the wrapper and register its status**

Export `MotionWrapper` from `@study-ui` and add its Story, test, accessibility, and import row to the component status document.

- [x] **Step 2: Add default and reduced Storybook stories**

Create one default story with object-valued `whileHover` and `whilePress`, plus one reduced story using `reducedMotion: 'always'`; keep the decorator/user strategy aligned with the component default.

- [x] **Step 3: Build Storybook**

Run `npm run build:storybook` and confirm both MotionWrapper story chunks are emitted.

### Task 5: Integrate the wrapper into the homepage without cutting widget contracts

**Files:**
- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `study-hub/frontend/src/views/Home.test.js`

- [x] **Step 1: Add a failing homepage contract assertion**

Assert the nine widget components remain mounted through `MotionWrapper` and that representative calendar, queue, knowledge, creation, and workflow events still reach their existing handlers.

- [x] **Step 2: Wrap each widget with MotionWrapper**

Move the `home-dashboard-grid__item`, module id, Flip id, size style, and per-index delay to `MotionWrapper`; use `:while-hover="{ y: -2 }"` and `:while-press="{ scale: 0.98 }"`; keep the nested component's exact `v-bind="propsFor(widget.id)"` and `v-on="listenersFor(widget.id)"`.

- [x] **Step 3: Run the homepage tests and verify GREEN**

Run `npm run test:unit -- src/views/Home.test.js src/design-system/patterns/MotionWrapper.test.js`; all existing API and event assertions must pass.

### Task 6: Complete verification and handoff

**Files:**
- Modify: `study-hub/frontend/tests/animation-bundle-budget.mjs` only if the existing budget report needs a Phase 1B label; otherwise leave it unchanged.
- Modify: `STUDYHUB-18` taskboard comments/status through `taskctl`.

- [x] **Step 1: Run focused and full checks**

Run `npm run test:unit`, `npm run build`, `npm run build:storybook`, `npm run test:animation-budget`, and `npm run test:home-motion`.

- [x] **Step 2: Record actual bundle impact**

Use the production output to record the MotionWrapper dependency increment and compare it with the existing animation budget; do not report registry estimates as build measurements.

- [x] **Step 3: Check changed files**

Run `git diff --check` on the Phase 1B files and verify no unrelated files were modified. Do not commit or stage the shared dirty worktree.

- [x] **Step 4: Add the implementation and verification comment**

Record files, passing commands, bundle result, known warnings, and remaining risk on `STUDYHUB-18`, then move it to `in_review` with the latest issue version. Leave completion to explicit user acceptance.
