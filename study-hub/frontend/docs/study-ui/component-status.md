# Study UI Component Status

`Owner` identifies the maintenance boundary. `Figma Node` is intentionally blank when no Figma Component Set was created; source-frame references are not presented as component ids.

| Category | Component | Owner | Status | Unit Test | Story | Accessibility | Figma Node | Code Import |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| General | UiButton | Study UI | Stable 0.1 | Yes | Yes | Native button, focus ring, loading and disabled guard | — | `import { UiButton } from '@study-ui'` |
| General | UiIconButton | Study UI | Stable 0.1 | Yes | Yes | Required accessible label and tooltip | — | `import { UiIconButton } from '@study-ui'` |
| General | UiPillButton | Study UI | Candidate 0.2 | Yes | Yes | Native pressed button semantics and disabled guard | Homepage frame extraction | `import { UiPillButton } from '@study-ui'` |
| Data entry | UiInput | Study UI | Stable 0.1 | Yes | Yes | Visible label, described error, native focus | — | `import { UiInput } from '@study-ui'` |
| Data entry | UiSelect | Study UI | Stable 0.1 | Yes | Yes | Visible label, native options and error relation | — | `import { UiSelect } from '@study-ui'` |
| Data display | UiTag | Study UI | Stable 0.1 | Yes | Yes | Content tone does not imply status | — | `import { UiTag } from '@study-ui'` |
| Data display | UiBadge | Study UI | Stable 0.1 | Yes | Yes | Status dot always has a text label | — | `import { UiBadge } from '@study-ui'` |
| Data display | UiProgress | Study UI | Stable 0.1 | Yes | Yes | Progressbar role and clamped numeric value | — | `import { UiProgress } from '@study-ui'` |
| Data display | UiCompactHeader | Study UI | Candidate 0.2 | Yes | Yes | Configurable native heading level and separate action region | Homepage frame extraction | `import { UiCompactHeader } from '@study-ui'` |
| Data display | UiInsetSurface | Study UI | Candidate 0.2 | Yes | Yes | Visual container leaves semantics to slotted native controls | Homepage frame extraction | `import { UiInsetSurface } from '@study-ui'` |
| Feedback | UiSpinner | Study UI | Stable 0.1 | Yes | Yes | Status role and visually hidden loading text | — | `import { UiSpinner } from '@study-ui'` |
| Feedback | UiEmpty | Study UI | Stable 0.1 | Yes | Yes | Labeled region and optional action | — | `import { UiEmpty } from '@study-ui'` |
| Pattern | UiPanelHeader | Study UI | Stable 0.1 | Yes | Yes | Stable heading and action region | — | `import { UiPanelHeader } from '@study-ui'` |
| Pattern | UiWidgetFrame | Study UI | Stable 0.1 | Yes | Yes | One labeled state at a time | `349:96` source frame | `import { UiWidgetFrame } from '@study-ui'` |
| Layout | UiDashboardGrid | Study UI | Stable 0.1 | Yes | Yes | Reading-order DOM with responsive visual grid | `349:96` source frame | `import { UiDashboardGrid } from '@study-ui'` |
| Layout | UiDashboardItem | Study UI | Stable 0.1 | Yes | Yes | Logical span does not alter content semantics | `349:96` source frame | `import { UiDashboardItem } from '@study-ui'` |
| Layout | UiAppShell | Study UI | Stable 0.1 | Yes | Yes | One main landmark; navigation supplied by NavBar | `349:96` source frame | `import { UiAppShell } from '@study-ui'` |
| Layout | WorkbenchFrame | Study UI | Candidate 0.2 | Yes | Yes | One main landmark and constrained PC workspace | `349:96` | `import { WorkbenchFrame } from '@study-ui'` |
| Pattern | MotionWrapper | Study UI | Candidate 0.2 | Yes | Yes | Decorative motion wrapper; preserves attrs and has reduced-motion final state | `349:96` | `import { MotionWrapper } from '@study-ui'` |
| Navigation | CapsuleNavigation | Study UI | Candidate 0.2 | Yes | Yes | Named primary navigation, search, notification, and edit actions | `349:98` | `import { CapsuleNavigation } from '@study-ui'` |
| Layout | GreetingBar | Study UI | Candidate 0.2 | Yes | Yes | One page heading with live date and time | `349:127` | `import { GreetingBar } from '@study-ui'` |
| Layout | BentoDashboardGrid | Study UI | Candidate 0.2 | Yes | Yes | Eight-column DOM order with constrained spans | `349:96` | `import { BentoDashboardGrid } from '@study-ui'` |
| Layout | DashboardEditor | Study UI | Candidate 0.2 | Yes | Yes | Named edit actions, drag handle, save and cancel | `349:98` | `import { DashboardEditor } from '@study-ui'` |
| Pattern | DashboardModuleCard | Study UI | Candidate 0.2 | Yes | Yes | Stable content, loading, empty and error boundary | `349:96` | `import { DashboardModuleCard } from '@study-ui'` |
| Pattern | BentoBackground | Study UI | Candidate 0.2 | Yes | Yes | Decorative background only; aria-hidden and non-interactive | `349:96` | `import { BentoBackground } from '@study-ui'` |
| Study Hub widget | TaskWidget | Study Hub | Stable 0.1 | Yes | Yes | Keyboard-selectable rows and text status | `349:405` | `import { TaskWidget } from '@study-ui'` |
| Study Hub widget | CalendarWidget | Study Hub | Stable 0.1 | Yes | Yes | Grid label, named dates and pressed selection | `349:516` | `import { CalendarWidget } from '@study-ui'` |
| Study Hub widget | WorkHeatmapWidget | Study Hub | Candidate 0.2 | Yes | Yes | Labeled `img` role and fixed visible-cell capacity | `349:169` | `import { WorkHeatmapWidget } from '@study-ui'` |
| Study Hub widget | CalendarAgendaWidget | Study Hub | Candidate 0.2 | Yes | Yes | Named date-button group and agenda actions | `349:516` | `import { CalendarAgendaWidget } from '@study-ui'` |
| Study Hub widget | TodayFocusWidget | Study Hub | Candidate 0.2 | Yes | Yes | Named task buttons and visible status | `349:405` | `import { TodayFocusWidget } from '@study-ui'` |
| Study Hub widget | AutomationQueueWidget | Study Hub | Stable 0.1 | Yes | Yes | Title opens the full content parser; keyboard-open rows, named retry action and progress | `349:369` | `import { AutomationQueueWidget } from '@study-ui'` |
| Study Hub widget | KnowledgeWidget | Study Hub | Stable 0.1 | Yes | Yes | Native document buttons and text status | `349:471` | `import { KnowledgeWidget } from '@study-ui'` |
| Study Hub widget | DailyMemoryWidget | Study Hub | Candidate 0.2 | Yes | Yes | Native button opens daily review | `349:484` | `import { DailyMemoryWidget } from '@study-ui'` |
| Study Hub widget | QuickCommandWidget | Study Hub | Candidate 0.2 | Yes | Yes | Native command buttons with capped capacity | `349:510` | `import { QuickCommandWidget } from '@study-ui'` |
| Study Hub widget | CreationWidget | Study Hub | Stable 0.1 | Yes | Yes | Native work-item buttons and image alternatives | `349:493` | `import { CreationWidget } from '@study-ui'` |
| Study Hub widget | WorkflowWidget | Study Hub | Stable 0.1 | Yes | Yes | Ordered steps and named run controls | `349:459` | `import { WorkflowWidget } from '@study-ui'` |
