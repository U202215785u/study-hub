# UX-R7-UI-Feedback-Components：统一反馈组件小方案

最后更新：2026-06-07  
上一阶段：五模块首轮走查全部完成（Wiki/Home/Automation/Journal/Search Assistant）  
关联总方案：`study-hub/project-memory/ux/体验稳定化与产品化总方案.md`  
关联 TODO：`study-hub/project-memory/ux/体验稳定化与产品化TODO总表.md`（§6.1）

---

## 1. 任务卡定位

五模块走查发现 16 个 P2，其中一半是同一个根因：**反馈组件各自手搓，没有统一规范**。

当前散落情况：

| 模式 | 散落数量 | 问题 |
|------|---------|------|
| `showToast()` | 本地定义在 **6 个文件** | Home/Brainstorm/SOP/CreatorHub/SkillMarket 各写各的 |
| `Toast.vue` | 被引用在 **4 个文件** | Wiki/WikiPage/SOP/SkillMarket 引用组件但 wrapper 不统一 |
| `confirm()` | **17 处**跨 8 个文件 | 原生弹窗，样式不一致，无法定制 |
| `alert()` | **12 处**跨 6 个文件 | 原生弹窗，阻断式，错误信息堆给用户 |
| 空输入校验 | **0 处** | Automation 提交空链接无任何反馈（UX-Auto-001） |
| 错误恢复操作 | **0 处** | 失败后无重试/复制诊断按钮（UX-Auto-003） |

本卡目标：**做一套三个统一组件，首批落地到 Home/Journal/Automation，替换 80% 的原生弹窗。**

---

## 2. 本轮范围

### 2.1 必须完成：三个统一组件

#### 组件 1：`AppToast`（统一轻提示）

- 替代所有本地 `showToast()` + `alert()` 调用。
- 支持成功/错误/信息三种类型。
- 支持自动消失（2.5s）和手动关闭。
- 支持底部居中（默认）和顶部居中两种位置。
- 通过 provide/inject 或 composable 全局可用。

覆盖的 P2：
- UX-Journal-003：保存失败用原生 alert → AppToast
- 全局 alert() 替换：Journal/Home/Workflow/LearningChecklist/WikiShareCard

#### 组件 2：`AppConfirm`（统一确认弹窗）

- 替代所有原生 `confirm()` 调用。
- 支持标题 + 描述 + 确认/取消按钮。
- 确认按钮支持危险样式（红色）。
- 通过 composable 或命令式调用（`useConfirm()`）。

覆盖的 P2：
- UX-Journal-002：删除用原生 confirm → AppConfirm
- 全局 confirm() 替换：Journal/Home/Wiki/WikiPage/SOP/SkillMarket/KnowledgeBase/LearningChecklist

#### 组件 3：输入校验模式

- 不为每个输入框写校验，而是建立约定：
  - 空输入 → 输入框红边框 + 下方红色提示文字 + Toast "请填写 XXX"
  - 格式错误 → 同上
- 首批落地到 Home 的自动化解析入口。

覆盖的 P2：
- UX-Auto-001：空输入提交无校验

### 2.2 尽量完成

- Automation 失败任务增加重试/复制诊断按钮（覆盖 UX-Auto-003）。
- Automation 错误信息从"失败"扩展为完整错误摘要（覆盖 UX-Auto-002）。
- Home 复制操作反馈确认（覆盖 UX-Home-003）。

### 2.3 本轮不做

- 不做 Loading 规范（留到下一张卡）。
- 不做 Empty State 规范（留到下一张卡）。
- 不做全局推广到所有模块（仅首批 Home/Journal/Automation）。
- 不做暗色模式适配。
- 不做键盘快捷键支持。
- 不做动画/过渡优化。

---

## 3. 组件设计

### 3.1 AppToast

```text
调用方式：toast.success('保存成功') / toast.error('保存失败') / toast.info('正在处理…')

位置：底部居中（fixed bottom-6 left-1/2 -translate-x-1/2）
类型：
  - success：绿色边框 + 绿色文字
  - error：红色边框 + 红色文字
  - info：默认边框 + 默认文字
时长：默认 2.5s，error 类型 4s
堆叠：同时多个 toast 向上堆叠，不覆盖
```

### 3.2 AppConfirm

```text
调用方式：confirm('确定要删除吗？', { title: '删除日记', danger: true })
       → Promise<boolean>

结构：
  - 半透明黑色遮罩
  - 居中白色卡片
  - 标题（可选，默认"确认操作"）
  - 描述文字
  - 两个按钮：取消（左侧）+ 确认（右侧，danger 时为红色）

行为：
  - 确认 → resolve(true)
  - 取消 / 点遮罩 / ESC → resolve(false)
  - 按钮有 loading 态（防止重复点击）
```

### 3.3 输入校验约定

```text
规则：
  - 必填字段为空时：边框变红 + 下方出现红色提示文字
  - 格式错误时：同上 + 提示正确格式
  - 提交时统一校验，不通过的不发请求

首批落地：Home 解析卡片输入框
  - 提交时检查输入是否为空
  - 空则 toast.error('请粘贴视频或图文分享链接') + 输入框红边框
```

---

## 4. 落地计划

### 4.1 第一批：Home 首页

替换内容：

| 位置 | 原来 | 改为 |
|------|------|------|
| `showToast()` 本地函数 | 30+ 处调用 | `useToast()` composable |
| 常用网站删除确认 | `confirm('确定删除…')` | `AppConfirm` |
| AI 服务删除确认 | `confirm('确定删除…')` | `AppConfirm` |
| 文档删除确认 | `confirm('确定要删除…')` | `AppConfirm` |
| 文档重新识别确认 | `confirm('重新识别…')` | `AppConfirm` |
| 解析提交空输入 | 无校验 | 红边框 + toast |
| API key 错误 | `alert(长文本)` | `toast.error(简洁版)` |

### 4.2 第二批：Journal 手账

替换内容：

| 位置 | 原来 | 改为 |
|------|------|------|
| 保存失败 | `alert(result.error)` | `toast.error('保存失败：' + msg)` |
| 删除确认 | `confirm('确定要删除…')` | `AppConfirm({ danger: true })` |
| 切换日期未保存 | `confirm('当前日记有未保存…')` | `AppConfirm({ title: '未保存的修改' })` |

### 4.3 第三批：Automation 解析

替换内容：

| 位置 | 原来 | 改为 |
|------|------|------|
| 空输入提交 | 无反馈 | 红边框 + toast |
| 失败任务展示 | 仅"失败" | 完整错误摘要 |
| 失败任务操作 | 无 | 重试 + 复制诊断按钮 |

---

## 5. 实现文件

### 5.1 新建文件

```
study-hub/frontend/src/components/AppToast.vue      ← 统一 Toast 组件
study-hub/frontend/src/components/AppConfirm.vue    ← 统一确认弹窗
study-hub/frontend/src/composables/useToast.js      ← Toast composable（全局单例）
study-hub/frontend/src/composables/useConfirm.js    ← Confirm composable（命令式调用）
```

### 5.2 修改文件（首批）

```
study-hub/frontend/src/views/Home.vue        ← showToast + confirm + alert → 新组件
study-hub/frontend/src/views/JournalView.vue ← alert + confirm → 新组件
study-hub/frontend/src/main.js               ← 注册全局 plugin（如需要）
```

### 5.3 后续推广（不在本轮）

```
Wiki.vue / WikiPage.vue / SOP.vue / SkillMarket.vue
KnowledgeBase.vue / LearningChecklist.vue / Workflow.vue
CreatorHub.vue / Brainstorm.vue
```

---

## 6. 任务拆分

### Task 1：创建 AppToast + useToast

- [x] 创建 `AppToast.vue`（支持 success/error/info）。
- [x] 创建 `useToast.js`（全局单例，支持堆叠）。
- [x] 在 `App.vue` 注册全局 Toast。
- [x] 验证多次调用不会创建重复实例。

### Task 2：创建 AppConfirm + useConfirm

- [x] 创建 `AppConfirm.vue`（标题 + 描述 + 确认/取消 + danger 样式）。
- [x] 创建 `useConfirm.js`（命令式调用，返回 Promise）。
- [x] 支持 ESC 关闭和点击遮罩关闭。
- [x] 验证确认/取消返回正确的 boolean。

### Task 3：Home 落地替换

- [x] 替换本地 `showToast()` 为 `toast.success/error/info()`。
- [x] 替换 4 处 `confirm()` 为 `useConfirm()`。
- [x] 替换 1 处 `alert()` 为 `toast.error()`。
- [x] 增加解析提交空输入校验（红边框 + toast）。

### Task 4：Journal 落地替换

- [x] 替换保存失败 `alert()` 为 `toast.error()`。
- [x] 替换删除确认 `confirm()` 为 `useConfirm({ danger: true })`。
- [x] 替换切换未保存确认 `confirm()` 为 `useConfirm({ title: '未保存的修改' })`。

### Task 5：Automation 错误恢复

- [x] 队列抽屉失败任务增加完整错误摘要（替换截断文本）。
- [x] 失败任务增加重试按钮。
- [x] 失败任务增加复制诊断信息按钮。

### Task 6：构建验证 + 视觉检查

- [~] `npm run build` — 环境内存不足中断，代码无语法错误，dev server 正常。
- [x] 浏览器验证 Toast 三种类型显示正常。
- [x] 浏览器验证 Confirm 弹窗（danger 样式）显示正常。
- [x] 浏览器验证空输入校验红边框 + toast。

---

## 7. 完成标准

- [x] `AppToast.vue` + `useToast.js` 已创建，三种类型可用。
- [x] `AppConfirm.vue` + `useConfirm.js` 已创建，正常/danger 样式可用。
- [x] Home 的 showToast/confirm/alert 全部替换完成。
- [x] Journal 的 alert/confirm 全部替换完成。
- [x] Automation 空输入校验已加入。
- [x] Automation 失败任务增加了错误摘要 + 重试 + 复制诊断。
- [~] `npm run build` — 环境内存限制中断，dev server 验证通过。
- [x] 浏览器核心交互验证通过。
- [x] 覆盖的 P2 在 `ux/问题追踪.md` 中标记状态。

---

## 8. 覆盖的 P2 清单一览

| 编号 | 问题 | 通过什么解决 |
|------|------|-------------|
| UX-Journal-002 | 删除用原生 confirm | AppConfirm |
| UX-Journal-003 | 保存失败用原生 alert | AppToast |
| UX-Auto-001 | 空输入无校验 | 输入校验约定 |
| UX-Auto-002 | 错误信息简略 | 失败任务完整摘要 |
| UX-Auto-003 | 失败无恢复操作 | 重试 + 复制诊断按钮 |
| UX-Home-003 | 复制反馈待确认 | AppToast |
| — | 全局 alert() 12 处 | AppToast（首批 Home+Journal） |
| — | 全局 confirm() 17 处 | AppConfirm（首批 Home+Journal） |

---

## 9. 下一步

本卡完成后：

1. **第一批模块全部闭环**：Wiki/Home/Automation/Journal 四个模块走查 + 修复完成。
2. **可选择**：
   - 推广 AppToast/AppConfirm 到剩余 6 个模块。
   - 进入能力模块走查（Workflow/DDL 等）。
   - 做 Loading/Empty State 规范（下一张 UI 卡）。
