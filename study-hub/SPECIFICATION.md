# 学习中枢 Study Hub — 产品规格说明书

> 本文档是产品经理与各模块开发者的契约。每个模块的开发者在动手之前必须先读完自己负责的模块章节。
> 
> 版本：v1.0 | 日期：2026-05-02

---

## 目录

1. [模块总览与负责人](#1-模块总览与负责人)
2. [模块 A：Frontend 仪表盘 (index.html)](#2-模块-afrontend-仪表盘-indexhtml)
3. [模块 B：Frontend 知识库管理 (kb.html)](#3-模块-bfrontend-知识库管理-kbhtml)
4. [模块 C：Backend Core (main.py + database.py)](#4-模块-cbackend-core-mainpy--databasepy)
5. [模块 D：AI Client 适配层 (ai_client.py)](#5-模块-dai-client-适配层-ai_clientpy)
6. [模块 E：RAG 知识库 (chunker + vector_store + /rag)](#6-模块-erag-知识库-chunker--vector_store--rag)
7. [模块 F：Chrome 扩展 (extension/)](#7-模块-fchrome-扩展-extension)
8. [模块 G：MCP Server (mcp_server.py)](#8-模块-gmcp-server-mcp_serverpy)
9. [模块 H：Inbox Watcher (watcher.py)](#9-模块-hinbox-watcher-watcherpy)
10. [模块 I：每日复盘系统 (review.py)](#10-模块-i每日复盘系统-reviewpy)
11. [接口契约（模块间通信约定）](#11-接口契约模块间通信约定)
12. [验收标准总表](#12-验收标准总表)

---

## 1. 模块总览与负责人

```
Frontend ──HTTP──> Backend Core ──调用──> AI Client
                     │                      │
                     ├──> RAG (ChromaDB) <──┘ (embedding)
                     ├──> Review System <───┘ (润色/周报)
                     ├──> Upload / Categories
                     └──> Inbox Watcher (文件系统事件)

Chrome Extension ──HTTP──> Backend Core (/upload/text)
MCP Server ──HTTP──> Backend Core (全部 API)
```

| 编号 | 模块 | 文件范围 | 建议开发者 | 优先级 |
|------|------|----------|-----------|--------|
| A | 仪表盘前端 | `frontend/index.html` | 前端 | P0 |
| B | 知识库管理前端 | `frontend/kb.html` | 前端 | P0 |
| C | 后端核心 | `main.py` `database.py` | 后端 | P0 |
| D | AI 适配层 | `ai_client.py` | 后端 | P0 |
| E | RAG 知识库 | `chunker.py` `vector_store.py` `endpoints/rag.py` | 后端 | P0 |
| F | Chrome 扩展 | `extension/` | 扩展开发 | P1 |
| G | MCP Server | `mcp_server.py` | 集成开发 | P1 |
| H | Inbox Watcher | `watcher.py` | 后端 | P1 |
| I | 每日复盘 | `endpoints/review.py` | 后端 | P0 |

---

## 2. 模块 A：Frontend 仪表盘 (index.html)

### 2.1 功能描述

浏览器新标签页的主页面。用户打开新标签页时看到的第一屏，聚合了所有学习工具的入口。

### 2.2 当前状态

基本功能已实现，但存在以下待修复/待开发项。

### 2.3 开发者任务清单

#### P0 - 必须完成

**1. 分类筛选下拉框数据加载**
- 文件位置：`index.html` 第 214 行的 `<select id="searchCategory">`
- 当前问题：下拉框写死了一个 `<option value="">全部分类</option>`，没有动态加载分类列表
- 预期行为：页面加载时调用 `GET /categories` 获取全部分类列表，动态填充到下拉框
- 实现方式：在 `init()` 函数中添加 `loadCategories()` 调用，参考 `kb.html` 中的类似实现
- 验收标准：刷新页面后下拉框显示所有已创建的分类（含 "全部" 和 "未分类"）

**2. 文档点击查看功能完善**
- 当前问题：`index.html` 中点击文档标题调用 `viewDocument(id)`，打开了 docModal 弹窗，但功能过于简陋
- 预期行为：弹窗中显示文档标题、分类标签、创建时间、标签、全文内容，以及 "发送到 Claude" 按钮
- 验收标准：点击文档 → 弹窗展示完整信息 → 点击发送到 Claude → 复制全文 → 打开 claude.ai

**3. 搜索功能错误处理优化**
- 当前问题：当后端不可达时，`doKBQuery` 函数 catch 了错误但显示的是硬编码的 API_BASE
- 预期行为：显示友好的错误提示 "无法连接学习中枢后端，请确认已执行 docker compose up -d 或 python main.py"
- 验收标准：后端未启动时搜索，显示友好错误信息

#### P1 - 重要

**4. 自定义命令系统**
- 当前 `handleCommand` 函数只处理了 `notes` 和 `folder` 两个硬编码命令
- 预期行为：支持用户在 localStorage 中配置自定义 `>命令 → URL` 映射，例如 `>prd → https://docs.google.com/xxx`
- UI：在设置弹窗中管理命令列表（新增/编辑/删除）
- 验收标准：输入 `>prd` 回车 → 打开对应 URL

**5. 常用网站 / AI 启动器支持编辑**
- 当前问题：右键可以编辑快捷方式，但 AI 启动器只能添加不能编辑/删除
- 预期行为：AI 启动器卡片 hover 时显示编辑和删除按钮，与常用网站行为一致
- 验收标准：AI 启动器可以编辑名称、URL、图标，可以删除

#### P2 - 锦上添花

**6. 仪表盘布局可配置**
- 允许用户拖拽调整模块顺序（搜索→快捷方式→AI启动器→知识库→复盘）
- 允许隐藏不需要的模块

### 2.4 存储规范

所有用户配置存储在 `localStorage`，键名规范：
- `shortcuts` — 常用网站列表 JSON
- `ais` — AI 启动器列表 JSON
- `commands` — 自定义命令映射 JSON `{"命令名": "URL"}`
- `api_base` — 后端地址（如用户自定义过）

### 2.5 依赖关系

- 依赖模块 C（Backend Core）提供 API
- 依赖模块 I（每日复盘）提供 `/review/polish` `/review/list` `/review/weekly`
- 依赖模块 E（RAG）提供 `/rag/query`

---

## 3. 模块 B：Frontend 知识库管理 (kb.html)

### 3.1 功能描述

独立的知识库管理页面。提供分类侧边栏 + 文档表格的全功能文档管理界面。

### 3.2 当前状态

UI 框架完整，但部分功能按钮为占位符。

### 3.3 开发者任务清单

#### P0 - 必须完成

**1. 文档删除功能联调**
- 文件位置：`kb.html` 第 582-591 行 `deleteDoc()` 函数
- 当前问题：按钮显示 "请通过后端 API 删除（待添加）"，实际未实现
- 预期行为：点击删除 → 确认弹窗 → 调用 `DELETE /documents/{id}` → 刷新列表
- 需要后端配合：添加 `DELETE /documents/{id}` API（见模块 C）
- 验收标准：点击删除 → 确认 → 文档从列表消失

**2. 批量删除功能**
- 文件位置：`kb.html` 第 569-580 行 `batchDelete()` 函数
- 当前问题：按钮可点击但无实际效果
- 预期行为：勾选多个文档 → 点击批量删除 → 确认 → 全部删除 → 刷新列表
- 需要后端配合：添加 `POST /documents/batch-delete` API（见模块 C）
- 验收标准：选中 3 个文档 → 批量删除 → 3 个文档全部移除

**3. 文档搜索功能**
- 当前问题：`renderDocs()` 中通过 `searchBox` 实现了客户端标题过滤，但对大文档库不够
- 预期增强：搜索框延迟 300ms 防抖后再过滤，避免快速输入时频繁渲染
- 验收标准：快速连续输入 10 个字符 → 只触发 1 次过滤渲染

#### P1 - 重要

**4. 文档编辑功能**
- 新增需求：点击文档行旁的 "编辑" 按钮 → 弹窗中可修改标题、内容、分类
- API：`PUT /documents/{id}` — 更新 title / content / category_id
- 验收标准：修改标题 → 保存 → 列表中标题即时更新

**5. 分类拖拽排序**
- 新增需求：侧边栏分类列表支持拖拽排序
- API：`PUT /categories/sort` — 接收排序后的分类 ID 数组
- 验收标准：拖拽分类到新位置 → 松开 → 顺序持久化

#### P2 - 锦上添花

**6. 文档内容中关键词高亮**
- 文档详情弹窗中，对搜索关键词进行高亮标注

### 3.4 依赖关系

- 依赖模块 C（Backend Core）提供删除、编辑 API（部分待添加）

---

## 4. 模块 C：Backend Core (main.py + database.py)

### 4.1 功能描述

FastAPI 服务入口、数据库初始化、CORS 配置、静态文件挂载、生命周期管理。

### 4.2 当前状态

基本框架完整。数据库表结构完整。缺少删除类 API。

### 4.3 开发者任务清单

#### P0 - 必须完成

**1. 添加文档删除 API**
- 文件位置：`endpoints/upload.py`（新增路由）
- 接口：`DELETE /documents/{doc_id}`
- 行为：
  1. 校验文档存在，不存在返回 404
  2. 删除 `documents` 表中对应行
  3. 同步删除 ChromaDB 中该文档的所有 chunks
  4. 返回 `{"status": "ok", "deleted_id": doc_id}`
- 验收标准：`curl -X DELETE /documents/1` → 数据库和向量库同步删除

**2. 添加批量删除 API**
- 文件位置：`endpoints/upload.py`（新增路由）
- 接口：`POST /documents/batch-delete`
- 请求体：`{"doc_ids": [1, 2, 3]}`
- 行为：
  1. 逐个删除文档和对应的 ChromaDB chunks
  2. 即使部分删除失败也继续执行（best-effort）
  3. 返回成功删除数量 `{"deleted_count": 2, "failed_ids": [3]}`
- 验收标准：`curl -X POST /documents/batch-delete -d '{"doc_ids":[1,2,3]}'` → 3 个文档删除

**3. 分类下拉框数据接口确认**
- 接口 `GET /categories` 已存在，需确认以下返回格式：
  ```json
  [
    {"id": 1, "name": "Python", "icon": "🐍", "color": "#4ade80", "doc_count": 5, "sort_order": 0},
    {"id": 2, "name": "JavaScript", "icon": "📜", "color": "#f59e0b", "doc_count": 3, "sort_order": 1}
  ]
  ```
- 确认 `doc_count` 实时反映已关联文档数量。

#### P1 - 重要

**4. 添加文档编辑 API**
- 接口：`PUT /documents/{doc_id}`
- 请求体：`{"title": "新标题", "content": "新内容", "category_id": 2}`
- 行为：支持部分更新（只传要改的字段），更新后如果 content 变了需要重新分块 + 向量化
- 验收标准：修改内容后，重新搜索能反映出新内容

**5. 分类排序 API**
- 接口：`PUT /categories/sort`
- 请求体：`{"order": [3, 1, 2]}` — 分类 ID 数组，按期望顺序排列
- 行为：批量更新 `sort_order` 字段
- 验收标准：排序后 `GET /categories` 按新顺序返回

**6. 错误处理中间件**
- 当前问题：后端异常时 FastAPI 返回 HTML 格式的 500，前端无法 parse
- 新增：全局异常处理器，所有未捕获异常返回 `{"error": "内部服务错误", "detail": "..."}` 的 JSON
- 验收标准：任何未处理异常都返回 JSON 格式错误信息

#### P2 - 锦上添花

**7. API 限流**
- 对 `/rag/query` 和 `/review/polish` 添加简单的速率限制（每 IP 每分钟 30 次）
- 方案：内存中的 token bucket，无需引入 Redis

### 4.4 接口契约

所有 API 返回格式统一为 JSON。成功时不强制包装，错误时必须包含 `error` 字段。

---

## 5. 模块 D：AI Client 适配层 (ai_client.py)

### 5.1 功能描述

统一的多 AI Provider 适配器。屏蔽 Claude API (Anthropic 格式) 和 OpenAI 兼容 API 的差异，提供统一的 `chat()` 和 `embed()` 接口。

### 5.2 当前支持的 Provider

| Provider | chat | embed | 备注 |
|----------|------|-------|------|
| Claude | Anthropic Messages API | 不支持，自动退避 | embeddings 会切换到其他可用 provider |
| Kimi | OpenAI 兼容 `/chat/completions` | `/embeddings` | 国内可用 |
| DeepSeek | OpenAI 兼容 | `/embeddings` | |
| 豆包 | OpenAI 兼容 | `/embeddings` | 火山引擎 |

### 5.3 开发者任务清单

#### P0 - 必须完成

**1. Embedding 模型可配置**
- 当前问题：`embed()` 方法中 `embedding_model` 硬编码为 `cfg["model"]`，但 chat model 和 embedding model 通常不同
- 预期行为：每个 provider 配置支持独立的 `embedding_model` 环境变量，如 `KIMI_EMBEDDING_MODEL`
- 默认值：不配置时使用 provider 的默认 chat model
- 验收标准：`.env` 中设置 `KIMI_EMBEDDING_MODEL=moonshot-v1-8k` → embed 调用使用该模型

**2. 默认 provider 逻辑修正**
- 当前问题：`DEFAULT_PROVIDER` 的默认值写在代码里是 `"kimi"`，但 `.env.example` 中 `AI_DEFAULT_PROVIDER=claude`
- 修复：改为 `os.getenv("AI_DEFAULT_PROVIDER", "claude")`
- 验收标准：不设置环境变量时默认使用 claude

**3. Embedding 请求超时优化**
- 当前问题：embed 使用同步 `httpx.Client(timeout=120)` 阻塞事件循环
- 预期行为：改为异步 `httpx.AsyncClient`，与 `chat()` 方法保持一致
- 验收标准：大量文本 embedding 不阻塞其他 API 请求

#### P1 - 重要

**4. Provider 健康检查**
- 新增方法：`async def health_check(provider) -> bool`
- 行为：向 provider 发送最小请求验证 API Key 有效
- 用途：前端 /health 接口可返回各 provider 状态
- 验收标准：`GET /health` 返回 `{"claude": "ok", "kimi": "unconfigured"}`

**5. 请求重试机制**
- 当前问题：API 偶发超时直接返回错误，无重试
- 行为：5xx 错误自动重试 1 次（间隔 1s），超时错误自动重试 1 次
- 验收标准：模拟一次超时 → 自动重试成功

#### P2 - 锦上添花

**6. Token 用量统计**
- 每次 chat/embed 调用记录 token 消耗
- 提供 `GET /admin/usage` 接口查看用量统计
- 本地 SQLite 存储，不做云端上报

### 5.4 依赖关系

- 被模块 E（RAG）的 embedding 调用
- 被模块 I（每日复盘）的润色/周报调用
- 被模块 G（MCP Server）间接依赖（通过后端 API）

---

## 6. 模块 E：RAG 知识库 (chunker + vector_store + /rag)

### 6.1 功能描述

文档分块 → 向量化 → 语义搜索 → AI 基于上下文回答。知识库的核心检索增强生成链路。

### 6.2 数据流

```
文档上传 → chunk_text() → [chunk1, chunk2, ...]
       → VectorStore.add_document() → embedding → ChromaDB
用户提问 → VectorStore.query() → embedding → top_k 检索
       → 拼接 context → AI Client chat() → 回答
```

### 6.3 开发者任务清单

#### P0 - 必须完成

**1. 分块策略优化**
- 文件位置：`processing/chunker.py`
- 当前方案：固定 500 字符按句子边界切分
- 问题：对于代码类文档，按句号切分会破坏代码结构
- 预期方案：
  - 检测到代码块（``` 包裹的内容）保持完整，不切割
  - 默认 chunk_size 改为 800 字符
  - chunk 之间保留 100 字符的 overlap（重叠），确保跨 chunk 边界的上下文不断裂
- 验收标准：上传包含 2000 字符代码块的文档 → 代码块不被切碎

**2. 搜索结果排序优化**
- 文件位置：`processing/vector_store.py` `query()` 方法
- 当前问题：只取了 top_k=5，但未对 distance 做阈值过滤，可能返回语义完全不相关的结果
- 预期方案：增加 `distance_threshold` 参数（默认 1.5），超过此阈值的结果丢弃
- 验收标准：搜索一个知识库中完全不存在的概念 → 返回空结果而非强行匹配

**3. RAG 搜索支持标签过滤**
- 文件位置：`endpoints/rag.py` `rag_query()`
- 当前支持：`category_id` 过滤
- 新增：`tags` 参数过滤（如 `["python", "async"]`），多个标签 AND 逻辑
- ChromaDB where 条件：`{"$and": [{"category": "Python"}, {"tags": {"$contains": "async"}}]}`
- 验收标准：`POST /rag/query {"question": "...", "tags": ["python"]}` → 只搜索带 python 标签的文档

#### P1 - 重要

**4. 文档重新向量化**
- 场景：文档内容编辑后需要重新分块 + 向量化
- 新增方法：`VectorStore.update_document(doc_id, title, new_chunks, category, tags)`
- 行为：先删除旧 chunks，再添加新 chunks（当前 `add_document` 已有此逻辑，抽取为独立方法）
- 验收标准：编辑文档后，旧内容不再出现在搜索结果中

**5. Embedding 缓存**
- 问题：相同文本重复 embedding 浪费 API 调用
- 方案：对 chunk 文本做 MD5 哈希，已存在相同哈希的不重新 embedding
- 实现：内存 LRU cache（最多缓存 1000 条）
- 验收标准：上传相同内容的文档 → embedding 调用次数不增加

#### P2 - 锦上添花

**6. 混合搜索（Hybrid Search）**
- 当前只有语义搜索，增加关键词 BM25 搜索作为补充
- 最终结果 = 语义搜索结果 + BM25 结果（去重 + 加权合并）
- 验收标准：搜索精确术语（如函数名）→ 关键词匹配结果排在语义模糊匹配前面

### 6.4 依赖关系

- 依赖模块 D（AI Client）提供 embedding 和 chat
- 被模块 G（MCP Server）通过 API 调用
- 被模块 H（Inbox Watcher）调用入库

---

## 7. 模块 F：Chrome 扩展 (extension/)

### 7.1 功能描述

浏览器扩展，自动采集 AI 网站（Claude / ChatGPT / DeepSeek / Kimi / 豆包）的对话内容，回流到学习中枢知识库。

两种采集方式：
1. **自动采集**：每 30 秒增量扫描对话区，标签页关闭时自动回流传入 `/upload/text`
2. **手动采集**：页面右下角浮动按钮，点击立即采集当前对话

### 7.2 当前状态

框架完整。5 个 AI 网站的适配器已实现。后台自动采集 + 手动按钮采集均已工作。

### 7.3 开发者任务清单

#### P0 - 必须完成

**1. DOM 选择器维护机制**
- 文件位置：`extension/adapters.js`
- 问题：AI 网站经常改版，DOM 结构变化导致选择器失效
- 当前：选择器硬编码在 `adapters.js` 中，失效后需手动更新扩展
- 方案一（推荐）：增加 `fallback` 链式选择器，当前主选择器无结果时自动尝试备选
  ```javascript
  selectors: {
    container: '[data-testid="user-message"]',  // 主选择器
    fallback: '.prose, [class*="message"], article',  // 备选链
  }
  ```
- 方案二（长期）：远端配置 — 扩展定期从后端拉取最新的选择器配置 JSON
- 验收标准：Claude 改版后（主选择器失效），扩展仍能通过 fallback 提取到对话

**2. 采集内容去重优化**
- 当前问题：`lastSnapshot` 通过字符串 slice 做增量，但如果页面 DOM 重新渲染（如折叠再展开），会导致大量重复内容
- 预期方案：对每个消息块计算内容哈希，只采集新增的哈希对应的内容
- 验收标准：折叠再展开对话 → 不会重复采集已有内容

**3. 采集状态指示优化**
- 当前问题：浮动按钮采集成功后显示 "已采集 (xxx字)" 但 3 秒后恢复原状，用户可能不知道采集了哪些对话
- 新增：浏览器 badge 图标显示当前页面已采集的字数（`chrome.action.setBadgeText`）
- 验收标准：在 Claude 中对话后，扩展图标右上角显示字数角标

#### P1 - 重要

**4. 采集历史记录**
- 在 popup 弹窗中增加 "最近采集" 列表（最近 5 条）
- 数据存储：`chrome.storage.local`
- API：获取最近入库的文档 GET `/documents?source=ai_dialogue&limit=5`
- 验收标准：打开 popup → 看到 "今天 14:30 采集了 Claude对话 3200字" → 点击可跳转知识库

**5. 静默模式**
- 新增 popup 中的开关：开启后不显示浮动采集按钮，仅在后台默默采集
- 适用场景：不想让采集按钮遮挡页面内容
- 验收标准：开启静默模式 → 刷新 AI 页面 → 无浮动按钮 → 标签关闭后对话仍回流

#### P2 - 锦上添花

**6. 对话标签自动生成**
- 采集对话时调用 AI 生成 3-5 个标签（如 "Python" "异步" "装饰器"）
- 调用 `/rag/query` 或专门的标签生成 API
- 验收标准：采集的对话自动带有 AI 生成的标签

### 7.4 适配器维护规范

每当 AI 网站改版导致选择器失效，更新 `adapters.js`：

```javascript
// 每个适配器必须包含：
{
  name: "网站名",           // 显示名称
  selectors: {
    container: "主选择器",   // 最新的有效选择器
    fallback: "备选1, 备选2", // 逗号分隔的备选选择器链
  },
  extract(el) {             // 从 DOM 元素提取文本的函数
    return el.textContent.trim();
  }
}
```

---

## 8. 模块 G：MCP Server (mcp_server.py)

### 8.1 功能描述

让 Claude Desktop 通过 MCP 协议直接操作学习中枢知识库。Claude 可以在对话中搜索知识库、保存内容、查看复盘、生成周报。

### 8.2 MCP 工具清单（7 个）

| 工具名 | HTTP 调用 | 用途 |
|--------|----------|------|
| `search_knowledge_base` | `POST /rag/query` | 语义搜索 |
| `list_categories` | `GET /categories` | 分类列表 |
| `list_documents` | `GET /documents` | 文档列表 |
| `get_document` | `GET /documents/{id}` | 文档详情 |
| `save_to_knowledge_base` | `POST /upload/text` | 保存文本 |
| `polish_review` | `POST /review/polish` | 润色笔记 |
| `get_review_list` | `GET /review/list` | 复盘列表 |
| `get_weekly_report` | `GET /review/weekly` | 周报 |

### 8.3 开发者任务清单

#### P0 - 必须完成

**1. 文档删除工具**
- 新增 MCP 工具：`delete_document`
- 参数：`doc_id` (integer)
- 调用：`DELETE /documents/{doc_id}`（等后端实现后对接）
- 验收标准：Claude 对话中说 "删除文档 3" → 调用 `delete_document` → 文档删除

**2. search_knowledge_base 返回结果增强**
- 当前问题：搜索结果只返回 answer 文本，没有展示 chunk 内容细节
- 预期：返回中包含 top-3 匹配的 chunk 摘要（前 200 字符），帮助用户判断相关性
- 验收标准：搜索后不仅看到 AI 回答，还能看到 "匹配片段 1: xxx…"

**3. 连接错误信息优化**
- 当前返回：`"错误：无法连接到 study-hub 后端。请确保后端已启动"`
- 预期增强：加上启动命令提示 `"请执行: cd study-hub && docker compose up -d 或 cd backend && python main.py"`
- 验收标准：后端未启动时，Claude 中返回的提示包含具体操作指令

#### P1 - 重要

**4. 工具执行进度反馈**
- 当前问题：`save_to_knowledge_base` 大文本时可能耗时较长，Claude 端无反馈
- 方案：对于可能耗时超过 3 秒的操作，先返回 "处理中…" 状态（实际上 MCP 不支持流式，但可以优化文本处理）
- 实现：超大文本（>50000 字）先截断提示，避免超时

**5. 新增 `get_document_by_title` 工具**
- 场景：用户说 "打开 Python 装饰器那篇文档"，只知道标题不知道 ID
- 实现：调用 `GET /documents?search=装饰器` 做标题模糊匹配
- 验收标准：Claude 中说 "打开装饰器那篇" → 找到并返回文档内容

#### P2 - 锦上添花

**6. MCP 工具使用统计**
- 记录每个工具的调用次数、成功率
- 提供 `get_mcp_stats` 工具查看

### 8.4 依赖关系

- 依赖后端全部 API 正常运行
- 依赖模块 E（RAG）的搜索能力
- 依赖模块 I（每日复盘）的润色/周报能力

---

## 9. 模块 H：Inbox Watcher (watcher.py)

### 9.1 功能描述

监听 `backend/data/inbox/` 文件夹，任何新放入的 `.txt` `.md` `.pdf` 文件自动完成：读取 → 分块 → 向量化 → 入库 → 移至 processed 文件夹。

### 9.2 当前状态

基本功能完整。支持 txt/md/pdf 三种格式。处理完毕后将文件移动到 `processed/` 子目录。

### 9.3 开发者任务清单

#### P0 - 必须完成

**1. PDF 中文提取优化**
- 当前使用 PyMuPDF (fitz) 提取文本，对中文 PDF 可能存在编码问题
- 预期：提取后检查文本中中文比例，如果异常（如全是乱码）记录 warning
- 验收标准：上传中文 PDF → 提取的文本中文比例 > 80%

**2. 文件重名处理**
- 当前 `_archive` 方法通过加时间戳避免重名覆盖，但未考虑同一文件多次放入的场景
- 预期增强：如果文件内容的 MD5 与知识库中已有文档相同，跳过重复入库，直接归档
- 验收标准：同一个文件拖入两次 → 第二次跳过，控制台输出 "已存在，跳过"

#### P1 - 重要

**3. 大文件处理优化**
- 当前问题：大文件（>1MB）一次性读取 + 分段 embedding 可能内存溢出或超时
- 预期方案：文件超过 2MB 时打印 warning，超过 10MB 时跳过并通知
- 验收标准：拖入 15MB 的 txt 文件 → 不崩溃，控制台输出 "文件过大，跳过"

**4. 处理状态前端展示**
- 场景：用户拖入多个文件，想知道处理进度
- 方案：新增 `GET /inbox/status` 接口，返回最近处理记录（成功/失败 + 时间）
- 前端：在知识库卡片中添加 "最近入库" 列表
- 验收标准：拖入文件后刷新页面，看到 "xxx.md 已于 14:30 入库"

#### P2 - 锦上添花

**5. 支持更多格式**
- Markdown 变体：`.mdx` `.rst`
- 代码文件：`.py` `.js` `.ts` `.go` `.rs` 等（作为纯文本入库，标记 content_type 为对应语言）

### 9.4 依赖关系

- 依赖模块 E（RAG）的 chunker 和 vector_store
- 被模块 C（Backend Core）在 lifespan 中启动和停止

---

## 10. 模块 I：每日复盘系统 (review.py)

### 10.1 功能描述

用户写学习笔记 → AI 润色成结构化总结 → 给出学习建议 → 推荐知识库关联内容。

数据沉淀：所有复盘存入 `daily_reviews` 表，支持回顾历史和周报生成。

### 10.2 当前状态

核心功能完整。润色/周报/历史列表均已实现。

### 10.3 开发者任务清单

#### P0 - 必须完成

**1. AI 输出 JSON 解析鲁棒性增强**
- 文件位置：`endpoints/review.py` 第 60-69 行
- 当前问题：AI 可能不按 JSON 格式输出（格式错误、多了解释文字等），当前靠 `{` 和 `}` 截取，容错性一般
- 预期增强：
  - 增加 ` ```json ``` ` 代码块提取逻辑
  - 如果完全无法 parse，将原始 AI 输出作为 polished 文本，不丟失数据
  - 记录 parse 失败次数到日志
- 验收标准：AI 返回格式不规范时，仍然能提取到润色文本

**2. 复盘关联文档展示**
- 当前问题：`related_docs` 只返回文档名列表，前端不可点击跳转
- 预期增强：返回格式改为 `[{"id": 1, "title": "Python 装饰器"}, ...]`
- 前端配合：渲染为可点击链接，点击打开文档内容弹窗
- 验收标准：复盘结果中的关联推荐可点击跳转到文档详情

**3. 周报日期范围确认**
- 当前问题：`weekly_report` 硬编码取最近 7 天，但 "本周" 的定义应该是周一到周日
- 预期行为：计算本周一的日期，从此日期开始取数据
- 验收标准：周三查看周报 → 显示的是本周一至今的复盘，而非上周三至今

#### P1 - 重要

**4. 复盘模板系统**
- 场景：不同用户有不同的复盘风格（有人喜欢 bullet points，有人喜欢段落叙述）
- 新增：`REVIEW_TEMPLATES` 配置，支持自定义 prompt 模板
- 默认模板："学习总结 + 知识盲区 + 明日计划"
- 存储：localStorage（前端选择模板，附带在请求中）
- 验收标准：选择 "简明版" 模板 → AI 输出风格变为简短 bullet points

**5. 连续打卡功能**
- 新增：记录用户连续复盘天数
- 前端：仪表盘复盘卡片显示 "已连续复盘 X 天" 
- API：`GET /review/streak` 返回连续天数和最长连续天数
- 验收标准：连续 7 天写复盘 → 显示 🔥 7 天

#### P2 - 锦上添花

**6. 学习趋势分析**
- 基于历史复盘数据，AI 分析用户的学习趋势
- 新增：`GET /review/trends` → 本月学了什么、下个月建议学什么
- 验收标准：每月生成一份 "学习趋势报告"

### 10.4 REVIEW_SYSTEM_PROMPT 规范

当前 system prompt 要求 AI 输出 JSON 格式。修改 prompt 时需注意：
- 必须明确要求 `严格 JSON，不要加任何解释文字`
- `suggestions` 数组长度 2-3 条，每条不超过 50 字
- `related` 数组只推荐知识库中实际存在的文档

---

## 11. 接口契约（模块间通信约定）

### 11.1 前端 ↔ 后端

- 协议：HTTP REST
- 格式：JSON（请求和响应）
- 错误格式：`{"error": "错误描述", "detail": "可选详细"}`
- 上传文件：`multipart/form-data`
- API_BASE：前端通过 `localStorage.getItem('api_base')` 或 `window.location.origin` 自动检测
- 默认端口：`8741`

### 11.2 Chrome 扩展 ↔ 后端

- 同上 HTTP REST
- API_BASE 通过 `chrome.storage.sync` 保存，默认 `http://localhost:8741`
- 标签关闭时回流使用 `chrome.storage.session`（会话级别，关闭浏览器自动清空）

### 11.3 MCP Server ↔ 后端

- 协议：HTTP REST（MCP Server 作为 HTTP 客户端调用后端 API）
- MCP Server 不直接操作数据库，所有操作通过 API
- 超时：chat/embed 类操作 120s，其他 30s

### 11.4 后端内部

- AI Client 是单例（`ai_client = AIClient()`）
- VectorStore 是单例（`get_vector_store()` 返回全局实例）
- 数据库连接每次请求创建（`get_db()`），用后即关
- Inbox Watcher 在独立线程运行（watchdog Observer）

### 11.5 关键约定

1. **文档 ID 跨系统一致**：SQLite 的 `documents.id` 和 ChromaDB metadata 的 `doc_id` 必须同步
2. **分类名和 ID 映射**：ChromaDB metadata 存分类名（字符串），SQLite 存 category_id（整数），修改分类名时需要同步更新 ChromaDB
3. **标签存储格式**：SQLite 存 JSON 数组字符串 `'["tag1", "tag2"]'`，ChromaDB 存逗号分隔字符串 `"tag1,tag2"`
4. **字符编码**：全链路 UTF-8
5. **时间格式**：统一 ISO 8601（`YYYY-MM-DD` 或 `YYYY-MM-DDTHH:MM:SS`）

---

## 12. 验收标准总表

### 12.1 功能验收

| 编号 | 功能场景 | 操作 | 预期结果 | 涉及模块 |
|------|---------|------|---------|---------|
| FT-01 | 文档上传 | 上传 test.md | 知识库列表出现该文档，可搜索到内容 | A, C, E |
| FT-02 | 语义搜索 | 搜索 "装饰器" | 返回 AI 回答 + 引用的文档列表 | A, C, D, E |
| FT-03 | 文件拖入 | 拖入 test.md 到 inbox | 自动入库，文件移动到 processed | C, E, H |
| FT-04 | AI 对话采集 | 在 Claude 中对话后关标签 | 对话内容出现在知识库 | C, F |
| FT-05 | 每日复盘 | 写笔记 → 点润色 | 显示润色总结 + 学习建议 + 关联文档 | A, C, D, I |
| FT-06 | 周报 | 有 3 天复盘 → 点周报 | 生成包含概览、收获、建议的周报 | A, C, D, I |
| FT-07 | MCP 搜索 | Claude 中说 "搜知识库" | 返回 AI 回答 + 来源 | C, D, E, G |
| FT-08 | 分类管理 | 创建分类 → 移动文档 | 文档出现在目标分类下 | B, C |
| FT-09 | 文档删除 | 删除文档 | 数据库和向量库同步删除 | B, C, E |
| FT-10 | 批量操作 | 选中文档 → 批量移动/删除 | 所有选中文档操作成功 | B, C, E |

### 12.2 非功能验收

| 编号 | 指标 | 标准 | 验证方式 |
|------|------|------|---------|
| NF-01 | API 响应时间 | `/rag/query` P95 < 5s | 本地测试 10 次取 P95 |
| NF-02 | 前端首屏加载 | index.html < 1s (不含 API 调用) | Chrome DevTools Lighthouse |
| NF-03 | 并发能力 | 5 个并发上传不崩溃 | 同时上传 5 个文件 |
| NF-04 | 数据一致性 | 删文档后 ChromaDB 同步清空 | 删文档 → 搜索该文档内容 → 无结果 |
| NF-05 | 错误处理 | 后端不可用时前端不白屏 | 停掉后端 → 刷新页面 → 显示提示而非白屏 |
| NF-06 | 内存占用 | 后端空闲 < 200MB, 含 ChromaDB < 500MB | 任务管理器 |

---

## 附录 A：开发环境搭建

```bash
# 后端
cd study-hub/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env
# 编辑 .env，至少填入 CLAUDE_API_KEY
python main.py
# 访问 http://localhost:8741

# 前端直接打开文件即可，无需构建

# Chrome 扩展
# chrome://extensions → 开发者模式 → 加载已解压 → 选 extension/ 目录
```

## 附录 B：当前已知问题速查

| 问题 | 严重程度 | 涉及模块 | 状态 |
|------|---------|---------|------|
| 缺少文档删除 API | 高 | C | 待开发 |
| 缺少批量删除 API | 中 | C | 待开发 |
| 前端分类下拉框无数据 | 中 | A | 待开发 |
| AI Client 默认 provider 写死 kimi | 中 | D | 待修复 |
| embed 使用同步 HTTP 阻塞事件循环 | 中 | D | 待修复 |
| AI 网站 DOM 选择器可能随时失效 | 中 | F | 需监控 |
| kb.html 文档详情弹窗功能简陋 | 低 | B | 待增强 |
| 缺少文档编辑 API | 低 | C | 待开发 |

---

*本文档由产品经理维护。每个迭代开始前更新，迭代结束后根据实际完成情况修订。*
