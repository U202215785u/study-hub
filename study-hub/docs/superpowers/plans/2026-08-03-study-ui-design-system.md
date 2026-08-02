# Study UI Design System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a documented, tested Study UI component system from the approved Figma dashboard language and migrate the Study Hub homepage to consume it.

**Architecture:** Keep Study UI as an internal Vue module exposed only through `src/design-system/index.js`. CSS custom properties are the runtime source of truth; Tailwind maps utilities to those properties, while Storybook documents components by functional category. Domain widgets depend on public Study UI components, and the homepage owns data orchestration rather than visual rules.

**Tech Stack:** Vue 3.5, Vite 5, Tailwind CSS 3.4, Storybook for Vue/Vite, Vitest, Vue Test Utils, Storybook accessibility addon, Playwright screenshot verification.

---

## File Map

### Configuration

- Modify `frontend/package.json`: add Storybook, unit-test and verification scripts.
- Modify `frontend/vite.config.js`: add `@study-ui` alias and Vitest environment.
- Modify `frontend/tailwind.config.js`: map existing utilities to semantic CSS variables.
- Create `frontend/.storybook/main.js`: Storybook stories and addons.
- Create `frontend/.storybook/preview.js`: load tokens and define viewport backgrounds.
- Create `frontend/vitest.setup.js`: reset DOM state after component tests.

### Foundations

- Create `frontend/src/design-system/foundations/tokens.css`: primitive, semantic and component CSS variables.
- Create `frontend/src/design-system/foundations/tokens.js`: documented token metadata for Storybook tables.
- Create `frontend/src/design-system/foundations/index.js`: foundation exports.
- Modify `frontend/src/assets/main.css`: import tokens and set semantic application defaults.

### Public Components

- Create `frontend/src/design-system/components/general/UiButton.vue`.
- Create `frontend/src/design-system/components/general/UiIconButton.vue`.
- Create `frontend/src/design-system/components/data-entry/UiInput.vue`.
- Create `frontend/src/design-system/components/data-entry/UiSelect.vue`.
- Create `frontend/src/design-system/components/data-display/UiTag.vue`.
- Create `frontend/src/design-system/components/data-display/UiBadge.vue`.
- Create `frontend/src/design-system/components/data-display/UiProgress.vue`.
- Create `frontend/src/design-system/components/feedback/UiSpinner.vue`.
- Create `frontend/src/design-system/components/feedback/UiEmpty.vue`.
- Create `UiButton.test.js`, `UiButton.stories.js`, `UiIconButton.test.js`, `UiIconButton.stories.js`, `UiInput.test.js`, `UiInput.stories.js`, `UiSelect.test.js`, `UiSelect.stories.js`, `UiTag.test.js`, `UiTag.stories.js`, `UiBadge.test.js`, `UiBadge.stories.js`, `UiProgress.test.js`, `UiProgress.stories.js`, `UiSpinner.test.js`, `UiSpinner.stories.js`, `UiEmpty.test.js`, and `UiEmpty.stories.js` beside their components.

### Patterns And Widgets

- Create `frontend/src/design-system/patterns/UiPanelHeader.vue`.
- Create `frontend/src/design-system/patterns/UiWidgetFrame.vue`.
- Create `frontend/src/design-system/patterns/UiDashboardGrid.vue`.
- Create `frontend/src/design-system/patterns/UiDashboardItem.vue`.
- Create `frontend/src/design-system/patterns/UiAppShell.vue`.
- Create: `frontend/src/design-system/components/data-entry/UiInput.test.js`
- Create: `frontend/src/design-system/components/data-entry/UiInput.stories.js`
- Create: `frontend/src/design-system/components/data-entry/UiSelect.test.js`
- Create: `frontend/src/design-system/components/data-entry/UiSelect.stories.js`
- Create: `frontend/src/design-system/components/data-display/UiTag.test.js`
- Create: `frontend/src/design-system/components/data-display/UiTag.stories.js`
- Create: `frontend/src/design-system/components/data-display/UiBadge.test.js`
- Create: `frontend/src/design-system/components/data-display/UiBadge.stories.js`
- Create: `frontend/src/design-system/components/data-display/UiProgress.test.js`
- Create: `frontend/src/design-system/components/data-display/UiProgress.stories.js`
- Create: `frontend/src/design-system/components/feedback/UiSpinner.test.js`
- Create: `frontend/src/design-system/components/feedback/UiSpinner.stories.js`
- Create: `frontend/src/design-system/components/feedback/UiEmpty.test.js`
- Create: `frontend/src/design-system/components/feedback/UiEmpty.stories.js`
- Create `frontend/src/design-system/widgets/TaskWidget.vue`.
- Create `frontend/src/design-system/widgets/CalendarWidget.vue`.
- Create `frontend/src/design-system/widgets/AutomationQueueWidget.vue`.
- Create `frontend/src/design-system/widgets/KnowledgeWidget.vue`.
- Create `frontend/src/design-system/widgets/CreationWidget.vue`.
- Create `frontend/src/design-system/widgets/WorkflowWidget.vue`.
- Create `frontend/src/design-system/index.js`: the only public import surface.

### Homepage Integration

- Create `frontend/src/composables/home/useHomeSearch.js`.
- Create `frontend/src/composables/home/useAutomationQueue.js`.
- Create `frontend/src/composables/home/useKnowledgeDocuments.js`.
- Create `frontend/src/composables/home/useDailyReview.js`.
- Modify `frontend/src/views/Home.vue`: compose Study UI widgets and preserve business behavior.
- Modify `frontend/src/App.vue`: use `UiAppShell` for regular routes.
- Modify `frontend/src/components/NavBar.vue`: render the new navigation contract.
- Create `frontend/src/views/Home.test.js`: page-level behavior test.
- Create `frontend/tests/home-responsive.mjs`: desktop/mobile runtime checks.
- Create `frontend/docs/study-ui/component-status.md`: component ownership and Figma mapping table.

## Task 1: Add The Component-Library Tooling Baseline

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.js`
- Create: `frontend/vitest.setup.js`
- Create: `frontend/.storybook/main.js`
- Create: `frontend/.storybook/preview.js`
- Test: `frontend/src/design-system/tooling.test.js`

- [ ] **Step 1: Install development dependencies**

Run:

```powershell
cd frontend
npm install --save-dev --no-audit --no-fund storybook@8.6.14 @storybook/vue3-vite@8.6.14 @storybook/addon-docs@8.6.14 @storybook/addon-a11y@8.6.14 vitest@2.1.9 @vue/test-utils@2.4.11 jsdom@25.0.1 playwright@1.62.1
npx playwright install chromium
```

Expected: `package.json` and `package-lock.json` contain the new development dependencies and npm exits with code 0.

- [ ] **Step 2: Add scripts to `package.json`**

Add these entries under `scripts`:

```json
{
  "test:unit": "vitest run",
  "test:unit:watch": "vitest",
  "storybook": "storybook dev -p 6006",
  "build:storybook": "storybook build",
  "verify:study-ui": "npm run test:unit && npm run build:storybook && npm run build"
}
```

- [ ] **Step 3: Write a failing tooling contract test**

Create `src/design-system/tooling.test.js`:

```js
import { describe, expect, it } from 'vitest'
import * as studyUi from './index'

describe('Study UI public surface', () => {
  it('exports an object from the stable entry point', () => {
    expect(studyUi).toBeTypeOf('object')
  })
})
```

- [ ] **Step 4: Run the test and verify the missing entry point fails**

Run: `npm run test:unit -- src/design-system/tooling.test.js`

Expected: FAIL because `src/design-system/index.js` does not exist.

- [ ] **Step 5: Configure Vite and Vitest**

Update `vite.config.js` with the alias and test block:

```js
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(() => ({
  plugins: [vue()],
  resolve: {
    alias: {
      '@study-ui': fileURLToPath(new URL('./src/design-system/index.js', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js'],
  },
  base: process.env.VITE_ELECTRON ? './' : '/',
  build: { outDir: 'dist', emptyOutDir: true },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8741', changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, '') },
      '/mods': { target: 'http://localhost:8741', changeOrigin: true },
      '/second-self/api': { target: 'http://localhost:8741', changeOrigin: true },
    },
  },
}))
```

Create `vitest.setup.js`:

```js
import { afterEach } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

enableAutoUnmount(afterEach)
```

- [ ] **Step 6: Configure Storybook**

Create `.storybook/main.js`:

```js
export default {
  stories: ['../src/**/*.stories.@(js|mdx)'],
  addons: ['@storybook/addon-docs', '@storybook/addon-a11y'],
  framework: { name: '@storybook/vue3-vite', options: {} },
}
```

Create `.storybook/preview.js`:

```js
import '../src/assets/main.css'

export default {
  parameters: {
    backgrounds: {
      default: 'canvas',
      values: [
        { name: 'canvas', value: '#10140F' },
        { name: 'surface', value: '#1B1D1A' },
      ],
    },
    viewport: {
      viewports: {
        mobile: { name: 'Mobile 390', styles: { width: '390px', height: '844px' } },
        tablet: { name: 'Tablet 768', styles: { width: '768px', height: '1024px' } },
        desktop: { name: 'Desktop 1440', styles: { width: '1440px', height: '980px' } },
      },
    },
  },
}
```

- [ ] **Step 7: Add the temporary public entry point and verify tooling**

Create `src/design-system/index.js`:

```js
export const STUDY_UI_VERSION = '0.1.0'
```

Run: `npm run test:unit -- src/design-system/tooling.test.js`

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/vitest.setup.js frontend/.storybook frontend/src/design-system/tooling.test.js frontend/src/design-system/index.js
git commit -m "chore(ui): add Study UI tooling baseline"
```

## Task 2: Establish Tokens As The Single Visual Source

**Files:**
- Create: `frontend/src/design-system/foundations/tokens.css`
- Create: `frontend/src/design-system/foundations/tokens.js`
- Create: `frontend/src/design-system/foundations/index.js`
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/tailwind.config.js`
- Test: `frontend/src/design-system/foundations/tokens.test.js`

- [ ] **Step 1: Write the token contract test**

Create `tokens.test.js`:

```js
import { describe, expect, it } from 'vitest'
import { semanticTokens } from './tokens'

describe('Study UI tokens', () => {
  it('keeps action, status and content colors separate', () => {
    expect(semanticTokens.color.actionPrimary).toBe('--ui-color-action')
    expect(semanticTokens.color.contentPurple).toBe('--ui-color-content-purple')
    expect(semanticTokens.color.danger).not.toBe(semanticTokens.color.contentOrange)
  })

  it('uses a four-pixel spacing grid', () => {
    expect(semanticTokens.space).toEqual([
      '--ui-space-0', '--ui-space-1', '--ui-space-2', '--ui-space-3', '--ui-space-4',
      '--ui-space-5', '--ui-space-6', '--ui-space-8', '--ui-space-10', '--ui-space-12',
    ])
  })
})
```

- [ ] **Step 2: Run the test and verify exports are missing**

Run: `npm run test:unit -- src/design-system/foundations/tokens.test.js`

Expected: FAIL because `tokens.js` does not exist.

- [ ] **Step 3: Create the documented token metadata**

Create `tokens.js`:

```js
export const semanticTokens = Object.freeze({
  color: {
    canvas: '--ui-color-canvas', surface: '--ui-color-surface', surfaceRaised: '--ui-color-surface-raised',
    textStrong: '--ui-color-text-strong', textDefault: '--ui-color-text', textMuted: '--ui-color-text-muted',
    actionPrimary: '--ui-color-action', actionPrimaryText: '--ui-color-action-text',
    contentPurple: '--ui-color-content-purple', contentOrange: '--ui-color-content-orange',
    contentPeach: '--ui-color-content-peach', contentCream: '--ui-color-content-cream',
    success: '--ui-color-success', warning: '--ui-color-warning', danger: '--ui-color-danger', info: '--ui-color-info',
  },
  space: ['--ui-space-0', '--ui-space-1', '--ui-space-2', '--ui-space-3', '--ui-space-4', '--ui-space-5', '--ui-space-6', '--ui-space-8', '--ui-space-10', '--ui-space-12'],
  radius: { sm: '--ui-radius-sm', md: '--ui-radius-md', lg: '--ui-radius-lg', widget: '--ui-radius-widget' },
  duration: { fast: '--ui-duration-fast', normal: '--ui-duration-normal', slow: '--ui-duration-slow' },
  breakpoint: { mobile: 390, tablet: 768, compact: 1024, wide: 1280 },
})
```

Create `foundations/index.js`:

```js
export { semanticTokens } from './tokens'
```

- [ ] **Step 4: Create runtime CSS variables**

Create `tokens.css`:

```css
:root {
  color-scheme: dark;
  --ui-color-canvas: #10140f;
  --ui-color-surface: #1b1d1a;
  --ui-color-surface-raised: #252824;
  --ui-color-border: rgb(245 246 238 / 12%);
  --ui-color-border-strong: rgb(245 246 238 / 20%);
  --ui-color-text-strong: #f5f6ee;
  --ui-color-text: #d9ddcf;
  --ui-color-text-muted: #8b9186;
  --ui-color-action: #d7ff63;
  --ui-color-action-text: #11140f;
  --ui-color-content-purple: #8b73ff;
  --ui-color-content-orange: #ea4e00;
  --ui-color-content-peach: #ffb183;
  --ui-color-content-cream: #f4e6c5;
  --ui-color-success: #4fd69c;
  --ui-color-warning: #f0c75e;
  --ui-color-danger: #ff6b78;
  --ui-color-info: #6cb8ff;
  --ui-space-0: 0; --ui-space-1: 4px; --ui-space-2: 8px; --ui-space-3: 12px;
  --ui-space-4: 16px; --ui-space-5: 20px; --ui-space-6: 24px;
  --ui-space-8: 32px; --ui-space-10: 40px; --ui-space-12: 48px;
  --ui-radius-sm: 6px; --ui-radius-md: 10px; --ui-radius-lg: 16px; --ui-radius-widget: 22px;
  --ui-shadow-widget: 0 18px 34px -8px rgb(0 0 0 / 22%);
  --ui-focus-ring: 0 0 0 3px rgb(215 255 99 / 35%);
  --ui-duration-fast: 120ms; --ui-duration-normal: 180ms; --ui-duration-slow: 260ms;
}

@media (prefers-reduced-motion: reduce) {
  :root { --ui-duration-fast: 0ms; --ui-duration-normal: 0ms; --ui-duration-slow: 0ms; }
}
```

- [ ] **Step 5: Map Tailwind aliases to semantic variables**

Replace the custom `colors` in `tailwind.config.js` with:

```js
colors: {
  bg: 'var(--ui-color-canvas)',
  surface: 'var(--ui-color-surface)',
  'surface-hover': 'var(--ui-color-surface-raised)',
  border: 'var(--ui-color-border)',
  text: 'var(--ui-color-text)',
  'text-secondary': 'var(--ui-color-text-muted)',
  accent: 'var(--ui-color-action)',
  danger: 'var(--ui-color-danger)',
  success: 'var(--ui-color-success)',
  warning: 'var(--ui-color-warning)',
}
```

Add `@import "../design-system/foundations/tokens.css";` at the start of `src/assets/main.css`, and change `body` to consume the semantic variables.

- [ ] **Step 6: Run token tests and application build**

Run: `npm run test:unit -- src/design-system/foundations/tokens.test.js`

Expected: PASS.

Run: `npm run build`

Expected: Vite build succeeds without unresolved CSS variables.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/design-system/foundations frontend/src/assets/main.css frontend/tailwind.config.js
git commit -m "feat(ui): establish Study UI design tokens"
```

## Task 3: Build Button Primitives And Their Documentation Contract

**Files:**
- Create: `frontend/src/design-system/components/general/UiButton.vue`
- Create: `frontend/src/design-system/components/general/UiIconButton.vue`
- Create: `frontend/src/design-system/components/general/UiButton.test.js`
- Create: `frontend/src/design-system/components/general/UiButton.stories.js`
- Modify: `frontend/src/design-system/index.js`

- [ ] **Step 1: Write failing interaction tests**

Create `UiButton.test.js`:

```js
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import UiButton from './UiButton.vue'
import UiIconButton from './UiIconButton.vue'

describe('UiButton', () => {
  it('emits one click and blocks clicks while loading', async () => {
    const wrapper = mount(UiButton, { slots: { default: '保存' } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
    await wrapper.setProps({ loading: true })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
    expect(wrapper.attributes('aria-busy')).toBe('true')
  })

  it('requires an accessible label for icon-only actions', () => {
    expect(() => mount(UiIconButton)).toThrow(/label/)
  })
})
```

- [ ] **Step 2: Run tests and verify components are missing**

Run: `npm run test:unit -- src/design-system/components/general/UiButton.test.js`

Expected: FAIL because component files do not exist.

- [ ] **Step 3: Implement `UiButton`**

Create `UiButton.vue` with props `variant`, `size`, `loading`, `disabled`, `block`, and `type`. Its root must be a native `<button>`, emit `click`, expose `prefix` and `suffix` slots, set `aria-busy`, and prevent emission when loading or disabled. Map variants to scoped CSS classes backed by `--ui-*` variables; use minimum heights `32px`, `40px`, and `48px` for `sm`, `md`, and `lg`.

The click guard must be:

```js
function onClick(event) {
  if (props.loading || props.disabled) return
  emit('click', event)
}
```

- [ ] **Step 4: Implement `UiIconButton`**

Create `UiIconButton.vue` as a wrapper around `UiButton` with required `label`, `title`, `variant`, `size`, `loading`, and `disabled` props. Set `aria-label` and `title` from `label`; in development, throw `new Error('UiIconButton requires a label')` when no label is supplied.

- [ ] **Step 5: Add Ant-style component stories**

Create `UiButton.stories.js` with `title: '通用/Button 按钮'`, autodocs tags, controls for every prop, and stories named `Primary`, `Variants`, `Sizes`, `WithIcon`, `Loading`, `Disabled`, `Danger`, and `Block`. The docs description must state that one action region contains at most one primary button.

- [ ] **Step 6: Export and verify**

Add to `src/design-system/index.js`:

```js
export { default as UiButton } from './components/general/UiButton.vue'
export { default as UiIconButton } from './components/general/UiIconButton.vue'
```

Run: `npm run test:unit -- src/design-system/components/general/UiButton.test.js`

Expected: PASS.

Run: `npm run build:storybook`

Expected: Storybook build succeeds and contains `通用/Button 按钮`.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/design-system/components/general frontend/src/design-system/index.js
git commit -m "feat(ui): add button primitives"
```

## Task 4: Build Form, Status, And Progress Primitives

**Files:**
- Create: `frontend/src/design-system/components/data-entry/UiInput.vue`
- Create: `frontend/src/design-system/components/data-entry/UiSelect.vue`
- Create: `frontend/src/design-system/components/data-display/UiTag.vue`
- Create: `frontend/src/design-system/components/data-display/UiBadge.vue`
- Create: `frontend/src/design-system/components/data-display/UiProgress.vue`
- Create: `frontend/src/design-system/components/feedback/UiSpinner.vue`
- Create: `frontend/src/design-system/components/feedback/UiEmpty.vue`
- Create: `frontend/src/design-system/patterns/UiPanelHeader.test.js`
- Create: `frontend/src/design-system/patterns/UiPanelHeader.stories.js`
- Create: `frontend/src/design-system/patterns/UiWidgetFrame.test.js`
- Create: `frontend/src/design-system/patterns/UiWidgetFrame.stories.js`
- Create: `frontend/src/design-system/patterns/UiDashboardGrid.test.js`
- Create: `frontend/src/design-system/patterns/UiDashboardGrid.stories.js`
- Create: `frontend/src/design-system/patterns/UiAppShell.test.js`
- Create: `frontend/src/design-system/patterns/UiAppShell.stories.js`
- Modify: `frontend/src/design-system/index.js`

- [ ] **Step 1: Write the public behavior tests**

Tests must assert these exact contracts:

```js
// UiInput: visible label is associated with the native input; error sets aria-invalid and aria-describedby.
// UiSelect: update:modelValue emits the selected native value.
// UiTag: tone="content-purple" is not accepted by UiBadge.
// UiBadge: status is one of neutral|info|success|warning|danger.
// UiProgress: value is clamped to 0..100 and exposed through aria-valuenow.
// UiSpinner: role="status" includes visually hidden loading text.
// UiEmpty: action slot renders only when supplied.
```

Use Vue Test Utils `mount`, native `setValue`, and explicit attribute assertions for each component.

- [ ] **Step 2: Run the component test folder and verify failure**

Run: `npm run test:unit -- src/design-system/components`

Expected: FAIL because the new components are not implemented.

- [ ] **Step 3: Implement data-entry components**

`UiInput` props: `modelValue`, `label`, `description`, `error`, `disabled`, `required`, `type`, `placeholder`, `id`. Emit `update:modelValue`, `focus`, and `blur`. Use a generated id only when no `id` is supplied.

`UiSelect` props: `modelValue`, `label`, `description`, `error`, `disabled`, `required`, `options`, `id`; option shape is `{ value: string, label: string, disabled?: boolean }`. Emit `update:modelValue`, `focus`, and `blur`.

- [ ] **Step 4: Implement data-display and feedback components**

`UiTag` uses content tones `neutral | lime | purple | orange | peach | cream` and has no status semantics.

`UiBadge` uses statuses `neutral | info | success | warning | danger`; it always renders a text label next to the status dot.

`UiProgress` supports `linear | segmented`, uses `role="progressbar"`, and renders a text label when `showValue` is true.

`UiSpinner` uses `role="status"`; `UiEmpty` exposes `icon`, default, and `action` slots.

- [ ] **Step 5: Add stories by functional category**

Create one story file per component. Use the navigation titles `数据录入/Input 输入框`, `数据录入/Select 选择器`, `数据展示/Tag 标签`, `数据展示/Badge 状态徽标`, `数据展示/Progress 进度`, `反馈/Spinner 加载中`, and `反馈/Empty 空状态`. Each file includes default, disabled, error or loading, and narrow-container stories as applicable.

- [ ] **Step 6: Export and verify**

Export every component from `src/design-system/index.js`.

Run: `npm run test:unit -- src/design-system/components`

Expected: all component tests PASS.

Run: `npm run build:storybook`

Expected: build succeeds with no accessibility addon configuration errors.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/design-system/components frontend/src/design-system/index.js
git commit -m "feat(ui): add form and status primitives"
```

## Task 5: Build Dashboard Layout Patterns

**Files:**
- Create: `frontend/src/design-system/patterns/UiPanelHeader.vue`
- Create: `frontend/src/design-system/patterns/UiWidgetFrame.vue`
- Create: `frontend/src/design-system/patterns/UiDashboardGrid.vue`
- Create: `frontend/src/design-system/patterns/UiDashboardItem.vue`
- Create: `frontend/src/design-system/patterns/UiAppShell.vue`
- Create: `frontend/src/design-system/widgets/TaskWidget.test.js`
- Create: `frontend/src/design-system/widgets/TaskWidget.stories.js`
- Create: `frontend/src/design-system/widgets/CalendarWidget.test.js`
- Create: `frontend/src/design-system/widgets/CalendarWidget.stories.js`
- Create: `frontend/src/design-system/widgets/AutomationQueueWidget.test.js`
- Create: `frontend/src/design-system/widgets/AutomationQueueWidget.stories.js`
- Create: `frontend/src/design-system/widgets/KnowledgeWidget.test.js`
- Create: `frontend/src/design-system/widgets/KnowledgeWidget.stories.js`
- Create: `frontend/src/design-system/widgets/CreationWidget.test.js`
- Create: `frontend/src/design-system/widgets/CreationWidget.stories.js`
- Create: `frontend/src/design-system/widgets/WorkflowWidget.test.js`
- Create: `frontend/src/design-system/widgets/WorkflowWidget.stories.js`
- Modify: `frontend/src/design-system/index.js`

- [ ] **Step 1: Write pattern tests**

Test the following contracts:

```js
// UiPanelHeader renders title, meta and actions without changing height when actions appear.
// UiWidgetFrame renders exactly one of content, loading, error, or empty state.
// UiDashboardGrid owns responsive columns; UiDashboardItem maps span="1x1|2x1|2x2|2x3" to data-span.
// UiAppShell labels primary navigation, main content and complementary Dock landmarks.
```

- [ ] **Step 2: Verify tests fail**

Run: `npm run test:unit -- src/design-system/patterns`

Expected: FAIL because pattern files are missing.

- [ ] **Step 3: Implement `UiWidgetFrame` state precedence**

Props: `title`, `description`, `loading`, `error`, `empty`, `ariaLabel`. Slots: `actions`, `default`, `loading`, `error`, `empty`, `footer`. State precedence is `loading > error > empty > content`; expose the active state as `data-state`.

- [ ] **Step 4: Implement grid and shell behavior**

`UiDashboardGrid` uses CSS Grid with four logical columns at `>=1280px`, three at `1024px`, two at `768px`, and one below `768px`. `UiDashboardItem` accepts `span="1x1|2x1|2x2|2x3"`, renders `data-span`, and clamps every span to one column on mobile.

`UiAppShell` uses slots `brand`, `topNavigation`, `sidebar`, `default`, and `dock`. The Dock is visible at `>=1280px`, becomes a drawer trigger slot from `1024px` to `1279px`, and is absent from layout below `1024px` unless explicitly opened.

- [ ] **Step 5: Add pattern stories**

Use titles `布局/AppShell 应用外壳`, `布局/DashboardGrid 仪表盘网格`, `数据展示/WidgetFrame 小组件框架`, and `通用/PanelHeader 面板标题`. The DashboardGrid story composes `UiDashboardItem` examples for all four spans. Include all state-precedence and four viewport stories.

- [ ] **Step 6: Export and verify**

Export patterns through `src/design-system/index.js`.

Run: `npm run test:unit -- src/design-system/patterns`

Expected: PASS.

Run: `npm run build:storybook`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/design-system/patterns frontend/src/design-system/index.js
git commit -m "feat(ui): add dashboard layout patterns"
```

## Task 6: Build The Six Homepage Widgets

**Files:**
- Create: `frontend/src/design-system/widgets/TaskWidget.vue`
- Create: `frontend/src/design-system/widgets/CalendarWidget.vue`
- Create: `frontend/src/design-system/widgets/AutomationQueueWidget.vue`
- Create: `frontend/src/design-system/widgets/KnowledgeWidget.vue`
- Create: `frontend/src/design-system/widgets/CreationWidget.vue`
- Create: `frontend/src/design-system/widgets/WorkflowWidget.vue`
- Create: `frontend/src/design-system/widgets/TaskWidget.test.js`
- Create: `frontend/src/design-system/widgets/TaskWidget.stories.js`
- Create: `frontend/src/design-system/widgets/CalendarWidget.test.js`
- Create: `frontend/src/design-system/widgets/CalendarWidget.stories.js`
- Create: `frontend/src/design-system/widgets/AutomationQueueWidget.test.js`
- Create: `frontend/src/design-system/widgets/AutomationQueueWidget.stories.js`
- Create: `frontend/src/design-system/widgets/KnowledgeWidget.test.js`
- Create: `frontend/src/design-system/widgets/KnowledgeWidget.stories.js`
- Create: `frontend/src/design-system/widgets/CreationWidget.test.js`
- Create: `frontend/src/design-system/widgets/CreationWidget.stories.js`
- Create: `frontend/src/design-system/widgets/WorkflowWidget.test.js`
- Create: `frontend/src/design-system/widgets/WorkflowWidget.stories.js`
- Modify: `frontend/src/design-system/index.js`

- [ ] **Step 1: Define and test serializable widget contracts**

Use these prop shapes in tests and implementation:

```js
const task = { id: 't1', title: '项目复盘', time: '10:00 - 11:00', status: 'running', progress: 30 }
const calendarDay = { date: '2026-06-07', label: '7', selected: true, eventTones: ['lime'] }
const queueItem = { id: 'q1', title: '抖音视频解析', status: 'running', progress: 42 }
const knowledgeItem = { id: 'k1', title: '设计系统笔记', meta: '今天', status: 'ready' }
const creationItem = { id: 'c1', title: '文章模板', thumbnail: '', kind: 'article' }
const workflowStep = { id: 'w1', label: '收集', status: 'done' }
```

Assert that each widget emits identifiers rather than mutating objects: `select`, `open`, `retry`, or `run` events carry the item id.

- [ ] **Step 2: Run widget tests and verify failure**

Run: `npm run test:unit -- src/design-system/widgets`

Expected: FAIL because widgets are missing.

- [ ] **Step 3: Implement widgets from public Study UI components**

Every widget must use `UiWidgetFrame`, public primitives, and CSS variables. Widgets may not import files inside another component's directory. Add `data-figma-node` attributes using the known Figma nodes or component names; use `349:405` for the task timeline, `349:516` for calendar, `349:369` for automation queue, `349:471` for knowledge, `349:493` for creation, and `349:459` for workflow.

- [ ] **Step 4: Add behavior and edge-state stories**

Use titles under `Study Hub/Widgets/*`. Every widget has `Default`, `Empty`, `Loading`, `Error`, `LongContent`, and `Mobile` stories. LongContent uses a 60-character Chinese title to prove truncation or wrapping behavior.

- [ ] **Step 5: Export and verify**

Export all six widgets through `src/design-system/index.js`.

Run: `npm run test:unit -- src/design-system/widgets`

Expected: PASS.

Run: `npm run build:storybook`

Expected: PASS with all six widget docs pages.

- [ ] **Step 6: Commit**

```powershell
git add frontend/src/design-system/widgets frontend/src/design-system/index.js
git commit -m "feat(ui): add Study Hub dashboard widgets"
```

## Task 7: Extract Homepage Business State Into Composables

**Files:**
- Create: `frontend/src/composables/home/useHomeSearch.js`
- Create: `frontend/src/composables/home/useAutomationQueue.js`
- Create: `frontend/src/composables/home/useKnowledgeDocuments.js`
- Create: `frontend/src/composables/home/useDailyReview.js`
- Create: `frontend/src/composables/home/useHomeSearch.test.js`
- Create: `frontend/src/composables/home/useAutomationQueue.test.js`
- Create: `frontend/src/composables/home/useKnowledgeDocuments.test.js`
- Create: `frontend/src/composables/home/useDailyReview.test.js`
- Modify: `frontend/src/views/Home.vue`

- [ ] **Step 1: Characterize existing behavior with tests**

For each composable, inject an API adapter rather than importing the settings store directly. Tests must assert:

```js
// Search: Enter submits current mode/query/category and exposes loading/error/result.
// Queue: polling starts once, maps server tasks, and stops on dispose.
// Knowledge: sorting and reload preserve current category.
// Review: polish and weekly-report calls expose status without replacing raw input.
```

Use fake timers for queue polling and rejected promises for error paths.

- [ ] **Step 2: Run composable tests and verify failure**

Run: `npm run test:unit -- src/composables/home`

Expected: FAIL because composables do not exist.

- [ ] **Step 3: Implement composables with explicit dependency injection**

Each function accepts `{ apiGet, apiPost, apiDelete }` or the smallest required subset. Return only Vue refs and commands consumed by `Home.vue`; start polling from an explicit `start()` command and expose `stop()` for `onUnmounted`.

- [ ] **Step 4: Replace matching inline logic in `Home.vue`**

Import the composables, connect their refs and commands, and remove only the duplicated logic they replace. Do not alter endpoint paths or payload shapes during this task.

- [ ] **Step 5: Run unit and existing routing checks**

Run: `npm run test:unit -- src/composables/home`

Expected: PASS.

Run: `npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add frontend/src/composables/home frontend/src/views/Home.vue
git commit -m "refactor(home): extract dashboard state composables"
```

## Task 8: Migrate The Homepage And Application Shell

**Files:**
- Modify: `frontend/src/views/Home.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/NavBar.vue`
- Create: `frontend/src/views/Home.test.js`

- [ ] **Step 1: Write the page composition test**

Mount `Home.vue` with router and Pinia test instances. Stub network adapters and assert the page renders `UiDashboardGrid`, all six widget components, one primary search action, and accessible navigation landmarks. Assert legacy API commands are still reachable through widget events.

- [ ] **Step 2: Run the page test and verify failure**

Run: `npm run test:unit -- src/views/Home.test.js`

Expected: FAIL because the homepage still uses duplicated legacy markup.

- [ ] **Step 3: Replace visual markup with Study UI composition**

Use this page hierarchy:

```vue
<UiDashboardGrid aria-label="首页工作台">
  <UiDashboardItem span="2x3"><TaskWidget /></UiDashboardItem>
  <UiDashboardItem span="2x2"><CalendarWidget /></UiDashboardItem>
  <UiDashboardItem span="2x2"><AutomationQueueWidget /></UiDashboardItem>
  <UiDashboardItem span="2x1"><KnowledgeWidget /></UiDashboardItem>
  <UiDashboardItem span="2x2"><CreationWidget /></UiDashboardItem>
  <UiDashboardItem span="2x1"><WorkflowWidget /></UiDashboardItem>
</UiDashboardGrid>
```

Keep modal and drawer business flows reachable through component events. Remove Tailwind class strings that duplicate public component visuals; page-only grid placement may remain.

- [ ] **Step 4: Apply `UiAppShell` in `App.vue`**

Retain the existing full-screen route behavior for `/wiki` and `/kb`. Regular routes render `NavBar`, the route view, system status, optional sidebar, and optional Dock through `UiAppShell` slots.

- [ ] **Step 5: Update navigation semantics**

`NavBar.vue` must expose one primary `<nav aria-label="主导航">`, use icon buttons only with accessible labels, and move overflow items into a named menu at compact widths.

- [ ] **Step 6: Verify page and application build**

Run: `npm run test:unit -- src/views/Home.test.js`

Expected: PASS.

Run: `npm run build`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/views/Home.vue frontend/src/views/Home.test.js frontend/src/App.vue frontend/src/components/NavBar.vue
git commit -m "feat(home): migrate dashboard to Study UI"
```

## Task 9: Verify Responsive Behavior And Visual Fidelity

**Files:**
- Create: `frontend/tests/home-responsive.mjs`
- Create: `frontend/tests/home-visual-baseline.md`
- Modify affected Study UI CSS only when verification finds discrepancies.

- [ ] **Step 1: Add a responsive browser check**

The script opens `/`, tests widths `1440`, `1024`, `768`, and `390`, and asserts:

```js
import assert from 'node:assert/strict'
import { mkdir, stat } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'

const origin = process.env.STUDY_UI_ORIGIN || 'http://127.0.0.1:5173'
const output = resolve('test-results/study-ui')
const widths = [1440, 1024, 768, 390]
await mkdir(output, { recursive: true })

const browser = await chromium.launch({ headless: true })
try {
  const page = await browser.newPage()
  for (const width of widths) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 980 })
    await page.goto(origin, { waitUntil: 'networkidle' })
    const geometry = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }))
    assert.ok(geometry.scrollWidth <= geometry.clientWidth, `horizontal overflow at ${width}px`)
    assert.equal(await page.getByRole('navigation', { name: '主导航' }).count(), 1)
    assert.equal(await page.getByRole('main').count(), 1)
    const target = resolve(output, `home-${width}.png`)
    await page.screenshot({ path: target, fullPage: true })
    assert.ok((await stat(target)).size > 10_000, `blank or incomplete screenshot at ${width}px`)
  }
} finally {
  await browser.close()
}
console.log('Study UI responsive checks passed')
```

- [ ] **Step 2: Start the frontend and run the check**

Run: `npm run dev -- --host 127.0.0.1`

In another terminal, run: `node tests/home-responsive.mjs`

Expected: four checks PASS and four nonblank screenshots are created.

- [ ] **Step 3: Compare against Figma node `349:96`**

Record in `home-visual-baseline.md` the verified values for canvas, surface, primary action, typography hierarchy, widget radius, grid rhythm, navigation placement, Dock behavior, and each breakpoint. For every discrepancy, name the affected Study UI component and fix that component rather than adding page-specific overrides.

- [ ] **Step 4: Run the complete verification suite**

Run: `npm run verify:study-ui`

Expected: unit tests, Storybook build, and application build all PASS.

Run: `node tests/home-responsive.mjs`

Expected: responsive checks PASS at all four widths.

- [ ] **Step 5: Commit**

```powershell
git add frontend/tests frontend/src/design-system
git commit -m "test(ui): verify responsive dashboard fidelity"
```

## Task 10: Publish Component Governance And Figma Mapping

**Files:**
- Create: `frontend/docs/study-ui/README.md`
- Create: `frontend/docs/study-ui/component-status.md`
- Create: `frontend/docs/study-ui/contributing.md`
- Modify component stories with final Figma references.

- [ ] **Step 1: Write the component-status table**

Include columns `Category`, `Component`, `Owner`, `Status`, `Unit Test`, `Story`, `Accessibility`, `Figma Node`, and `Code Import`. Every public export from `src/design-system/index.js` must have one row.

- [ ] **Step 2: Write the usage and contribution guide**

Document these rules explicitly:

```text
Applications import only from @study-ui.
Primitives do not access API clients or Pinia business stores.
Widgets emit identifiers and do not mutate caller-owned objects.
New public components require tests, stories, accessibility notes and tokens.
Raw colors are prohibited outside tokens.css and documented content assets.
Breaking prop or slot changes require a deprecation note before removal.
```

- [ ] **Step 3: Add Figma references to Storybook docs**

For each widget story, include the matching node from Task 6. For primitives created in Figma during implementation, record the exact Component Set node id; do not invent ids when a Figma component does not yet exist.

- [ ] **Step 4: Audit public exports against documentation**

Create `frontend/src/design-system/documentation.test.js`:

```js
import { readFile } from 'node:fs/promises'
import { describe, expect, it } from 'vitest'

describe('Study UI documentation coverage', () => {
  it('documents every public component export', async () => {
    const [entry, status] = await Promise.all([
      readFile(new URL('./index.js', import.meta.url), 'utf8'),
      readFile(new URL('../../docs/study-ui/component-status.md', import.meta.url), 'utf8'),
    ])
    const exports = [...entry.matchAll(/export \{ default as (Ui\w+|\w+Widget) \}/g)].map((match) => match[1])
    expect(exports.length).toBeGreaterThan(0)
    for (const name of exports) expect(status).toContain(`| ${name} |`)
  })
})
```

Run: `npm run test:unit -- src/design-system/documentation.test.js`

Expected: PASS with no undocumented exports.

- [ ] **Step 5: Run final acceptance**

Run:

```powershell
npm run verify:study-ui
node tests/home-responsive.mjs
```

Expected: all commands PASS. Manually verify keyboard focus order, visible focus rings, loading/error states, and the four responsive screenshots against Figma.

- [ ] **Step 6: Commit**

```powershell
git add frontend/docs/study-ui frontend/src/design-system frontend/tests
git commit -m "docs(ui): publish Study UI governance and mappings"
```

## Completion Evidence

The implementation is complete only when all of the following are present and current:

- `npm run verify:study-ui` passes.
- `node tests/home-responsive.mjs` passes at 1440, 1024, 768 and 390 widths.
- Storybook documents every public component with API, states, accessibility, tokens and design guidance.
- `component-status.md` covers every export from `@study-ui`.
- The homepage preserves its business actions while consuming Study UI components.
- Figma node mappings are recorded for the six homepage widgets and any created primitive Component Sets.
- Visual review finds no horizontal overflow, overlapping text, clipped controls or incoherent state colors.
