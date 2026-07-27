# Study Hub 体验稳定化与产品化 TODO 总表

最后更新：2026-06-07  
关联总方案：`study-hub/project-memory/ux/体验稳定化与产品化总方案.md`  
关联执行方案：`study-hub/project-memory/ux/体验稳定化与产品化全量执行方案.md`  
用途：覆盖 Study Hub 全部功能模块、系统模块、设计系统和治理任务的阶段总 TODO

---

## 0. 使用规则

本 TODO 总表是体验稳定化与产品化阶段的总看板。

使用方式：

- 每次只选择一个模块或一个跨模块任务包进入小方案。
- 小方案必须落到 `study-hub/project-memory/ux/plans/`。
- 每个模块至少完成“盘点 -> 脚本 -> 走查 -> 小方案 -> 修复 -> 回归 -> 沉淀”闭环。
- P0/P1 可以插队；P2/P3 不抢核心路径稳定化资源。
- 勾选任务前必须有对应产物或验证记录。

状态标记：

- `[ ]` 未开始
- `[~]` 进行中
- `[x]` 已完成
- `[!]` 阻塞
- `[-]` 不做/已废弃

优先级：

- P0：系统不可用、数据风险、启动/构建失败
- P1：核心路径阻断
- P2：明显体验问题
- P3：增强、美化、扩展

---

## 1. L0 阶段治理 TODO

### 1.1 文档与看板

- [x] P1 建立体验稳定化与产品化总方案  
  输出：`ux/体验稳定化与产品化总方案.md`
- [x] P1 建立体验稳定化与产品化全量执行方案  
  输出：`ux/体验稳定化与产品化全量执行方案.md`
- [x] P1 创建 UX 小方案目录  
  输出：`ux/plans/README.md`
- [ ] P1 在 `ux/状态.md` 增加“体验稳定化看板”  
  输出：模块、阶段、小方案、走查、修复、回归、评分、状态表
- [ ] P1 初始化全模块体验评分基线表  
  输出：`ux/状态.md` 或 `ux/体验评分基线.md`
- [ ] P1 把本 TODO 总表加入 `ux/状态.md` 最近动作  
  输出：状态索引可追踪
- [ ] P2 给 `ux/问题追踪.md` 补真实统计总览  
  输出：按模块统计 P0/P1/P2/P3、已修复、遗留
- [ ] P2 建立 `ux/reports/README.md`  
  输出：报告命名、截图证据、回归记录规则
- [ ] P2 建立 `ux/scripts/README.md`  
  输出：脚本命名、执行方式、覆盖要求

### 1.2 阶段节奏

- [x] P1 确定第一轮样板模块：Wiki  
  输出：`ux/plans/2026-06-07-wiki-core-path.md`
- [x] P1 确定第一批高频模块执行顺序：Wiki -> Home -> Automation -> Journal -> Search Assistant  
  输出：`ux/状态.md` 看板
- [ ] P2 确定第二批能力模块执行顺序：Workflow -> DDL -> Skill Market -> Creator Hub -> SOP -> Learning -> Brainstorm  
  输出：`ux/状态.md` 看板
- [ ] P2 确定系统模块执行顺序：Backend -> Deploy -> Extension -> Electron -> Second Self -> Obsidian Bridge  
  输出：`ux/状态.md` 看板
- [ ] P2 建立每轮结束复盘模板  
  输出：`ux/回归记录模板.md` 或合并进报告模板

### 1.3 通用验证

- [ ] P1 明确前端构建验证命令  
  输出：`cd study-hub/frontend && npm run build`
- [ ] P1 明确后端测试验证命令  
  输出：根据当前 Python 环境记录可用命令
- [ ] P1 明确后端启动验证方式  
  输出：统一使用 `后台启动.bat` / `start-background.ps1`
- [ ] P2 明确浏览器验证方式  
  输出：本地 URL、视口尺寸、截图记录规范
- [ ] P2 明确边界测试数据构造方式  
  输出：空数据、长标题、长正文、网络失败、重复点击

---

## 2. L1 全量盘点 TODO

### 2.1 模块清单盘点

- [ ] P1 盘点前端路由页面  
  覆盖：Home、KnowledgeBase、Wiki、WikiPage、Brainstorm、Learning、LearningChecklist、LearningPlan、Workflow、DDL、SOP、CreatorHub、SkillMarket、Journal
- [ ] P1 盘点后端 endpoint  
  覆盖：admin、ai_search、automation、brainstorm、categories、creator、ddl、evolution、export、images、journal、links、operations、rag、review、second_self、skills、sop、upload、wiki、workflow
- [ ] P1 盘点浏览器扩展  
  覆盖：popup、background、bing-assistant、manifest、scene-rules
- [ ] P1 盘点 Electron  
  覆盖：main、preload、package、builder 配置、后端管理能力
- [ ] P1 盘点 second-self  
  覆盖：独立服务、StudyHub 集成入口、3D 前端、批量导入、记忆数据库
- [ ] P1 盘点项目记忆模块  
  覆盖：ai-memory-research、automation、backend、brainstorm、creator-hub、ddl、deploy、frontend、journal、learning、memory、obsidian-bridge、search-assistant、second-self、skill-market、ui、ux、wiki、workflow

### 2.2 核心路径盘点

- [x] P1 为所有高频模块写核心路径  
  覆盖：Wiki、Home、Automation、Journal、Search Assistant
- [ ] P2 为所有能力模块写核心路径  
  覆盖：Workflow、DDL、Skill Market、Creator Hub、SOP、Learning、Brainstorm、KnowledgeBase
- [ ] P2 为所有系统模块写核心路径  
  覆盖：Backend 启停、Deploy、Extension、Electron、Second Self、Obsidian Bridge
- [ ] P2 为废弃模块写验证路径  
  覆盖：Memory 废弃态、路由清理、后端清理、扩展清理

### 2.3 现有问题盘点

- [ ] P1 汇总 P0/P1 问题到 `ux/问题追踪.md`
- [ ] P1 汇总 frontend open 问题：Toast 重复、accent 硬编码、apiBase 硬编码
- [ ] P1 汇总 backend open 问题：API key、异常堆栈、CORS、PID/localhost、Python 环境
- [ ] P1 汇总 automation open 问题：任务字典清理、小红书 fallback
- [ ] P1 汇总 workflow open 问题：gate fail 策略、human 超时、retry 无限循环、嵌套 workflow
- [x] P1 汇总 search-assistant open 问题：扩展 reload、中文编码、动态规则、真实 AI 分析
- [ ] P2 汇总 deploy open 问题：python 重定向器、venv 污染、野进程、Docker 未验证
- [ ] P2 汇总 wiki open 问题：compiled_hashes 同步、超长文档、wikilink 存在性
- [ ] P2 汇总 ui open 问题：Toast、Modal/Drawer、按钮规范、表单验证

---

## 3. 高频主路径模块 TODO

## 3.1 Home 首页

相关文件：

- `frontend/src/views/Home.vue`
- `frontend/src/stores/settings.js`
- `frontend/src/components/TaskStatusBadge.vue`
- `backend/endpoints/upload.py`
- `backend/endpoints/automation.py`

### 盘点与脚本

- [x] P1 定义 Home 核心路径 1：打开首页 -> 搜索/启动常用工具 -> 返回
- [x] P1 定义 Home 核心路径 2：查看最近文档 -> 预览/复制/删除
- [x] P1 定义 Home 核心路径 3：提交解析任务 -> 查看队列 -> 打开结果
- [x] P1 制定 `ux/plans/2026-06-07-home-entry-feedback.md`
- [ ] P1 编写 `ux/scripts/home-体验测试.md`
- [x] P1 执行 Home 首次体验走查
- [x] P1 输出 `ux/reports/home-体验报告-20260607.md`

### 交互与体验

- [ ] P1 检查常用网站删除是否有误触防护和撤销/确认体验
- [ ] P1 检查 AI 启动器删除是否不触发跳转
- [ ] P1 检查搜索入口是否清晰，搜索模式是否容易理解
- [ ] P1 检查最近文档预览、复制、删除、排序是否一致
- [ ] P1 检查解析队列抽屉是否能解释任务状态
- [ ] P2 优化 Home 空状态：无文档、无启动器、无队列任务
- [ ] P2 优化 Home 错误状态：API 不可用、文档不存在、解析失败
- [ ] P2 优化 Home 移动端布局：卡片、队列抽屉、操作按钮不拥挤

### 系统与沉淀

- [ ] P1 解决 Home 相关 apiBase 硬编码影响
- [ ] P1 抽取 Home/Brainstorm 共同 Toast 候选
- [ ] P2 抽取文档操作按钮模式：预览、复制、删除、重新解析
- [ ] P2 将 Home 的 Loading/Error/Empty 模式沉淀到 UI 规范
- [ ] P2 回归 Home 构建验证

---

## 3.2 Wiki / WikiPage

相关文件：

- `frontend/src/views/Wiki.vue`
- `frontend/src/views/WikiPage.vue`
- `frontend/src/components/MarkdownRenderer.vue`
- `frontend/src/components/WikiShareCard.vue`
- `backend/endpoints/wiki.py`
- `backend/endpoints/images.py`

### 盘点与脚本

- [x] P1 定义 Wiki 核心路径 1：进入 Wiki -> 查找文章 -> 阅读
- [x] P1 定义 Wiki 核心路径 2：进入 Wiki -> 新建文章 -> 保存 -> 再次查看
- [x] P1 定义 Wiki 核心路径 3：进入 Wiki -> 编辑文章 -> 保存 -> 回到阅读态
- [ ] P1 更新 `ux/scripts/wiki-体验测试.md`
- [ ] P1 回归 2026-05-30 Wiki 体验报告
- [x] P1 制定 `ux/plans/2026-06-07-wiki-core-path.md`

### P1 核心路径

- [ ] P1 验证编辑按钮是否稳定打开弹窗
- [x] P1 确认新建文章入口是否存在且可发现
- [ ] P1 确认搜索入口是否存在且可发现
- [ ] P1 验证编辑保存后当前页面、列表、URL 同步刷新
- [ ] P1 验证 WikiPage 独立路由直接访问、刷新、返回行为
- [ ] P1 验证封面图保存后不 404
- [x] P1 验证 wikilink 点击右侧预览和深入阅读路径

### P2 体验优化

- [x] P2 优化树形索引层级符号和缩进（`├`/`└` 前缀）
- [x] P2 优化文章元信息拥挤问题（chips + 标签独立行）
- [x] P2 优化主题切换按钮位置和提示（Header 全局入口）
- [ ] P2 验证长标题、长分类、长标签不溢出
- [ ] P2 验证超长 Markdown 阅读和编辑性能
- [ ] P2 验证封面图加载失败降级
- [ ] P2 验证 AI 封面图生成 loading、失败、重试

### 后端与数据

- [ ] P2 修复 compiled_hashes.json 与 wiki_pages 删除不同步
- [ ] P2 评估超长文档智能分段编译
- [x] P2 增加 wikilink 目标页面存在性验证（前端空状态 + 创建按钮）
- [ ] P2 验证 Wiki API 错误返回是否用户友好

### 沉淀

- [ ] P2 将 Wiki 编辑弹窗规则沉淀为 Modal 规范
- [ ] P2 将 Markdown 主题切换规则沉淀为阅读器规范
- [ ] P2 将封面图选择/AI 生成状态沉淀为长任务 UI 模式

---

## 3.3 KnowledgeBase 知识库

相关文件：

- `frontend/src/views/KnowledgeBase.vue`
- `frontend/src/components/MarkdownRenderer.vue`
- `backend/endpoints/upload.py`
- `backend/endpoints/categories.py`
- `backend/endpoints/export.py`
- `backend/endpoints/rag.py`
- `backend/endpoints/links.py`

### 盘点与脚本

- [ ] P1 定义 KnowledgeBase 核心路径 1：上传/粘贴内容 -> 入库 -> 查看
- [ ] P1 定义 KnowledgeBase 核心路径 2：筛选分类 -> 排序 -> 预览文档
- [ ] P1 定义 KnowledgeBase 核心路径 3：编辑分类/移动文档 -> 结果刷新
- [ ] P1 编写 `ux/scripts/knowledge-base-体验测试.md`
- [ ] P1 执行首次体验走查并输出报告

### 体验任务

- [ ] P1 验证文档列表排序与 Home 一致
- [ ] P1 验证文档预览弹窗尺寸、滚动和关闭
- [ ] P1 验证复制、删除、移动分类后的反馈
- [ ] P2 验证空知识库引导
- [ ] P2 验证大量文档下搜索/排序/分类性能
- [ ] P2 验证长文档 Markdown 渲染和滚动
- [ ] P2 验证上传失败、重复文档、解析失败提示

### 沉淀

- [ ] P2 与 Home 对齐文档操作组件
- [ ] P2 将文档预览抽屉/弹窗沉淀为 Drawer/Modal 规范
- [ ] P2 将分类标签、文档元信息沉淀为 Tag/Badge 规范

---

## 3.4 Automation 自动化解析

相关文件：

- `frontend/src/views/Home.vue`
- `frontend/src/components/TaskStatusBadge.vue`
- `backend/endpoints/automation.py`
- `backend/social_parsers.py`
- `bilibili-mcp-server/`
- `xiaohongshu-mcp-server/`

### 盘点与脚本

- [x] P1 定义 Automation 核心路径 1：提交单个链接 -> 任务成功 -> 文档入库
- [x] P1 定义 Automation 核心路径 2：批量提交 -> 队列进度 -> 批量结果
- [x] P1 定义 Automation 核心路径 3：解析失败 -> 查看原因 -> 重试
- [x] P1 制定 `ux/plans/2026-06-07-automation-progress-error.md`
- [ ] P1 编写 `ux/scripts/automation-体验测试.md`
- [x] P1 输出 `ux/reports/automation-体验报告-20260607.md`

### 核心路径稳定

- [ ] P1 验证抖音解析：普通链接、口令、收藏批量导入
- [ ] P1 验证 B 站解析：普通视频、长视频、有字幕/无字幕
- [ ] P1 验证小红书解析：HTML 结构变化时 fallback
- [ ] P1 验证队列任务详情不空白
- [ ] P1 验证重新解析不造成文档列表空窗
- [ ] P1 验证 ASR 失败时有中文可理解提示
- [ ] P1 验证 ffmpeg 不依赖进程 PATH

### 边界与稳定

- [ ] P2 清理 `_tasks` dict 长期增长问题
- [ ] P2 增加队列历史上限或定期清理策略
- [ ] P2 增加小红书解析 fallback 策略
- [ ] P2 验证火山 ASR 未配置时 DashScope 回退提示
- [ ] P2 验证下载返回 HTML/小文件/错误文件时提示
- [ ] P2 验证重复提交去重策略和用户反馈
- [ ] P2 验证批量任务部分成功/部分失败展示

### 沉淀

- [ ] P2 将长任务进度条沉淀为 Loading/Progress 规范
- [ ] P2 将失败重试和复制诊断信息沉淀为 Error State 规范
- [ ] P2 将批量任务状态沉淀为队列抽屉规范

---

## 3.5 Journal 手账日记

相关文件：

- `frontend/src/views/JournalView.vue`
- `backend/endpoints/journal.py`
- `backend/database.py`

### 盘点与脚本

- [x] P1 定义 Journal 核心路径 1：进入日记 -> 写今日 -> 保存
- [x] P1 定义 Journal 核心路径 2：切换日期 -> 查看历史 -> 编辑
- [x] P1 定义 Journal 核心路径 3：查看统计/随机回顾 -> 返回日记
- [x] P1 编写 `ux/scripts/journal-体验测试.md`
- [x] P1 输出 `ux/reports/journal-体验报告-20260607.md`

### 体验任务

- [ ] P1 验证一天一篇自动合并逻辑
- [ ] P1 验证保存、删除、更新反馈
- [ ] P1 验证日期切换不丢失未保存内容
- [ ] P2 验证空日期状态是否温和
- [ ] P2 验证长日记输入和阅读体验
- [ ] P2 验证标签云、心情、贴纸选择反馈
- [ ] P2 验证移动端三栏布局是否可用
- [ ] P3 优化随机回顾的情绪化表达
- [ ] P3 优化视觉细节：纸面、装订线、日期、行距

### 沉淀

- [ ] P2 将自动保存/手动保存反馈模式记录为表单规范
- [ ] P2 将情绪化空状态作为 Journal 专属设计记录

---

## 3.6 Search Assistant 搜索助手浮窗

相关文件：

- `extension/bing-assistant.js`
- `extension/assistant-panel.css`
- `extension/data/scene-rules.json`
- `extension/manifest.json`
- `frontend/src/views/Home.vue`

### 盘点与脚本

- [x] P1 定义 Search Assistant 核心路径 1：Bing 搜索 -> 浮窗出现 -> 场景匹配
- [x] P1 定义 Search Assistant 核心路径 2：来源筛选 -> 应用筛选 -> 页面刷新保持状态
- [x] P1 定义 Search Assistant 核心路径 3：展开 AI 分析 -> 获取解释
- [x] P1 编写 `ux/scripts/search-assistant-体验测试.md`
- [x] P1 输出 `ux/reports/search-assistant-体验报告-20260607.md`

### 核心任务

- [x] P1 验证扩展自动加载问题并记录可接受开发流程
- [x] P1 接入真实 AI 分析后端或明确占位状态
- [x] P1 验证场景标签切换、筛选、拖拽、关闭小圆点
- [x] P1 验证任意 Bing 搜索页均显示浮窗
- [x] P1 验证场景匹配不会被旧 session 覆盖

### 体验与扩展性

- [ ] P2 解决中文 Unicode 转义可读性问题
- [ ] P2 设计后端场景规则 API
- [ ] P2 支持场景规则动态更新和缓存
- [ ] P2 接入 AI 分析 SSE 流式输出
- [ ] P2 增加首次使用引导
- [ ] P2 适配 Bing 深色模式
- [ ] P2 做窄屏底部抽屉响应式
- [ ] P3 支持用户自定义场景
- [ ] P3 支持搜索历史和场景反馈上报

### 沉淀

- [ ] P2 建立浏览器扩展真实页面走查脚本
- [ ] P2 记录 Shadow DOM 样式隔离规范
- [ ] P2 记录扩展 content script reload 陷阱

---

## 4. 能力型功能模块 TODO

## 4.1 Workflow 编排

相关文件：

- `frontend/src/views/Workflow.vue`
- `backend/endpoints/workflow.py`
- `backend/workflow/engine.py`
- `backend/workflow/loader.py`
- `backend/workflow/executors.py`
- `backend/workflow/registry.py`
- `workflows/*.yml`

### 盘点与脚本

- [ ] P1 定义 Workflow 核心路径 1：白话创建工作流 -> 保存模板
- [ ] P1 定义 Workflow 核心路径 2：填写参数 -> 运行 -> 查看步骤状态
- [ ] P1 定义 Workflow 核心路径 3：暂停/恢复/归档 -> 下载产物
- [ ] P1 编写 `ux/scripts/workflow-体验测试.md`
- [ ] P1 输出首次体验报告

### 稳定性

- [ ] P1 验证 hello-world 模板完整执行
- [ ] P1 验证 pinterest-analyze 模板的 browser/ai/file 产出链路
- [ ] P1 验证模板 CRUD、复制、删除、归档
- [ ] P1 验证任务状态不会永远 pending
- [ ] P1 验证 AI 失败和 SSL 降级提示

### 待决与边界

- [ ] P2 设计 before/after gate 失败策略：retry_current / retry_previous / stop
- [ ] P2 给 after gate retry 增加最大次数，避免无限循环
- [ ] P2 给 human 步骤增加超时策略
- [ ] P3 评估 workflow 嵌套
- [ ] P3 设计模板市场/社区共享

### 体验

- [ ] P2 优化执行记录可读性：步骤、输入、输出、错误、文件
- [ ] P2 优化参数表单校验和默认值
- [ ] P2 优化产物下载和报告预览
- [ ] P2 增加空模板/无执行记录的引导

---

## 4.2 DDL 时间规划

相关文件：

- `frontend/src/views/DDL.vue`
- `backend/endpoints/ddl.py`
- `backend/database.py`

### 盘点与脚本

- [ ] P1 定义 DDL 核心路径 1：创建任务 -> 设置时间 -> 日/周/月展示
- [ ] P1 定义 DDL 核心路径 2：拖拽排序 -> 修改状态 -> 统计变化
- [ ] P1 定义 DDL 核心路径 3：切换视图 -> 查找任务 -> 编辑
- [ ] P1 编写 `ux/scripts/ddl-体验测试.md`
- [ ] P1 输出首次体验报告

### 体验任务

- [ ] P1 验证日/周/月/列表四视图数据一致
- [ ] P1 验证时间选择弹窗和快速创建路径
- [ ] P1 验证拖拽、勾选、编辑、删除反馈
- [ ] P2 验证空任务、超期任务、同一时间多任务显示
- [ ] P2 验证移动端日历和时间轴可用性
- [ ] P2 验证重复点击保存不会创建重复任务
- [ ] P2 增加浏览器通知提醒方案
- [ ] P2 设计任务关联文档/项目方案
- [ ] P3 设计重复任务
- [ ] P3 设计 iCal/日历订阅导出
- [ ] P3 设计 CSV/Markdown 批量导入

---

## 4.3 Skill Market

相关文件：

- `frontend/src/views/SkillMarket.vue`
- `backend/endpoints/skills.py`
- `backend/core/skills_sync.py`
- `backend/core/skills_scanner.py`

### 盘点与脚本

- [ ] P1 定义 Skill Market 核心路径 1：搜索社区 Skill -> 查看详情 -> 安装
- [ ] P1 定义 Skill Market 核心路径 2：扫描本地 Skill -> 启用/禁用
- [ ] P1 定义 Skill Market 核心路径 3：卸载/管理本地 Skill
- [ ] P1 编写 `ux/scripts/skill-market-体验测试.md`
- [ ] P1 输出首次体验报告

### 稳定与体验

- [ ] P1 验证社区 Skill 同步失败提示
- [ ] P1 验证本地 Skill 扫描结果和状态切换
- [ ] P1 验证安装当前仅记录数据库的文案是否清晰
- [ ] P2 实现或废弃 `frontend/src/stores/skills.js` 预留
- [ ] P2 设计实际 git clone 安装流程和安全确认
- [ ] P2 设计 Skill 更新检测
- [ ] P2 设计收藏功能
- [ ] P3 支持多数据源同步
- [ ] P3 设计评分/评论

---

## 4.4 Creator Hub

相关文件：

- `frontend/src/views/CreatorHub.vue`
- `backend/endpoints/creator.py`
- `docker-compose.creator.yml`
- `docs/新媒体创作Skill推荐清单.md`

### 盘点与脚本

- [ ] P1 定义 Creator Hub 核心路径 1：选择平台 -> 查看推荐 Skill -> 复制安装命令
- [ ] P1 定义 Creator Hub 核心路径 2：选择快捷工作流 -> 理解下一步
- [ ] P1 定义 Creator Hub 核心路径 3：进入资源库 -> 跳转相关模块
- [ ] P1 编写 `ux/scripts/creator-hub-体验测试.md`
- [ ] P1 输出首次体验报告

### 体验与功能

- [ ] P1 验证硬编码 Skill 数据是否仍准确可用
- [ ] P1 验证复制命令反馈
- [ ] P1 验证平台切换后的信息密度
- [ ] P2 填充小红书/B站/公众号平台专属 Skill
- [ ] P2 与 Skill Market 打通动态 Skill 数据
- [ ] P2 设计已安装 Skill 状态检测
- [ ] P2 设计一键安装安全确认
- [ ] P3 设计工作流自动化：点击后串联多 Skill

---

## 4.5 SOP

相关文件：

- `frontend/src/views/SOP.vue`
- `frontend/src/components/SOPBlockCard.vue`
- `frontend/src/components/SOPChainEditor.vue`
- `frontend/src/components/SOPSuggestionQueue.vue`
- `backend/endpoints/sop.py`
- `backend/sop_evolution.py`

### 盘点与脚本

- [ ] P1 定义 SOP 核心路径 1：创建流程块 -> 保存 -> 查看
- [ ] P1 定义 SOP 核心路径 2：拖拽组合流程链 -> 保存顺序
- [ ] P1 定义 SOP 核心路径 3：从建议队列采纳/拒绝建议
- [ ] P1 编写 `ux/scripts/sop-体验测试.md`
- [ ] P1 输出首次体验报告

### 体验任务

- [ ] P1 验证拖拽反馈和 drop 位置清晰
- [ ] P1 验证流程块编辑、删除、保存反馈
- [ ] P1 验证建议队列解析和采纳路径
- [ ] P2 验证空流程链引导
- [ ] P2 验证长步骤、长标题、标签溢出
- [ ] P2 统一 SOP 卡片、标签、按钮样式
- [ ] P2 增加撤销/取消编辑防误操作提示

---

## 4.6 Learning

相关文件：

- `frontend/src/views/Learning.vue`
- `frontend/src/views/LearningChecklist.vue`
- `frontend/src/views/LearningPlan.vue`
- `mods/learning/*.md`
- `backend/main.py` learning 路由

### 盘点与脚本

- [ ] P1 定义 Learning 核心路径 1：选择学习计划 -> 阅读计划
- [ ] P1 定义 Learning 核心路径 2：打开清单 -> 勾选 -> 复盘
- [ ] P1 定义 Learning 核心路径 3：计划阅读 -> 返回列表
- [ ] P1 编写 `ux/scripts/learning-体验测试.md`
- [ ] P1 输出首次体验报告

### 体验任务

- [ ] P1 验证 Markdown 计划渲染
- [ ] P1 验证 checklist 完成状态本地策略是否表达清晰
- [ ] P2 验证有序列表、嵌套列表等 Markdown 格式
- [ ] P2 评估多端同步 checklist 状态是否进入后端存储
- [ ] P2 优化空计划/加载失败提示
- [ ] P3 增加学习复盘入口和阶段完成反馈

---

## 4.7 Brainstorm

相关文件：

- `frontend/src/views/Brainstorm.vue`
- `backend/endpoints/brainstorm.py`
- `mods/brainstorm/`

### 盘点与脚本

- [ ] P1 定义 Brainstorm 核心路径 1：输入想法 -> Step2 追问 -> 选择回答
- [ ] P1 定义 Brainstorm 核心路径 2：完成 Step3 -> 获得输出
- [ ] P1 定义 Brainstorm 核心路径 3：异常响应 -> 用户可恢复
- [ ] P1 编写 `ux/scripts/brainstorm-体验测试.md`
- [ ] P1 输出首次体验报告

### 稳定与体验

- [ ] P1 测试 Prompt 改动后的选项解析兼容性
- [ ] P1 验证 AI 返回格式异常时的降级提示
- [ ] P1 验证 loading、错误、重试
- [ ] P2 与 Home 统一 Toast
- [ ] P2 优化长对话、长选项显示
- [ ] P2 增加空输入和低质量输入引导

---

## 4.8 AI Search / RAG / Review / Operations

相关文件：

- `backend/endpoints/ai_search.py`
- `backend/endpoints/rag.py`
- `backend/endpoints/review.py`
- `backend/endpoints/operations.py`
- 相关前端入口主要在 Home、KnowledgeBase、CreatorHub

### 盘点与脚本

- [ ] P2 梳理 AI Search 是否有前端入口
- [ ] P2 梳理 RAG 查询入口和错误反馈
- [ ] P2 梳理 Review/Weekly Report 的前端或 API 使用路径
- [ ] P2 梳理 Operations 创作流水线相关入口

### 体验与稳定

- [ ] P2 验证 AI Search 网络失败和无结果提示
- [ ] P2 验证 RAG 空知识库、无相关结果、向量库不可用提示
- [ ] P2 验证 Review 润色失败、API key 缺失提示
- [ ] P2 验证 Operations 脚本生成、项目/选题管理的空状态和错误状态
- [ ] P3 决定是否为这些能力建立独立页面或统一入口

---

## 5. 系统与平台模块 TODO

## 5.1 Backend

相关文件：

- `backend/main.py`
- `backend/database.py`
- `backend/ai_client.py`
- `backend/mcp_server.py`
- `backend/processing/*`
- `backend/tests/test_main.py`

### P0/P1 稳定

- [ ] P1 统一可用 Python 启动方式，规避 GUI venv 和 Microsoft Store 重定向器
- [ ] P1 将 API key 从 `ai_client.py` 移到 `.env`
- [ ] P1 调整全局异常处理，生产环境不暴露堆栈
- [ ] P1 收紧或环境化 CORS 配置
- [ ] P1 将 `_sanitize_pid_file()` 端口检测改为 `127.0.0.1`
- [ ] P1 验证所有 router 注册不会因单模块语法错误导致服务无提示崩溃
- [ ] P1 增加 `/health` 对关键依赖的可诊断信息

### P2 可诊断性

- [ ] P2 建立统一错误响应格式
- [ ] P2 增加后端日志路径和最近错误查看说明
- [ ] P2 建立数据库迁移记录和启动校验
- [ ] P2 验证 ChromaDB 维度不一致时提示
- [ ] P2 扩充后端测试：health、documents、categories、automation、workflow、journal

---

## 5.2 Deploy / 启停 / 构建

相关文件：

- `start-background.ps1`
- `stop-background.ps1`
- `后台启动.bat`
- `后台停止.bat`
- `frontend/build.sh`
- `Dockerfile`
- `docker-compose.yml`

### 稳定任务

- [ ] P1 明确禁止手动 `python backend/main.py` 启动的操作规范
- [ ] P1 验证 `后台启动.bat` 能持续启动后端
- [ ] P1 验证 `后台停止.bat` 能停止 PID 文件进程和端口进程
- [ ] P1 修复或记录 Windows `python` 重定向器长期方案
- [ ] P1 修复或记录 venv 污染长期方案
- [ ] P1 验证端口被野进程占用时脚本提示清楚
- [ ] P1 前端 apiBase 硬编码改为配置化或同源策略

### 构建部署

- [ ] P1 验证前端 build.sh 无空格目录构建
- [ ] P2 验证 Docker 构建和启动
- [ ] P2 增加 `.env.example`
- [ ] P2 增加生产部署说明：静态文件 + API 反代
- [ ] P3 评估 Windows Service 封装

---

## 5.3 Browser Extension

相关文件：

- `extension/manifest.json`
- `extension/background.js`
- `extension/popup.html`
- `extension/popup.js`
- `extension/bing-assistant.js`
- `extension/data/scene-rules.json`

### 通用扩展体验

- [ ] P1 验证 popup 后端地址配置
- [ ] P1 验证 Service Worker 保活和 PING 机制
- [ ] P1 验证后端不可用时 popup 提示
- [ ] P1 验证抖音收藏批量导入入口
- [ ] P1 验证剪藏/提交队列结果反馈
- [ ] P2 验证扩展上下文失效时提示刷新页面
- [ ] P2 验证 Edge/Chrome storage 兼容
- [ ] P2 验证扩展权限最小化

### 废弃记忆功能清理

- [ ] P1 验证 memory 相关 content_scripts 已清理
- [ ] P1 验证 popup 不再显示已废弃记忆入口
- [ ] P2 更新扩展 README 或使用说明

---

## 5.4 Electron Desktop Dashboard

相关文件：

- `electron/main.js`
- `electron/preload.js`
- `electron/package.json`
- `electron/electron-builder.yml`
- `frontend/src/router/index.js`
- `frontend/src/stores/settings.js`

### 当前阻塞

- [!] P2 解决 Electron `require('electron')` 解析异常  
  说明：国内镜像安装的 Electron 28.3.3 二进制导致 require 返回包路径字符串

### 恢复任务

- [ ] P2 从官方源重装或升级 Electron 30+
- [ ] P2 验证 Electron 主进程启动
- [ ] P2 验证 preload API 暴露
- [ ] P2 验证 hash router 在 file 协议下可用
- [ ] P2 验证后端管理 IPC：启动、停止、状态
- [ ] P2 验证本地字体和静态资源
- [ ] P2 验证 window.open 改 openExternal
- [ ] P3 制定 Desktop Dashboard 体验走查脚本

---

## 5.5 Second Self

相关文件：

- `study-hub/second-self/*`
- `study-hub/backend/endpoints/second_self.py`
- `study-hub/frontend/public/second-self/index.html`
- `study-hub/frontend/public/second-self/hero.js`

### 盘点与脚本

- [ ] P1 定义 Second Self 核心路径 1：进入 StudyHub 统一入口 -> 聊天
- [ ] P1 定义 Second Self 核心路径 2：批量导入 -> 蒸馏 -> 查看记忆
- [ ] P1 定义 Second Self 核心路径 3：查看/编辑核心 self 文件
- [ ] P1 编写 `ux/scripts/second-self-体验测试.md`
- [ ] P1 输出首次体验报告

### 体验与稳定

- [ ] P1 验证 3D hero 非空、可加载、不卡死
- [ ] P1 验证 DeepSeek API 缺失/失败提示
- [ ] P1 验证 batch-import 四种格式
- [ ] P1 验证 SQLite WAL 并发和 busy_timeout
- [ ] P1 验证 StudyHub 8741 入口无需单独启动 8420
- [ ] P2 验证移动端/窄屏 second-self 页面
- [ ] P2 增加导入结果摘要和失败条目展示
- [ ] P2 验证安全边界：raw/ 不可变、路径越界保护

---

## 5.6 Memory 废弃态

相关文件：

- `project-memory/memory/状态.md`
- `backend/main.py`
- `backend/database.py`
- `backend/mcp_server.py`
- `frontend/src/router/index.js`
- `extension/manifest.json`

### 废弃验证

- [-] P1 不恢复五层记忆系统
- [ ] P1 验证 `/memory` 前端路由已移除
- [ ] P1 验证后端 memory router 已移除
- [ ] P1 验证数据库初始化不再创建废弃 memory 表
- [ ] P1 验证 MCP Server 不再暴露废弃 memory 工具
- [ ] P1 验证扩展不再加载 memory content scripts
- [ ] P2 更新 `memory/问题.md` 中待观察项，标注历史状态
- [ ] P2 清理用户容易误解的旧文档入口

---

## 5.7 Obsidian Bridge

相关文件：

- `project-memory/obsidian-bridge/PRD.md`

### 架构与体验

- [ ] P2 阅读 Obsidian Bridge PRD
- [ ] P2 制定 Obsidian 双向通信小方案
- [ ] P2 明确依赖 Obsidian Local REST API 插件的安装/鉴权体验
- [ ] P2 设计 wikilinks 自动转换规则
- [ ] P2 设计同步冲突和失败提示
- [ ] P3 编写 Obsidian Bridge 体验测试脚本
- [ ] P3 决定是否进入实现阶段

---

## 5.8 Admin / System Status

相关文件：

- `backend/endpoints/admin.py`
- `frontend/src/components/SystemStatus.vue`

### 体验与诊断

- [ ] P2 定义系统状态核心路径：查看后端连接、日志、最近文档、系统信息
- [ ] P2 验证 SystemStatus 连接失败提示
- [ ] P2 验证 admin logs 可读性
- [ ] P2 验证 monitored URLs 展示和错误状态
- [ ] P2 增加复制诊断信息入口
- [ ] P3 设计健康检查仪表盘

---

## 6. UI / 设计系统 TODO

## 6.1 第一批：反馈组件

- [ ] P1 制定 Toast 组件小方案
- [ ] P1 抽取统一 Toast 组件
- [ ] P1 在 Home 和 Brainstorm 首批落地 Toast
- [ ] P2 推广 Toast 到 Wiki、Automation、Journal、Skill Market
- [ ] P1 制定 Loading 规范：按钮 loading、页面 loading、长任务 loading
- [ ] P1 制定 Error State 规范：原因、操作、诊断
- [ ] P1 制定 Empty State 规范：图标、标题、说明、主操作

## 6.2 第二批：操作容器

- [ ] P2 制定 Modal 组件小方案
- [ ] P2 梳理 Home、Wiki、DDL、SOP、Journal 中的弹窗
- [ ] P2 抽取通用 Modal 或先写 Modal 规范
- [ ] P2 制定 Drawer 规范
- [ ] P2 对齐文档预览、队列抽屉、Wiki 预览
- [ ] P2 制定 Confirm Dialog 规范
- [ ] P2 替换原生 `confirm()` 的高风险操作

## 6.3 第三批：基础控件

- [ ] P2 制定 Button 规范：主、次、危险、图标、文本
- [ ] P2 制定 Toolbar 规范：搜索、排序、筛选、新建、更多
- [ ] P2 制定 Tag/Badge 规范：分类、状态、来源、优先级
- [ ] P2 制定 Form Field 规范：标签、提示、错误、禁用
- [ ] P2 制定 Status Badge 规范，复用 TaskStatusBadge 经验

## 6.4 第四批：视觉变量

- [ ] P2 扫描硬编码色值
- [ ] P2 收敛 accent 色 `#7c8aff` 和变体
- [ ] P2 定义 CSS 变量：背景、文本、边框、强调、危险、成功
- [ ] P2 定义间距和圆角规则
- [ ] P2 定义页面标题区和工具栏布局规则
- [ ] P3 定义暗色模式策略
- [ ] P3 定义 Markdown 阅读区域主题策略

## 6.5 响应式与可访问性

- [ ] P2 为高频模块验证 390px、768px、1280px 视口
- [ ] P2 确保按钮文字不溢出
- [ ] P2 确保弹窗和抽屉不超出视口
- [ ] P2 增加可见 focus 状态
- [ ] P2 检查颜色对比度
- [ ] P3 制定键盘快捷键策略

---

## 7. 后端 API 功能面 TODO

按 endpoint 覆盖，不一定都需要独立页面。

- [ ] P2 `admin.py`：验证 stats/logs/system/info 的错误状态和权限边界
- [ ] P2 `ai_search.py`：验证搜索失败、空结果、API key 缺失
- [ ] P1 `automation.py`：纳入 Automation 主路径
- [ ] P1 `brainstorm.py`：纳入 Brainstorm 主路径
- [ ] P2 `categories.py`：纳入 KnowledgeBase 分类管理
- [ ] P2 `creator.py`：确认服务管理 API 是否仍预留或需要前端入口
- [ ] P1 `ddl.py`：纳入 DDL 主路径
- [ ] P3 `evolution.py`：确认 Skill 自进化功能入口和安全边界
- [ ] P2 `export.py`：验证文档导出和全量导出体验
- [ ] P2 `images.py`：验证 AI 封面图生成失败/超时/路径
- [ ] P1 `journal.py`：纳入 Journal 主路径
- [ ] P2 `links.py`：验证 wiki/document links 和 backlinks
- [ ] P2 `operations.py`：纳入 Creator Hub/运营流水线体验
- [ ] P2 `rag.py`：验证知识问答入口和空结果
- [ ] P2 `review.py`：验证润色/周报能力是否需要前端入口
- [ ] P1 `second_self.py`：纳入 Second Self 主路径
- [ ] P1 `skills.py`：纳入 Skill Market 主路径
- [ ] P1 `sop.py`：纳入 SOP 主路径
- [ ] P1 `upload.py`：纳入 KnowledgeBase/Home 文档主路径
- [ ] P1 `wiki.py`：纳入 Wiki 主路径
- [ ] P1 `workflow.py`：纳入 Workflow 主路径

---

## 8. 测试脚本与报告 TODO

### 8.1 scripts 目录

- [ ] P1 创建 `ux/scripts/README.md`
- [ ] P1 更新 `wiki-体验测试.md`
- [ ] P1 新增 `home-体验测试.md`
- [ ] P1 新增 `automation-体验测试.md`
- [ ] P1 新增 `journal-体验测试.md`
- [x] P1 新增 `search-assistant-体验测试.md`
- [ ] P2 新增 `knowledge-base-体验测试.md`
- [ ] P2 新增 `workflow-体验测试.md`
- [ ] P2 新增 `ddl-体验测试.md`
- [ ] P2 新增 `skill-market-体验测试.md`
- [ ] P2 新增 `creator-hub-体验测试.md`
- [ ] P2 新增 `sop-体验测试.md`
- [ ] P2 新增 `learning-体验测试.md`
- [ ] P2 新增 `brainstorm-体验测试.md`
- [ ] P2 新增 `second-self-体验测试.md`
- [ ] P3 新增 `obsidian-bridge-体验测试.md`
- [ ] P3 新增 `electron-体验测试.md`

### 8.2 reports 目录

- [ ] P1 创建 `ux/reports/README.md`
- [ ] P1 更新/回归 Wiki 报告
- [x] P1 输出 Home 报告
- [x] P1 输出 Automation 报告
- [x] P1 输出 Journal 报告
- [x] P1 输出 Search Assistant 报告
- [ ] P2 输出 KnowledgeBase 报告
- [ ] P2 输出 Workflow 报告
- [ ] P2 输出 DDL 报告
- [ ] P2 输出 Skill Market 报告
- [ ] P2 输出 Creator Hub 报告
- [ ] P2 输出 SOP 报告
- [ ] P2 输出 Learning 报告
- [ ] P2 输出 Brainstorm 报告
- [ ] P2 输出 Second Self 报告
- [ ] P3 输出 Electron 报告
- [ ] P3 输出 Obsidian Bridge 报告

---

## 9. 小方案 TODO

### 9.1 第一批 P1 小方案

- [x] P1 `2026-06-07-wiki-core-path.md`
- [x] P1 `2026-06-07-home-entry-feedback.md`
- [x] P1 `2026-06-07-automation-progress-error.md`
- [ ] P1 `2026-06-09-journal-record-review.md`
- [x] P1 `2026-06-10-search-assistant-real-browser.md`
- [ ] P1 `2026-06-11-backend-deploy-stability.md`
- [x] P1 `2026-06-12-ui-feedback-components.md`

### 9.2 第二批 P2 小方案

- [ ] P2 `workflow-run-template-ux.md`
- [x] P2 `2026-06-07-wiki-p2-polish.md`
- [ ] P2 `knowledge-base-document-operations.md`
- [ ] P2 `ddl-calendar-planning-ux.md`
- [ ] P2 `skill-market-install-management.md`
- [ ] P2 `creator-hub-skill-driven-flow.md`
- [ ] P2 `sop-chain-editor-ux.md`
- [ ] P2 `learning-plan-checklist-ux.md`
- [ ] P2 `brainstorm-ai-response-resilience.md`
- [ ] P2 `second-self-batch-import-chat.md`
- [ ] P2 `extension-popup-clip-queue.md`

### 9.3 第三批 P3 小方案

- [ ] P3 `electron-desktop-dashboard-recovery.md`
- [ ] P3 `obsidian-bridge-architecture-ux.md`
- [ ] P3 `visual-polish-design-tokens.md`
- [ ] P3 `workflow-template-market.md`
- [ ] P3 `search-assistant-custom-scenes.md`

---

## 10. 阶段完成定义

### 10.1 最小完成

- [x] 高频五模块都有脚本
- [x] 高频五模块都有报告
- [x] 高频五模块都有小方案
- [ ] Wiki 完成一轮完整闭环
- [ ] P0 问题清单明确
- [ ] P1 问题进入追踪表

### 10.2 合格完成

- [ ] Wiki、Home、Automation 完成修复和回归
- [x] Journal、Search Assistant 完成走查和小方案
- [ ] Backend/Deploy P1 稳定性问题有处理方案
- [ ] Toast、Loading、Error、Empty 初步统一
- [ ] `ux/问题追踪.md` 不再是模板占位，而是真实看板

### 10.3 理想完成

- [ ] 全部前端路由页面都有体验脚本或明确不测理由
- [ ] 全部后端 endpoint 都映射到前端路径或系统验证项
- [ ] 高频模块体验评分达到 4.0/5 左右
- [ ] P1 不长期积压
- [ ] UI 设计规范和组件规范初版完成
- [ ] 新功能默认纳入核心路径、边界测试、体验验收
