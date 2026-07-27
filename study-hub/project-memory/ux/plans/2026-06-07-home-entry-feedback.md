# UX-R3-Home-Entry-Feedback：Home 高频入口与状态反馈小方案

最后更新：2026-06-07  
上一阶段样板：`study-hub/project-memory/ux/plans/2026-06-07-wiki-core-path.md`、`study-hub/project-memory/ux/plans/2026-06-07-wiki-p2-polish.md`  
关联总方案：`study-hub/project-memory/ux/体验稳定化与产品化总方案.md`  
关联 TODO：`study-hub/project-memory/ux/体验稳定化与产品化TODO总表.md`

---

## 1. 任务卡定位

本卡是 Wiki 样板闭环后的第一张复制卡。

目标：把 Wiki 中已经跑通的“路径定义 -> 问题分级 -> 修复验证 -> 文档同步”方法复制到 Home 首页。

Home 是 Study Hub 的入口工作台，承担：

- 搜索与常用启动器
- 最近文档
- 自动化解析入口
- 解析队列状态
- 知识库入口
- AI / Skill / Workflow 等模块跳转

本卡不做横屏 Dashboard 大改版，只做当前 Home 的入口清晰度、操作反馈和错误/空状态稳定化，为后续 UI 大改保留功能路径基线。

---

## 2. 当前状态摘要

### 2.1 已完成能力

- Home 已支持常用网站和 AI 启动器。
- 常用网站和 AI 启动器已支持删除。
- 知识库最近文档已支持预览、复制、删除。
- 知识库文档列表已支持排序。
- 自动化解析队列已有全局抽屉面板和步骤进度。
- 重新解析后队列任务详情空白 + 文档列表不刷新问题已修复。

### 2.2 已知问题

| 编号 | 问题 | 级别 | 来源 |
|---|---|---|---|
| ISS-004 | Toast 组件在 Brainstorm.vue 和 Home.vue 中重复实现 | P2 | frontend/问题.md |
| ISS-005 | accent 色 `#7c8aff` 及变体硬编码在多个 Vue 文件 | P2 | frontend/问题.md |
| ISS-021 | apiBase 硬编码 `http://localhost:8741` | P1 | frontend/问题.md |
| UX-Home-001 | 首页核心入口尚未完成体验走查 | P1 | 本卡新增 |
| UX-Home-002 | Home 空/错/加载状态未形成统一基线 | P2 | 本卡新增 |

### 2.3 相关文件

前端：

- `study-hub/frontend/src/views/Home.vue`
- `study-hub/frontend/src/stores/settings.js`
- `study-hub/frontend/src/components/TaskStatusBadge.vue`
- `study-hub/frontend/src/components/Toast.vue`
- `study-hub/frontend/src/components/SystemStatus.vue`

后端：

- `study-hub/backend/endpoints/upload.py`
- `study-hub/backend/endpoints/automation.py`
- `study-hub/backend/endpoints/categories.py`
- `study-hub/backend/endpoints/admin.py`

文档：

- `study-hub/project-memory/frontend/问题.md`
- `study-hub/project-memory/ux/问题追踪.md`
- `study-hub/project-memory/ux/体验稳定化与产品化TODO总表.md`
- `study-hub/project-memory/ui/横屏工作台Dashboard框架图.md`

---

## 3. 核心用户路径

### 路径 1：搜索与启动

用户目标：从 Home 快速进入搜索、常用网站、AI 工具或内部模块。

步骤：

1. 用户进入 `/`。
2. 用户使用搜索框或搜索模式。
3. 用户点击常用网站或 AI 启动器。
4. 系统打开目标或跳转内部模块。
5. 用户能返回 Home 或继续使用。

成功标准：

- 搜索入口明确。
- 搜索模式可理解。
- 启动器点击区域和删除按钮不会互相干扰。
- 外部打开失败时有提示。

### 路径 2：最近文档操作

用户目标：在 Home 上快速处理最近文档。

步骤：

1. 用户进入 Home。
2. 用户查看最近文档。
3. 用户选择排序方式。
4. 用户预览、复制或删除文档。
5. 系统给出明确反馈，并刷新列表。

成功标准：

- 文档操作按钮含义清楚。
- 删除有确认或撤销策略。
- 复制有成功/失败反馈。
- API 返回错误时不出现空白弹窗。

### 路径 3：自动化解析与队列

用户目标：提交链接解析，并理解任务当前状态。

步骤：

1. 用户在 Home 找到解析入口。
2. 用户提交单个或批量链接。
3. 系统创建队列任务。
4. 用户打开队列抽屉查看进度。
5. 任务完成后，用户打开结果文档。

成功标准：

- 提交后有任务创建反馈。
- 队列能说明运行中、完成、失败。
- 失败时有原因和下一步。
- 完成后文档列表刷新。

### 路径 4：系统状态与恢复

用户目标：当后端、API 或扩展异常时，知道系统发生了什么。

步骤：

1. 用户进入 Home。
2. 后端不可用、API 返回错误或队列失败。
3. Home 展示错误状态。
4. 用户能重试、复制诊断或查看系统状态。

成功标准：

- 不出现静默失败。
- 错误文案用户可理解。
- 有明确下一步：重试、刷新、查看状态。

---

## 4. 本轮范围

### 4.1 必须完成

- [ ] 定义 Home 四条核心路径。
- [ ] 执行 Home 首次体验走查。
- [ ] 新增或更新 `ux/scripts/home-体验测试.md`。
- [ ] 输出 `ux/reports/home-体验报告-20260607.md`。
- [ ] 确认常用网站和 AI 启动器删除路径无误触。
- [ ] 确认最近文档预览/复制/删除/排序路径。
- [ ] 确认解析队列抽屉能解释任务状态。
- [ ] 确认 apiBase 硬编码对 Home 的影响范围。

### 4.2 尽量完成

- [ ] 梳理 Home 与 Brainstorm 的 Toast 重复点。
- [ ] 梳理 Home 中可复用的 Empty/Error/Loading 模式。
- [ ] 记录后续横屏 Dashboard 改版时 Home 的功能路径基线。

### 4.3 本轮不做

- 不做 Home 横屏 Dashboard 大改版。
- 不做全局 Toast 组件抽取实现。
- 不做 apiBase 配置化实现。
- 不做自动化解析底层逻辑改造。
- 不做视觉重设计。

---

## 5. 体验设计要求

### 5.1 入口可发现性

- 搜索、最近文档、自动化解析、常用启动器必须是首屏可理解的入口。
- 删除/编辑类操作不能比主打开操作更抢眼。
- 外部跳转和内部跳转应有视觉区分。

### 5.2 状态反馈

Loading：

- 文档加载、解析提交、队列刷新、删除操作需要 loading 或禁用态。

Success：

- 复制成功、删除成功、任务创建成功需要明确反馈。

Error：

- 文档不存在、API 错误、后端不可用、解析失败都需要可理解提示。

Empty：

- 无最近文档、无启动器、无队列任务时需要引导性空状态。

### 5.3 防错

- 删除启动器和文档需要确认或撤销策略。
- 提交解析时避免重复点击。
- 文档 API 返回 `error` 时不能打开空白弹窗。

### 5.4 后续 UI 大改约束

Home 将来可以改成横屏工作台 Dashboard，但必须保留这些功能路径：

- 全局搜索/命令入口
- 最近文档入口
- 解析入口与队列状态
- 常用启动器
- 系统状态
- 继续学习/继续创作入口

---

## 6. 边界测试

| 场景 | 操作 | 预期 |
|---|---|---|
| 无最近文档 | 打开 Home | 显示空状态和上传/解析引导 |
| 后端不可用 | 打开 Home 或加载文档 | 显示错误状态，不空白 |
| 文档不存在 | 点击已删除文档 | 显示错误提示，不出现空白弹窗 |
| 复制失败 | 浏览器拒绝剪贴板 | 显示失败提示 |
| 删除取消 | 点击删除后取消 | 数据不变 |
| 删除确认 | 点击删除并确认 | 列表刷新 |
| 重复提交解析 | 快速点击提交 | 不创建重复任务或有禁用态 |
| 队列失败任务 | 打开队列抽屉 | 显示失败原因和下一步 |
| 启动器删除 | 删除 AI 启动器 | 不触发外部跳转 |
| 移动端 390px | 打开 Home | 卡片不溢出，操作按钮可点 |

---

## 7. 验证清单

### 7.1 命令验证

- [ ] 前端构建：`cd study-hub/frontend && npm run build`
- [ ] 后端基础测试：按当前可用 Python 环境运行 `backend/tests/test_main.py`

### 7.2 浏览器验证

- [ ] 打开 `/`
- [ ] 使用搜索入口
- [ ] 点击常用网站
- [ ] 点击 AI 启动器
- [ ] 删除常用网站
- [ ] 删除 AI 启动器
- [ ] 查看最近文档
- [ ] 切换排序
- [ ] 预览文档
- [ ] 复制文档
- [ ] 删除文档
- [ ] 提交解析任务
- [ ] 打开队列抽屉
- [ ] 查看完成/失败任务
- [ ] 390px / 768px / 1280px 视口检查

### 7.3 文档验证

- [ ] 更新 `ux/问题追踪.md` Home 区。
- [ ] 更新 `frontend/问题.md` 中 Home 相关问题状态。
- [ ] 更新 `ux/状态.md` 当前阶段看板。
- [ ] 更新 `体验稳定化与产品化TODO总表.md` Home 相关勾选。
- [ ] 如果沉淀反馈规则，更新 `ui/状态.md`。

---

## 8. 任务拆分

### Task 1：现状复核

- [x] 读取 `Home.vue`。
- [x] 读取 `settings.js`。
- [x] 读取 `TaskStatusBadge.vue`。
- [x] 读取 `frontend/问题.md` 中 Home 相关问题。
- [x] 确认当前 Home 已完成和仍待确认的入口。

### Task 2：体验走查脚本

- [x] 创建 `ux/scripts/home-体验测试.md`。
- [x] 覆盖搜索/启动器/最近文档/解析队列/系统状态四条路径。
- [x] 加入空数据、错误、重复点击、移动端场景。

### Task 3：首次走查

- [x] 启动前后端。
- [x] 按脚本执行核心路径。
- [x] 记录问题、截图或文字证据（6 张截图）。
- [x] 输出 `ux/reports/home-体验报告-20260607.md`。

### Task 4：问题分级

- [x] 将问题分为 P1/P2/P3（无 P1，3 个 P2，2 个 P3）。
- [x] 将问题写入 `ux/问题追踪.md`。
- [x] 前端工程问题状态同步到 `frontend/问题.md`。
- [x] 判断无需 Home P1 修复卡。

### Task 5：沉淀和下一步

- [x] 提炼 Home 可复用反馈模式（confirm + toast + 空状态）。
- [x] 标注 P2-001/P2-002 等待横屏 Dashboard 大改。
- [x] 决定下一张卡进入 Automation 第一轮。

---

## 9. 完成标准

- [x] Home 四条核心路径已定义。
- [x] `ux/scripts/home-体验测试.md` 已创建。
- [x] Home 首次体验走查完成。
- [x] `ux/reports/home-体验报告-20260607.md` 已输出。
- [x] Home 活跃问题已写入 `ux/问题追踪.md`。
- [x] 已明确无需 Home P1 修复卡（无 P1 阻断）。
- [x] 已明确 P2-001/P2-002 移动端问题等待 UI 大改时处理。

---

## 10. 下一步

本卡完成后有三种可能：

1. 如果 Home 有 P1 阻断：创建 `2026-06-07-home-p1-fixes.md`。
2. 如果 Home 无 P1 但 P2 明显：创建 `2026-06-07-home-feedback-polish.md`。
3. 如果 Home 路径稳定：进入 `2026-06-07-automation-progress-error.md`。

推荐默认路线：

```text
Home 走查 -> Home P1/P2 判断 -> Automation 第一轮
```

