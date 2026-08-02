# Study UI

Study UI is the internal Vue 3 design system for Study Hub. It translates the Figma dashboard language into stable components, interaction contracts, responsive patterns, and documented domain widgets. Ant Design is the reference for component productization and documentation depth; Study UI keeps its own visual language and does not copy Ant Design's appearance.

## Design Language

Study UI is a quiet, dense working surface. Neutral canvas and surface layers carry most of the interface; lime is reserved for primary actions and active progress. Purple and orange identify content families, while success, warning, danger, and info remain independent status semantics.

The runtime source of truth is `src/design-system/foundations/tokens.css`. Components consume semantic `--ui-*` variables and do not own raw visual values.

## Component Taxonomy

| Category | Purpose | Components |
| --- | --- | --- |
| Foundations | Color, type, spacing, radius, motion and breakpoints | `semanticTokens`, CSS custom properties |
| General | Repeated commands and icon-only commands | `UiButton`, `UiIconButton` |
| Data entry | Labeled native form controls | `UiInput`, `UiSelect` |
| Data display | Content labels, status, quantitative progress | `UiTag`, `UiBadge`, `UiProgress` |
| Feedback | Loading and empty states | `UiSpinner`, `UiEmpty` |
| Navigation | Primary navigation, search entry and live greeting | `CapsuleNavigation`, `GreetingBar` |
| Patterns | Reusable composition and responsive structure | `UiPanelHeader`, `UiWidgetFrame`, `DashboardModuleCard` |
| Layout | Application shells, fixed-format grids and module editing | `UiDashboardGrid`, `UiDashboardItem`, `UiAppShell`, `WorkbenchFrame`, `BentoDashboardGrid`, `DashboardEditor` |
| Study Hub widgets | Serializable homepage domain views | `WorkHeatmapWidget`, `CalendarAgendaWidget`, `TodayFocusWidget`, `AutomationQueueWidget`, `KnowledgeWidget`, `DailyMemoryWidget`, `QuickCommandWidget`, `CreationWidget`, `WorkflowWidget` |

## Atomic Dependency Model

```text
Foundations -> Primitives -> Patterns -> Widgets -> Pages
```

- Foundations carry visual decisions and no component behavior.
- Primitives wrap native semantics and expose small, stable APIs.
- Patterns own composition, state precedence and responsive layout.
- Widgets accept serializable domain data and emit identifiers.
- Pages own API calls, stores, routing, dialogs and workflow orchestration.

Dependencies only point to the left. A primitive cannot import a widget or access page state.

## Usage

Applications import from the stable entry point only:

```js
import { UiButton, UiInput, TaskWidget } from '@study-ui'
```

Run the component catalog and verification suite from `frontend`:

```powershell
npm run storybook
npm run verify:study-ui
node tests/home-responsive.mjs
```

Storybook groups components by 通用、导航、数据录入、数据展示、反馈、布局 and Study Hub Widgets. Each public component has its own catalog entry with applicable states and fixed-capacity examples. Widget stories also carry the exact Figma source node.

## Documentation Contract

Each public component must document:

1. Definition and appropriate use.
2. Props, events and slots.
3. Default, loading, disabled, error, empty and long-content states where applicable.
4. Keyboard, focus and accessible-name behavior.
5. Semantic tokens used by the component.
6. Exact Figma node when one exists; otherwise it remains explicitly unmapped.

See [component-status.md](./component-status.md) for current coverage and [contributing.md](./contributing.md) for change rules.
