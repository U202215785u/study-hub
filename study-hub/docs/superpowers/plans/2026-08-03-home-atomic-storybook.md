# Home Atomic Storybook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the repeated visual language of the verified Study Hub home dashboard into reusable atomic and molecular components, make the live home use them, and publish the complete system in Storybook without changing home geometry or business behavior.

**Architecture:** Existing semantic tokens remain the visual source of truth. Small public components live under `src/design-system/components`, dashboard composition remains under `patterns`, domain widgets continue to accept serializable props and emit identifiers, and `Home.vue` remains the owner of API calls and side effects. Storybook documents the same public components used by production and includes one static full-dashboard composition for visual review.

**Tech Stack:** Vue 3, scoped CSS, Vitest, Vue Test Utils, Storybook 8, Playwright, Vite.

---

## File Map

**Create**

- `study-hub/frontend/src/design-system/components/general/UiPillButton.vue`
- `study-hub/frontend/src/design-system/components/general/UiPillButton.test.js`
- `study-hub/frontend/src/design-system/components/general/UiPillButton.stories.js`
- `study-hub/frontend/src/design-system/components/data-display/UiCompactHeader.vue`
- `study-hub/frontend/src/design-system/components/data-display/UiCompactHeader.test.js`
- `study-hub/frontend/src/design-system/components/data-display/UiCompactHeader.stories.js`
- `study-hub/frontend/src/design-system/components/data-display/UiInsetSurface.vue`
- `study-hub/frontend/src/design-system/components/data-display/UiInsetSurface.test.js`
- `study-hub/frontend/src/design-system/components/data-display/UiInsetSurface.stories.js`
- `study-hub/frontend/src/design-system/foundations/DesignLanguage.stories.js`
- `study-hub/frontend/src/design-system/examples/HomeDashboardExample.vue`
- `study-hub/frontend/src/design-system/examples/HomeDashboardExample.stories.js`

**Modify**

- `study-hub/frontend/src/design-system/components/general/UiButton.vue`
- `study-hub/frontend/src/design-system/components/general/UiButton.test.js`
- `study-hub/frontend/src/design-system/components/general/UiButton.stories.js`
- `study-hub/frontend/src/design-system/components/data-display/UiBadge.vue`
- `study-hub/frontend/src/design-system/components/data-display/UiBadge.test.js`
- `study-hub/frontend/src/design-system/components/data-display/UiBadge.stories.js`
- `study-hub/frontend/src/design-system/components/data-display/UiProgress.vue`
- `study-hub/frontend/src/design-system/components/data-display/UiProgress.test.js`
- `study-hub/frontend/src/design-system/components/data-display/UiProgress.stories.js`
- `study-hub/frontend/src/design-system/index.js`
- `study-hub/frontend/src/design-system/widgets/*.vue`
- `study-hub/frontend/src/design-system/widgets/*.stories.js`
- `study-hub/frontend/src/design-system/widgets/*.test.js`
- `study-hub/frontend/docs/study-ui/README.md`
- `study-hub/frontend/docs/study-ui/component-status.md`
- `study-hub/frontend/src/design-system/documentation.test.js`
- `study-hub/frontend/tests/home-card-contract.mjs`

## Task 1: Extend the existing atomic controls

**Files:**

- Modify: `study-hub/frontend/src/design-system/components/general/UiButton.test.js`
- Modify: `study-hub/frontend/src/design-system/components/general/UiButton.vue`
- Modify: `study-hub/frontend/src/design-system/components/general/UiButton.stories.js`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiBadge.test.js`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiBadge.vue`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiBadge.stories.js`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiProgress.test.js`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiProgress.vue`
- Modify: `study-hub/frontend/src/design-system/components/data-display/UiProgress.stories.js`

- [ ] **Step 1: Write failing tests for the new public states**

Add these cases to the existing test suites:

```js
it('exposes the xs size and pill shape', () => {
  const wrapper = mount(UiButton, { props: { size: 'xs', shape: 'pill' }, slots: { default: '复制' } })
  expect(wrapper.get('button').attributes('data-size')).toBe('xs')
  expect(wrapper.get('button').attributes('data-shape')).toBe('pill')
})

it('renders a compact badge without dropping its text label', () => {
  const wrapper = mount(UiBadge, { props: { status: 'success', size: 'compact', label: '已完成' } })
  expect(wrapper.get('.ui-badge').attributes('data-size')).toBe('compact')
  expect(wrapper.text()).toContain('已完成')
})

it('exposes compact danger progress semantics', () => {
  const wrapper = mount(UiProgress, { props: { value: 68, size: 'compact', status: 'danger', ariaLabel: '失败进度' } })
  expect(wrapper.get('.ui-progress').attributes()).toMatchObject({ 'data-size': 'compact', 'data-status': 'danger' })
  expect(wrapper.get('[role="progressbar"]').attributes('aria-valuenow')).toBe('68')
})
```

- [ ] **Step 2: Run the atomic tests and verify RED**

Run:

```powershell
npx vitest run src/design-system/components/general/UiButton.test.js src/design-system/components/data-display/UiBadge.test.js src/design-system/components/data-display/UiProgress.test.js
```

Expected: failures because `shape`, `xs`, badge `size`, progress `size`, and progress `status` are not exposed.

- [ ] **Step 3: Implement the minimal atomic APIs**

In `UiButton.vue`, add the attribute and prop:

```vue
<button
  class="ui-button"
  :data-variant="variant"
  :data-size="size"
  :data-shape="shape"
>
```

```js
shape: {
  type: String,
  default: 'default',
  validator: (value) => ['default', 'pill'].includes(value),
},
```

Change the size validator to `['xs', 'sm', 'md', 'lg']` and add:

```css
.ui-button[data-size='xs'] {
  min-height: 24px;
  padding: 0 var(--ui-space-2);
  font-size: 10px;
}

.ui-button[data-shape='pill'] {
  border-radius: 999px;
}
```

In `UiBadge.vue`, expose `:data-size="size"`, add the validated prop, and add compact styling:

```js
size: { type: String, default: 'default', validator: (value) => ['default', 'compact'].includes(value) },
```

```css
.ui-badge[data-size='compact'] {
  min-height: 18px;
  gap: var(--ui-space-1);
  font-size: 10px;
}
.ui-badge[data-size='compact'] .ui-badge__dot { width: 5px; height: 5px; }
```

In `UiProgress.vue`, expose both data attributes, add validated props, and use semantic colors:

```vue
<div class="ui-progress" :data-type="type" :data-size="size" :data-status="status">
```

```js
size: { type: String, default: 'default', validator: (value) => ['default', 'compact'].includes(value) },
status: { type: String, default: 'active', validator: (value) => ['active', 'success', 'warning', 'danger'].includes(value) },
```

```css
.ui-progress[data-size='compact'] { gap: var(--ui-space-1); }
.ui-progress[data-size='compact'] .ui-progress__track { min-height: 5px; }
.ui-progress[data-size='compact'] .ui-progress__fill,
.ui-progress[data-size='compact'] .ui-progress__segment { height: 5px; }
.ui-progress[data-status='success'] .ui-progress__fill,
.ui-progress[data-status='success'] .ui-progress__segment--filled { background: var(--ui-color-success); }
.ui-progress[data-status='warning'] .ui-progress__fill,
.ui-progress[data-status='warning'] .ui-progress__segment--filled { background: var(--ui-color-warning); }
.ui-progress[data-status='danger'] .ui-progress__fill,
.ui-progress[data-status='danger'] .ui-progress__segment--filled { background: var(--ui-color-danger); }
```

- [ ] **Step 4: Run the atomic tests and verify GREEN**

Run the command from Step 2. Expected: all three files pass.

- [ ] **Step 5: Expand Storybook states**

Add `xs` and `pill` controls/stories to `UiButton.stories.js`, `compact` stories to `UiBadge.stories.js`, and compact/status stories to `UiProgress.stories.js`. The concrete story exports are:

```js
export const ExtraSmall = { args: { size: 'xs' }, render: Primary.render }
export const Pill = { args: { size: 'xs', shape: 'pill' }, render: Primary.render }
export const Compact = { args: { size: 'compact' } }
export const CompactDanger = { args: { size: 'compact', status: 'danger', value: 68, label: '' } }
```

## Task 2: Add the reusable dashboard molecules

**Files:**

- Create: `study-hub/frontend/src/design-system/components/general/UiPillButton.vue`
- Create: `study-hub/frontend/src/design-system/components/general/UiPillButton.test.js`
- Create: `study-hub/frontend/src/design-system/components/general/UiPillButton.stories.js`
- Create: `study-hub/frontend/src/design-system/components/data-display/UiCompactHeader.vue`
- Create: `study-hub/frontend/src/design-system/components/data-display/UiCompactHeader.test.js`
- Create: `study-hub/frontend/src/design-system/components/data-display/UiCompactHeader.stories.js`
- Create: `study-hub/frontend/src/design-system/components/data-display/UiInsetSurface.vue`
- Create: `study-hub/frontend/src/design-system/components/data-display/UiInsetSurface.test.js`
- Create: `study-hub/frontend/src/design-system/components/data-display/UiInsetSurface.stories.js`

- [ ] **Step 1: Write failing behavior tests**

```js
// UiPillButton.test.js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiPillButton from './UiPillButton.vue'

describe('UiPillButton', () => {
  it('uses pressed button semantics and emits click', async () => {
    const wrapper = mount(UiPillButton, { props: { active: true }, slots: { default: '一键发布' } })
    expect(wrapper.get('button').attributes('aria-pressed')).toBe('true')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })
})

// UiCompactHeader.test.js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiCompactHeader from './UiCompactHeader.vue'

describe('UiCompactHeader', () => {
  it('renders the requested heading level and optional meta', () => {
    const wrapper = mount(UiCompactHeader, { props: { title: '今日任务', meta: '08月03日', level: 3 } })
    expect(wrapper.get('h3').text()).toBe('今日任务')
    expect(wrapper.get('.ui-compact-header__meta').text()).toBe('08月03日')
  })
})

// UiInsetSurface.test.js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiInsetSurface from './UiInsetSurface.vue'

describe('UiInsetSurface', () => {
  it('keeps interaction semantics in its slotted controls', () => {
    const wrapper = mount(UiInsetSurface, {
      props: { border: 'dashed', interactive: true },
      slots: { default: '<button type="button">打开文档</button>', actions: '<button type="button">复制</button>' },
    })
    expect(wrapper.get('.ui-inset-surface').attributes('data-border')).toBe('dashed')
    expect(wrapper.findAll('button')).toHaveLength(2)
    expect(wrapper.find('.ui-inset-surface > button').exists()).toBe(false)
  })
})
```

- [ ] **Step 2: Run molecule tests and verify RED**

Run:

```powershell
npx vitest run src/design-system/components/general/UiPillButton.test.js src/design-system/components/data-display/UiCompactHeader.test.js src/design-system/components/data-display/UiInsetSurface.test.js
```

Expected: module resolution failures because the three components do not exist.

- [ ] **Step 3: Implement UiPillButton**

```vue
<template>
  <UiButton
    size="xs"
    shape="pill"
    :variant="active || tone === 'action' ? 'primary' : 'secondary'"
    :disabled="disabled"
    :aria-pressed="active ? 'true' : 'false'"
    @click="emit('click', $event)"
  ><slot /></UiButton>
</template>

<script setup>
import UiButton from './UiButton.vue'
defineProps({
  active: Boolean,
  disabled: Boolean,
  tone: { type: String, default: 'neutral', validator: (value) => ['neutral', 'action'].includes(value) },
})
const emit = defineEmits(['click'])
</script>
```

- [ ] **Step 4: Implement UiCompactHeader**

```vue
<template>
  <header class="ui-compact-header" :data-size="size">
    <component :is="`h${level}`" class="ui-compact-header__title">{{ title }}</component>
    <slot />
    <span v-if="meta" class="ui-compact-header__meta">{{ meta }}</span>
    <span v-if="$slots.action" class="ui-compact-header__action"><slot name="action" /></span>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  meta: { type: String, default: '' },
  level: { type: Number, default: 2, validator: (value) => value >= 2 && value <= 6 },
  size: { type: String, default: 'sm', validator: (value) => ['sm', 'md'].includes(value) },
})
</script>

<style scoped>
.ui-compact-header { display: flex; min-width: 0; align-items: center; gap: var(--ui-space-2); }
.ui-compact-header__title { min-width: 0; flex: 1; overflow: hidden; margin: 0; color: var(--ui-color-text-strong); text-overflow: ellipsis; white-space: nowrap; }
.ui-compact-header[data-size='sm'] .ui-compact-header__title { font-size: 16px; line-height: 22px; }
.ui-compact-header[data-size='md'] .ui-compact-header__title { font-size: 18px; line-height: 23px; }
.ui-compact-header__meta { flex: 0 0 auto; color: var(--ui-color-text-muted); font-size: 10px; white-space: nowrap; }
.ui-compact-header__action { display: inline-flex; flex: 0 0 auto; }
</style>
```

- [ ] **Step 5: Implement UiInsetSurface**

```vue
<template>
  <div class="ui-inset-surface" :data-border="border" :data-tone="tone" :data-interactive="interactive ? 'true' : undefined">
    <div class="ui-inset-surface__content"><slot /></div>
    <div v-if="$slots.actions" class="ui-inset-surface__actions"><slot name="actions" /></div>
  </div>
</template>

<script setup>
defineProps({
  border: { type: String, default: 'dashed', validator: (value) => ['dashed', 'solid'].includes(value) },
  tone: { type: String, default: 'default', validator: (value) => ['default', 'muted'].includes(value) },
  interactive: Boolean,
})
</script>

<style scoped>
.ui-inset-surface { display: flex; min-width: 0; min-height: 0; box-sizing: border-box; align-items: center; gap: var(--ui-space-2); border: 1px dashed var(--ui-color-border-strong); border-radius: var(--ui-radius-md); padding: 0 var(--ui-space-3); overflow: hidden; background: var(--ui-color-shell); color: var(--ui-color-text); }
.ui-inset-surface[data-border='solid'] { border-style: solid; }
.ui-inset-surface[data-tone='muted'] { background: color-mix(in srgb, var(--ui-color-surface-muted) 36%, var(--ui-color-shell)); }
.ui-inset-surface[data-interactive='true']:hover,
.ui-inset-surface[data-interactive='true']:focus-within { border-color: var(--ui-color-action); }
.ui-inset-surface__content { min-width: 0; flex: 1; overflow: hidden; }
.ui-inset-surface__actions { display: flex; flex: 0 0 auto; align-items: center; gap: var(--ui-space-1); }
</style>
```

- [ ] **Step 6: Run molecule tests and verify GREEN**

Run the command from Step 2. Expected: all tests pass.

- [ ] **Step 7: Add Storybook entries**

Create autodocs stories named `通用/PillButton 胶囊按钮`, `数据展示/CompactHeader 紧凑标题`, and `数据展示/InsetSurface 内嵌表面`. Include default, active, disabled, actions, long text, and narrow-container states.

## Task 3: Publish the new public surface and design-language pages

**Files:**

- Modify: `study-hub/frontend/src/design-system/index.js`
- Modify: `study-hub/frontend/docs/study-ui/component-status.md`
- Create: `study-hub/frontend/src/design-system/foundations/DesignLanguage.stories.js`
- Modify: `study-hub/frontend/src/design-system/documentation.test.js`

- [ ] **Step 1: Extend the documentation contract test**

Add an assertion that the five design-language story exports exist:

```js
const designLanguage = await readFile(resolve('src/design-system/foundations/DesignLanguage.stories.js'), 'utf8')
for (const story of ['Overview', 'ColorsAndStatus', 'TypographyAndDensity', 'SpacingAndRadius', 'ShadowAndMotion']) {
  expect(designLanguage).toContain(`export const ${story}`)
}
```

- [ ] **Step 2: Run the documentation test and verify RED**

```powershell
npx vitest run src/design-system/documentation.test.js
```

Expected: failure because `DesignLanguage.stories.js` and the three public component rows do not exist.

- [ ] **Step 3: Export and document the molecules**

Append to `src/design-system/index.js`:

```js
export { default as UiPillButton } from './components/general/UiPillButton.vue'
export { default as UiCompactHeader } from './components/data-display/UiCompactHeader.vue'
export { default as UiInsetSurface } from './components/data-display/UiInsetSurface.vue'
```

Add three `Candidate 0.2` rows to `component-status.md` with tests, stories, accessibility notes, “homepage frame extraction” Figma mapping, and `@study-ui` imports.

- [ ] **Step 4: Create the design-language Storybook page**

Create one story module with `title: '设计语言/Study UI'` and five named exports. Each render reads CSS variables using `var(--ui-...)`; no raw replacement palette is introduced. `Overview` displays the dependency chain, `ColorsAndStatus` displays semantic swatches, `TypographyAndDensity` displays the five text levels and four control sizes, `SpacingAndRadius` displays the spacing/radius scale, and `ShadowAndMotion` displays card/overlay shadow and motion durations.

- [ ] **Step 5: Run the documentation test and verify GREEN**

Run the command from Step 2. Expected: pass.

## Task 4: Migrate the repeated row, title, and pill structures

**Files:**

- Modify: `study-hub/frontend/src/design-system/widgets/KnowledgeWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/QuickCommandWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CreationWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/WorkflowWidget.vue`
- Modify: their existing test files

- [ ] **Step 1: Add failing integration assertions**

In `DashboardCompositeWidgets.test.js` and `KnowledgeWidget.test.js`, mount the widgets and assert:

```js
expect(wrapper.findComponent(UiCompactHeader).exists()).toBe(true)
expect(wrapper.findComponent(UiInsetSurface).exists()).toBe(true)
expect(wrapper.findComponent(UiPillButton).exists()).toBe(true)
```

Keep the existing event assertions for `open`, `copy`, `remove`, and `run`.

- [ ] **Step 2: Run the widget tests and verify RED**

```powershell
npx vitest run src/design-system/widgets/KnowledgeWidget.test.js src/design-system/widgets/DashboardCompositeWidgets.test.js src/design-system/widgets/CreationWidget.test.js src/design-system/widgets/WorkflowWidget.test.js
```

Expected: failures because the widgets still own the repeated structures.

- [ ] **Step 3: Migrate KnowledgeWidget and QuickCommandWidget**

Use `UiCompactHeader` for each title. Wrap document/command rows with `UiInsetSurface`, keep native buttons inside, and keep the original emitted ids. Use `UiButton size="xs" shape="pill"` for copy/delete controls. Remove only CSS declarations now owned by the shared components.

- [ ] **Step 4: Migrate CreationWidget and WorkflowWidget**

Use `UiCompactHeader`, replace option/step buttons with `UiPillButton`, and use `UiInsetSurface` around creation title strips and the workflow input. Keep `open(item.id)` and `run(step.id)` payloads unchanged.

- [ ] **Step 5: Run the widget tests and verify GREEN**

Run the command from Step 2. Expected: all files pass and all existing event payload checks remain green.

## Task 5: Migrate compact status and header patterns in the remaining widgets

**Files:**

- Modify: `study-hub/frontend/src/design-system/widgets/AutomationQueueWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CalendarAgendaWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/WorkHeatmapWidget.vue`
- Modify: their existing test files

- [ ] **Step 1: Add failing component-usage assertions**

Assert AutomationQueue uses `UiProgress` with `size="compact"`, its micro actions use `UiButton size="xs"`, and CalendarAgenda, TodayFocus, and WorkHeatmap use `UiCompactHeader`.

- [ ] **Step 2: Run the affected widget tests and verify RED**

```powershell
npx vitest run src/design-system/widgets/AutomationQueueWidget.test.js src/design-system/widgets/DashboardCompositeWidgets.test.js src/design-system/widgets/WorkHeatmapWidget.test.js
```

- [ ] **Step 3: Replace local progress and button sizing**

In AutomationQueueWidget, replace the hand-built `<i><em /></i>` progress bar with:

```vue
<UiProgress
  :value="Math.max(8, item.progress || 0)"
  size="compact"
  :status="item.status === 'error' ? 'danger' : item.status === 'done' ? 'success' : 'active'"
  :aria-label="`${item.title}进度`"
/>
```

Use `size="xs" shape="pill"` for retry, view-more, and start actions where their current geometry requires a capsule.

- [ ] **Step 4: Replace repeated headers**

Use `UiCompactHeader` in CalendarAgenda, TodayFocus, and WorkHeatmap. Preserve their current heading levels, date/meta content, and action placement. DailyMemory remains domain-specific and receives no artificial decomposition.

- [ ] **Step 5: Run the affected widget tests and verify GREEN**

Run the command from Step 2. Expected: pass.

## Task 6: Reorganize Storybook and add the full dashboard example

**Files:**

- Modify: all `study-hub/frontend/src/design-system/widgets/*.stories.js`
- Create: `study-hub/frontend/src/design-system/examples/HomeDashboardExample.vue`
- Create: `study-hub/frontend/src/design-system/examples/HomeDashboardExample.stories.js`
- Modify: `study-hub/frontend/docs/study-ui/README.md`

- [ ] **Step 1: Write a static catalog contract test**

Extend `documentation.test.js` to assert that every current dashboard widget story title starts with `仪表盘组件/` and that `HomeDashboardExample.stories.js` contains `完整范例/首页仪表盘`.

- [ ] **Step 2: Run the contract test and verify RED**

```powershell
npx vitest run src/design-system/documentation.test.js
```

- [ ] **Step 3: Rename widget story groups and normalize states**

Change the nine current widget titles from `Study Hub Widgets/...` to `仪表盘组件/...`. Each widget keeps or adds the applicable exports from this set: `Default`, `Loading`, `Empty`, `Error`, `LongContent`, and `Overflow`.

- [ ] **Step 4: Create the full dashboard example**

`HomeDashboardExample.vue` imports `WorkbenchFrame`, `CapsuleNavigation`, `GreetingBar`, `BentoDashboardGrid`, `DashboardModuleCard`, and all nine widgets. It uses static arrays for heatmap cells, calendar days, tasks, queue items, documents, commands, creations, and workflow steps. It maps the existing dashboard registry order and spans into `grid-column` and `grid-row`; it does not call stores, fetch, routing side effects, or localStorage.

The story uses:

```js
import HomeDashboardExample from './HomeDashboardExample.vue'

export default {
  title: '完整范例/首页仪表盘',
  component: HomeDashboardExample,
  tags: ['autodocs'],
  parameters: { layout: 'fullscreen', viewport: { defaultViewport: 'desktop' } },
}

export const Default = {}
```

- [ ] **Step 5: Update the Study UI README**

Document the final navigation categories and the dual classification rule: Storybook groups by function while each component page states its atomic level.

- [ ] **Step 6: Run the contract test and verify GREEN**

Run the command from Step 2. Expected: pass.

## Task 7: Protect the live home and complete verification

**Files:**

- Modify: `study-hub/frontend/tests/home-card-contract.mjs`
- Verify: all task files

- [ ] **Step 1: Extend the home contract before final cleanup**

Add static assertions that the migrated widgets import the expected shared components and that the old deep button-size overrides and hand-built queue progress track are absent.

- [ ] **Step 2: Run the contract test and confirm it detects any remaining local duplication**

```powershell
node tests/home-card-contract.mjs
```

Expected before cleanup: failure naming any remaining duplicate structure. Remove only the reported obsolete declarations and rerun until green.

- [ ] **Step 3: Run all component and documentation tests**

```powershell
npm run test:unit
```

Expected: all tests pass with zero failed files.

- [ ] **Step 4: Build Storybook and production**

```powershell
npm run build:storybook
npm run build
```

Expected: both commands exit 0.

- [ ] **Step 5: Run the live-home regression suite**

```powershell
node tests/home-card-contract.mjs
node tests/home-responsive.mjs
node tests/home-visual-overlay.mjs
node tests/home-layout-persistence.mjs
```

Expected: proportional stage, five PC viewports, Figma overlay geometry, 16px card inset, no overflow, and layout persistence all pass.

- [ ] **Step 6: Inspect the generated Storybook and homepage screenshots**

Open the built catalog or run Storybook on the fixed catalog port, inspect design-language pages, the three new molecules, all nine widgets, and the full dashboard example. Inspect `test-results/study-ui/home-1440.png` and one widescreen screenshot for visual regression.

- [ ] **Step 7: Run repository hygiene checks**

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors. Do not stage or overwrite unrelated dirty files.
