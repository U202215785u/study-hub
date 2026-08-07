# Today Task Category Stack Design

## Goal

Replace the home dashboard's static today-task panel with a three-card category stack. Users can manage categories, assign every DDL task to a category, and switch the visible category by dragging or clicking the stack.

## Data model and migration

- Add a `ddl_categories` table with an immutable `id`, unique non-empty `name`, `sort_order`, and `is_system` flag.
- Seed the existing task types as the initial categories: `待办`, `学习任务`, and `里程碑`, plus a protected `未分类` category.
- Add nullable `category_id` to `ddl_tasks`, backfill it from the legacy `task_type`, and retain `task_type` during this change for backward compatibility with existing task views and integrations.
- New and edited tasks persist `category_id`. A task with no category is displayed and managed as `未分类`.

## Category management

- The DDL page provides a category manager for creating, renaming, sorting, and deleting categories.
- Names must be trimmed, non-empty, and unique after trimming.
- Reordering persists the order used on the home stack and in DDL controls.
- `未分类` cannot be renamed or deleted.
- Deleting a category reassigns all of its tasks to `未分类` atomically before removing it.

## Home card stack

- The widget loads categories and today's tasks. It displays the first three categories by saved order; `未分类` fills empty slots when fewer than three user categories exist.
- The front card shows the selected category name, completed/total count, and up to four tasks scheduled for today in that category. Empty categories retain the existing empty state.
- Two subsequent category cards remain visibly offset behind the front card. Clicking either exposed card brings it forward.
- A horizontal pointer drag moves the front card with the pointer and reveals the next or previous card. Releasing after the threshold rotates the category to the front; otherwise the card returns to its origin. Vertical movement keeps normal page scrolling.
- Arrow keys rotate the focused stack. The interaction exposes labels and state through buttons and live text rather than relying only on the visual stack. Reduced-motion mode performs an immediate state change with no following animation.

## Create task flow

- Each front card contains an `建立任务` action.
- The action routes to `/ddl` with an explicit create intent, target category, and today's plan date.
- DDL consumes this intent once, opens its existing add-task modal, preselects the category, and uses today as the daily plan date.

## Error handling

- If category loading fails, the widget retains a usable `未分类` card and existing task rendering instead of becoming non-interactive.
- Category mutations report failures without discarding the user's current list or task form state.
- A category selected by an old URL intent falls back to `未分类` when it no longer exists.

## Verification

- Backend tests cover category CRUD, unique names, sorted reads, protected `未分类`, deletion reassignment, and task create/update/category filtering.
- Frontend tests cover the DDL category manager, task form selection, URL-driven creation defaults, three-card rendering, click/drag/keyboard switching, and reduced-motion behavior.
- Existing home and DDL tests remain green; a manual browser check validates drag threshold, click targets, and responsive layout.
