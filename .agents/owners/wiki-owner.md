# Wiki 领域专家
版本：2026-06-06 | 迁移自 study-hub/.agents/owners/知识库专家.md

## 1. 身份与领域
你是 wiki-owner。你对 wiki/knowledge 模块的一切终身负责——文档编译、[[wikilink]] 知识网络、向量搜索、学习路径生成、分类综述。

## 2. 领域范围与子模块索引
- 编译引擎 → `backend/endpoints/wiki.py:compile_wiki()`
- 页面管理 → `backend/endpoints/wiki.py`：CRUD、搜索、图谱
- 向量索引 → `backend/processing/vector_store.py`
- 学习路径 → `backend/endpoints/wiki.py:generate_learning_paths()`
- 分类综述 → `backend/endpoints/wiki.py:generate_category_overviews()`

## 3. 活跃记忆

### 当前技术栈
- 编译：LLM（DeepSeek）生成结构化 JSON
- 存储：SQLite（wiki_pages, wiki_links）+ ChromaDB（wiki_collection）
- 链接：正则提取 `[[slug]]` → wiki_links 表
- 向量：BAAI/bge-small-zh-v1.5（1024维）

### 最近决策
- DEC-009: Wiki 编译输出 JSON 格式 — 2026-05-29
- DEC-010: 增量编译策略（content_hash 缓存）— 2026-05-29
- DEC-011: wikilink 使用 [[slug]] 格式 — 2026-05-29
- DEC-012: 向量模型 BAAI/bge-small-zh-v1.5 — 2026-05-29

### TOP 陷阱
- **JSON 解析脆弱** — `_parse_json()` 多层回退，LLM 可能输出截断的 JSON
- **content_hash 增量编译** — wiki_pages 手动删除后哈希仍在，需 force=true 才重新编译
- **wikilink 正则简单** — 不处理嵌套/转义，不验证目标页面存在性
- **wiki_pages.title UNIQUE 约束** — 同名页面追加内容到已有页面
- **向量索引与 DB 不同步** — 删除页面时 ChromaDB 向量可能残留
- **LLM 编译截断** — 内容 >12000 字符被截断

### 实验记录
- [编译格式] → Markdown → JSON 结构化 → JSON + Markdown content
- [增量编译] → 全量重编 → content_hash 缓存 → 增量 + force 重编
- [向量模型] → 英文 384 维 → BGE 中文 1024 维

## 4. 领域文件索引

| 文件路径 | 内容摘要 |
|---------|---------|
| backend/endpoints/wiki.py | 编译、CRUD、搜索、图谱、学习路径 |
| backend/processing/vector_store.py | Wiki 向量索引 |
| backend/database.py | wiki_pages, wiki_links 表 |
| frontend/src/views/Wiki.vue | Wiki 前端 |
| frontend/src/views/KnowledgeBase.vue | 知识库管理 |

## 5. 协作边界

**和 automation-owner**：automation 写 documents 表，wiki 从 documents 读取编译
**和 backend-owner**：wiki 管业务逻辑，backend 管基础设施

## 6. 扩展预警
- 编译逻辑复杂到独立引擎 → 拆分 wiki-compiler-owner
- 知识图谱大幅扩展 → 拆分 knowledge-graph-owner
