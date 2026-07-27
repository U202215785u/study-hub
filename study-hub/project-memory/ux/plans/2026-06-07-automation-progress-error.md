# UX-R4-Automation-Progress-Error：Automation 解析进度与错误恢复小方案

最后更新：2026-06-07  
上一张任务卡：`study-hub/project-memory/ux/plans/2026-06-07-home-entry-feedback.md`  
关联总方案：`study-hub/project-memory/ux/体验稳定化与产品化总方案.md`  
关联 TODO：`study-hub/project-memory/ux/体验稳定化与产品化TODO总表.md`

---

## 1. 任务卡定位

本卡是高频主路径第三张任务卡。

Wiki 已完成 P1/P2 样板闭环，Home 已完成入口与反馈走查且无 P1 阻断。现在进入 Automation，因为它是 Study Hub 中最容易出现长任务、失败、外部依赖和用户焦虑的模块。

本卡目标：

```text
提交链接
  -> 创建任务
  -> 查看队列
  -> 理解进度
  -> 打开结果
  -> 失败时知道原因和下一步
```

本卡不做底层解析算法重构，优先建立体验走查、问题分级和错误恢复基线。

---

## 2. 当前状态摘要

### 2.1 已完成能力

- 三平台解析运行中：抖音、B站、小红书。
- 抖音 ASR 已迁移到火山引擎 BigModel ASR 极速版，支持 2h/100MB。
- `.env` 未配置火山引擎时可回退 DashScope + 55s 截断。
- 下载内容校验已加入，可识别 HTML/小文件/非视频内容。
- ffmpeg 已改为完整路径检测，不依赖进程 PATH。
- 启动依赖自检已加入。
- 重新解析流程已修复，旧文档保留到新任务成功后再删除。
- 任务队列支持批量提交和自动去重。
- Home 已有解析队列抽屉、统计看板、步骤条和空状态。
- 抖音收藏批量导入已接入浏览器插件和 Home textarea 批量提交。

### 2.2 已知问题

| 编号 | 问题 | 级别 | 来源 |
|---|---|---|---|
| ISS-006 | 任务队列 `_tasks` dict 只增不减 | P2 | automation/问题.md |
| ISS-008 | 小红书 HTML 解析依赖 `window.__INITIAL_STATE__` | P2 | automation/问题.md |
| UX-Automation-001 | Automation 尚未完成独立体验走查 | P1 | 本卡新增 |
| UX-Automation-002 | 批量任务部分成功/部分失败体验待验证 | P2 | 本卡新增 |
| UX-Automation-003 | 外部依赖缺失时用户恢复路径待验证 | P2 | 本卡新增 |

### 2.3 相关文件

前端：

- `study-hub/frontend/src/views/Home.vue`
- `study-hub/frontend/src/components/TaskStatusBadge.vue`
- `study-hub/extension/popup.html`
- `study-hub/extension/popup.js`
- `study-hub/extension/content.js`

后端：

- `study-hub/backend/endpoints/automation.py`
- `study-hub/backend/social_parsers.py`
- `study-hub/backend/endpoints/upload.py`

文档：

- `study-hub/project-memory/automation/状态.md`
- `study-hub/project-memory/automation/问题.md`
- `study-hub/project-memory/frontend/问题.md`
- `study-hub/project-memory/ux/问题追踪.md`
- `study-hub/project-memory/ux/体验稳定化与产品化TODO总表.md`

---

## 3. 核心用户路径

### 路径 1：单链接解析

用户目标：提交一个视频/图文链接，等待解析完成，并在知识库中看到结果。

步骤：

1. 用户进入 Home。
2. 用户找到自动化解析入口。
3. 用户选择平台或粘贴链接。
4. 用户提交任务。
5. 系统创建队列任务。
6. 用户查看任务进度。
7. 任务完成后，用户打开生成文档。

成功标准：

- 提交入口清楚。
- 任务创建后有立即反馈。
- 队列能说明当前步骤。
- 结果可直接打开。
- 文档列表刷新及时。

### 路径 2：批量解析

用户目标：一次提交多个链接，理解每个任务的状态。

步骤：

1. 用户展开批量输入。
2. 用户粘贴多行链接。
3. 用户提交批量任务。
4. 系统展示队列统计。
5. 用户查看每个任务的运行/完成/失败状态。
6. 用户打开成功结果，理解失败原因。

成功标准：

- 批量提交不会让用户以为页面卡死。
- 部分成功/部分失败可区分。
- 失败项有重试或复制诊断路径。

### 路径 3：重新解析

用户目标：对已有文档重新解析，并避免旧文档提前消失。

步骤：

1. 用户打开已有解析文档。
2. 用户点击重新解析。
3. 系统创建新任务。
4. 旧文档保留。
5. 新任务成功后替换旧文档。
6. 文档列表刷新。

成功标准：

- 重新解析期间旧文档不消失。
- 新任务失败时旧文档仍可用。
- 完成后结果可找到。

### 路径 4：失败恢复

用户目标：解析失败后知道为什么失败，以及下一步该怎么做。

失败类型：

- 链接无效。
- 下载返回 HTML。
- ffmpeg 缺失。
- ASR key 未配置。
- ASR 文件过大或模型限制。
- 小红书结构变化。
- 网络超时。

成功标准：

- 错误文案不是裸异常。
- 用户知道是否可重试。
- 用户知道是否需要补依赖或换链接。
- 诊断信息可以复制。

---

## 4. 本轮范围

### 4.1 必须完成

- [ ] 定义 Automation 四条核心路径。
- [ ] 创建 `ux/scripts/automation-体验测试.md`。
- [ ] 执行 Automation 首次体验走查。
- [ ] 输出 `ux/reports/automation-体验报告-20260607.md`。
- [ ] 验证单链接提交、队列进度、结果打开。
- [ ] 验证批量提交和队列统计。
- [ ] 验证重新解析不会让旧文档提前消失。
- [ ] 验证失败任务是否有可理解错误。
- [ ] 将发现问题写入 `ux/问题追踪.md`。

### 4.2 尽量完成

- [ ] 验证抖音、B站、小红书三平台各一条路径。
- [ ] 验证火山 ASR 未配置时的回退提示。
- [ ] 验证 ffmpeg 依赖自检提示。
- [ ] 验证批量任务部分成功/部分失败。
- [ ] 判断是否需要创建 Automation P1 修复卡。

### 4.3 本轮不做

- 不修 `_tasks` dict 长期增长。
- 不实现小红书 fallback。
- 不重构 ASR 架构。
- 不重做 Home 页面 UI。
- 不接入新的平台解析。

---

## 5. 体验设计要求

### 5.1 状态反馈

任务状态必须分清：

```text
pending -> running -> success / error
```

步骤状态必须分清：

```text
extract_meta -> download/audio -> asr -> summarize -> import
```

如果某平台步骤不同，可以用平台专属名称，但用户必须知道当前卡在哪。

### 5.2 错误恢复

错误状态至少包含：

- 发生了什么。
- 可能原因。
- 用户下一步。
- 是否可重试。
- 是否可复制诊断信息。

示例：

```text
视频下载失败
可能是链接已失效，或平台返回了登录/验证码页面。
[重试] [复制诊断] [查看原链接]
```

### 5.3 批量任务

批量任务至少展示：

- 总数。
- 运行中。
- 成功。
- 失败。
- 可打开结果。
- 失败项可单独查看。

### 5.4 长任务心理预期

长视频 ASR 可能耗时较久，必须让用户知道：

- 已进入 ASR。
- 预计需要等待。
- 页面可以继续使用。
- 完成后会刷新或可在队列中查看。

---

## 6. 边界测试

| 场景 | 操作 | 预期 |
|---|---|---|
| 空输入 | 提交空链接 | 不创建任务，提示输入链接 |
| 无效链接 | 提交非链接文本 | 提示格式错误 |
| 抖音口令 | 粘贴含短链口令 | 能提取链接或提示重新复制 |
| 批量链接 | 粘贴多行链接 | 创建多个任务并显示统计 |
| 重复链接 | 连续提交同一链接 | 去重或提示重复 |
| 下载 HTML | 平台返回 HTML | 提示链接/登录/验证码问题 |
| ffmpeg 缺失 | 模拟依赖不可用 | 显示依赖缺失提示 |
| ASR key 缺失 | 未配置 VOLC_* | 说明回退或提示配置 |
| 长视频 | 提交长视频 | 不截断或明确回退限制 |
| 小红书改版 | 解析失败 | 显示平台结构变化可能原因 |
| 重新解析失败 | 新任务失败 | 旧文档仍保留 |
| 队列为空 | 打开队列抽屉 | 显示友好空状态 |

---

## 7. 验证清单

### 7.1 命令验证

- [ ] 后端启动：使用项目启动脚本。
- [ ] 后端测试：按当前可用 Python 环境运行 `backend/tests/test_main.py`。
- [ ] 前端构建：`cd study-hub/frontend && npm run build`。

### 7.2 浏览器验证

- [ ] 打开 Home。
- [ ] 找到自动化解析入口。
- [ ] 提交单链接。
- [ ] 提交批量链接。
- [ ] 打开队列抽屉。
- [ ] 查看运行中任务。
- [ ] 查看完成任务。
- [ ] 查看失败任务。
- [ ] 打开生成文档。
- [ ] 触发重新解析。
- [ ] 验证旧文档保留。
- [ ] 390px / 768px / 1280px 视口检查队列抽屉。

### 7.3 文档验证

- [ ] 更新 `ux/问题追踪.md` Automation 区。
- [ ] 更新 `automation/问题.md` 中确认的问题状态。
- [ ] 更新 `automation/状态.md` 最近走查结果。
- [ ] 更新 `体验稳定化与产品化TODO总表.md` Automation 相关勾选。
- [ ] 如果沉淀长任务规则，更新 `ui/状态.md`。

---

## 8. 任务拆分

### Task 1：现状复核

- [x] 读取 `Home.vue` 自动化解析相关代码。
- [x] 读取 `TaskStatusBadge.vue`。
- [x] 读取 `automation.py` 队列、状态、错误返回逻辑。
- [x] 读取 `automation/状态.md` 和 `automation/问题.md`。

### Task 2：体验测试脚本

- [x] 创建 `ux/scripts/automation-体验测试.md`。
- [x] 写入单链接、批量、重新解析、失败恢复四条路径。
- [x] 写入边界测试矩阵。

### Task 3：首次走查

- [x] 启动前后端。
- [x] 执行单链接解析路径（含空输入、无效链接）。
- [x] 执行批量解析路径（展开/收起）。
- [x] 执行队列抽屉路径。
- [x] 执行失败场景（无效链接→B站解析失败）。
- [x] 输出 `ux/reports/automation-体验报告-20260607.md`。

### Task 4：问题分级

- [x] 将发现问题分为 P1/P2/P3（无 P1，3 个 P2，2 个 P3）。
- [x] 判断无核心路径阻断。
- [x] 将问题写入 `ux/问题追踪.md`。
- [x] 工程问题状态同步。

### Task 5：下一步决策

- [ ] ~~如果有 P1，创建 `2026-06-07-automation-p1-fixes.md`。~~ 无 P1，不走此分支。
- [x] 建议创建 `2026-06-07-automation-error-polish.md` 修复 P2 错误恢复缺口。
- [x] 长任务反馈规则已记录（空校验 + 完整错误 + 恢复操作）。

---

## 9. 完成标准

- [x] Automation 四条核心路径已定义。
- [x] `ux/scripts/automation-体验测试.md` 已创建。
- [x] Automation 首次体验走查完成。
- [x] `ux/reports/automation-体验报告-20260607.md` 已输出。
- [x] Automation 活跃问题已写入 `ux/问题追踪.md`。
- [x] 已明确无需 Automation P1 修复卡（无 P1 阻断）。
- [x] P2 错误恢复缺口已记录，建议创建 error-polish 卡或并入 UI Feedback Components。

---

## 10. 下一步

本卡完成后有三种可能：

1. 如果 Automation 有 P1 阻断：创建 `2026-06-07-automation-p1-fixes.md`。
2. 如果 Automation 无 P1 但错误恢复有 P2：创建 `2026-06-07-automation-error-polish.md`。
3. 如果 Automation 路径稳定：进入 `2026-06-07-journal-record-review.md`。

推荐默认路线：

```text
Automation 走查 -> Automation P1/P2 判断 -> Journal 第一轮
```

