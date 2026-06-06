---
name: browser-extension-interaction
description: Study Hub 浏览器扩展侧边栏的交互设计原则和踩坑记录
metadata:
  type: experience
  project: study-hub
  component: extension/bing-assistant.js
---

# 浏览器扩展侧边栏交互设计

## 核心原则

### 1. 拖拽必须始终可用
- **不要**把拖拽和固定状态耦合
- 固定按钮只控制「松手后是否回到默认位置」
- `startDrag` 里**不能**有 `if (isPinned) return` 这种判断
- 正确做法：始终允许拖拽，固定状态只影响 `onDragEnd` 后的行为

### 2. 收起/展开布局逻辑
- 收起时 → 恢复页面原始布局（`marginRight = ''`）
- 展开时 → 给面板留空间（`marginRight = '360px'`）
- 逻辑写反会导致收起后页面被挤压，展开后布局不对

### 3. 事件委托处理动态内容
- 场景切换后 tabs 和 body 会重新渲染
- 用 `addEventListener` 逐个绑定 → 切换后事件丢失
- 改用事件委托：在父容器监听 `click`，`e.target.closest('.class')` 分发
- 动态内容不需要重新绑定事件

### 4. SPA 页面 URL 监听
- Bing 搜索用 `history.pushState` 做无刷新跳转
- 只监听 `popstate` 会漏掉大部分跳转
- 必须同时拦截 `pushState` 和 `replaceState`

```js
const origPush = history.pushState;
history.pushState = function(...args) {
  origPush.apply(this, args);
  setTimeout(onUrlChange, 50);
};
```

### 5. Shadow DOM 样式隔离
- 用独特类名前缀（如 `sh-*`）避免和宿主页面冲突
- 不要用 `!important` 过度，只在必要时用
- 外部 CSS 文件和内部内联样式不要重复定义

## 状态管理

| 状态 | 存储位置 | 说明 |
|------|---------|------|
| 面板位置 | `chrome.storage.local` | 拖拽后的坐标 |
| 收起/关闭 | `chrome.storage.local` | 刷新后恢复 |
| 来源勾选 | `chrome.storage.sync` | 跨设备同步 |
| 筛选状态 | `sessionStorage` | 页面刷新后恢复，5分钟过期 |

## 已修复的 Bug 记录

| Bug | 原因 | 修复 |
|-----|------|------|
| 拖拽不工作 | `startDrag` 里判断 `if (isPinned) return` | 移除判断，始终允许拖拽 |
| 收起后无法展开 | `adjustBing(!app.collapsed)` 逻辑反了 | 收起传 `false`，展开传 `true` |
| 场景切换按钮失效 | 重新渲染后事件绑定丢失 | 改用事件委托 |
| URL 变化检测不到 | 只监听 `popstate` | 拦截 `pushState`/`replaceState` |
| CSS 样式冲突 | 外部 CSS + 内联样式重复 | 统一用 Shadow DOM 内联样式 |
