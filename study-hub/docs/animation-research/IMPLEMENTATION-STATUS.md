# 首页动效实施状态

更新时间：2026-08-04

## 状态

首页动效方案已按 `FINAL-RECOMMENDATION.md` 实施，并经用户审核通过。任务板 `STUDYHUB-8` 已标记为 `done`。

## 已落地范围

- GSAP 3.15 本地 adapter 与生命周期清理，按 `prefers-reduced-motion` 分支执行。
- 首页导航、问候语和九个 Widget 的分层入场动画。
- Bento 卡片隐藏、恢复、重排和取消操作的 FLIP 过渡。
- DashboardModuleCard 的 `loading`、`error`、`empty`、`content` 四态过渡。
- 导航、日历、记忆卡片、创建入口和通用按钮的 token 化微交互。
- 搜索、复盘、文档、自动化弹层，解析队列和知识库抽屉，以及编辑器和 Toast 的过渡。
- Tab 循环、Esc 关闭和关闭后的焦点恢复。
- 紧凑视口下 footer 不拦截导航操作；验收脚本使用确定性的首页稳定条件。

## 验证记录

- `npm run test:unit`：57 个测试文件、131 项通过。
- `npm run build`：通过。
- `npm run build:storybook`：通过。
- `npm run test:animation-budget`：通过；`animations` chunk gzip 为 36,623 bytes，低于 46,080 bytes 门禁。
- `home-motion.mjs`：普通动效、reduced-motion、焦点恢复和编辑器操作通过。
- `home-responsive.mjs`：390、942、1440、1366、1920、2560 视口检查通过。
- `home-layout-persistence.mjs`：隐藏、恢复、取消和重排持久化检查通过。
- `home-visual-overlay.mjs`：Figma Widget 几何叠加检查通过。
- `git diff --check`：通过。

## 边界

本次范围只覆盖正式首页 Study UI。其他页面的 Toast、Modal/Drawer、表单和历史按钮仍可能存在独立实现，后续如需全站统一应建立新的迁移任务。

