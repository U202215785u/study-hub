# 首页动效状态

更新时间：2026-08-04

首页 Study UI 动效已完成并通过用户审核，对应任务 `STUDYHUB-8` 已完成。

当前首页动效包括：

- GSAP 管理的首页入场和 Bento FLIP 布局变化。
- CSS Transition 管理卡片四态、弹层、抽屉、编辑器和 Toast。
- 导航、日历、记忆卡片和创建入口的短时微交互。
- reduced-motion 降级、键盘 Tab 循环、Esc 关闭和焦点恢复。

验收基线：57 个 Vitest 文件、131 项通过；生产构建、Storybook 构建、动画体积门禁和四组首页 Playwright 验收全部通过。动画 chunk gzip 为 36,623 bytes。

边界：其他页面的交互组件尚未完成全站统一迁移。

