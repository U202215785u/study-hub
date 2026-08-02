# Study UI 组件目录

Study UI 把 Figma 首页语言整理为可复用的内部组件。Storybook 是组件说明和状态验收入口，不承载第二套首页实现。

## 分类

- 通用：按钮、图标按钮和通用标题。
- 导航：胶囊导航与页面问候。
- 数据录入：输入框与选择器。
- 数据展示：标签、状态、进度和组件框架。
- 反馈：加载、空状态和错误状态。
- 布局：工作台外壳、八列网格、模块容器和首页编辑器。
- Study Hub Widgets：工作热力、日历日程、今日任务、自动化队列、知识库、手账、快捷指令、创作入口和快捷工作流。

## 依赖方向

```text
Foundations -> Primitives -> Patterns -> Widgets -> Pages
```

页面负责真实数据、路由和副作用；组件只接收数据并抛出标识。公共组件从 `@study-ui` 导入，每个组件都必须有测试、Storybook 页面、可访问性说明和 Figma 映射记录。

完整维护规则位于 `docs/study-ui/README.md` 和 `docs/study-ui/contributing.md`。
