# 学习中枢 Study Hub

浏览器新标签页，作为所有学习工具的起点。五个核心模块：搜索框、常用网站、AI 启动器、RAG 知识库、每日复盘。

与 Claude 双向打通 —— 知识库文档一键发送到 Claude，Claude 对话自动回流知识库。

---

## 产品定位

**一句话**：把浏览器新标签页变成学习操作系统 —— 从"我该学什么"到"我学到了什么"形成闭环。

**核心痛点**：
- 学习工具分散（Claude / ChatGPT / DeepSeek / 笔记 / 资料），切换成本高
- 和 AI 的对话是宝贵的知识资产，但对话结束就丢了
- 知识碎片化，缺乏积累和回顾机制

**解决方案**：一个页面聚合所有学习入口，自动采集 AI 对话存入知识库，AI 辅助每日复盘形成学习闭环。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        浏览器新标签页 (Frontend)                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐        │
│  │ 搜索入口  │ 常用网站  │ AI启动器  │ 知识库卡片 │ 每日复盘  │        │
│  └────┬─────┴──────────┴──────────┴────┬─────┴────┬─────┘        │
│       │         localStorage           │          │              │
└───────┼────────────────────────────────┼──────────┼──────────────┘
        │                                │          │
        ▼                                ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Python 后端 (FastAPI :8741)                  │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐        │
│  │ /upload  │  /rag    │ /review  │/categories│ /inbox  │        │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘        │
│       │          │          │          │          │              │
│  ┌────┴──────────┴──────────┴──────────┴──────────┴────┐        │
│  │              AI Client (多 Provider 适配)              │        │
│  │   Claude / Kimi / DeepSeek / 豆包 → chat & embed      │        │
│  └────────────────────────┬────────────────────────────┘        │
│  ┌──────────┬─────────────┴──────────────┬──────────┐           │
│  │ SQLite   │   ChromaDB (向量存储)       │ Inbox    │           │
│  │ 文档/复盘 │   语义搜索                  │ Watcher  │           │
│  └──────────┴────────────────────────────┴──────────┘           │
└─────────────────────────────────────────────────────────────────┘
        ▲                                            │
        │ MCP (stdio)                                 │ HTTP
        │                                            ▼
┌───────────────┐                          ┌─────────────────┐
│ Claude Desktop│                          │ Chrome 扩展       │
│ (MCP Server)  │                          │ 对话自动采集      │
└───────────────┘                          └─────────────────┘
```

---

## 模块总览

| 模块 | 技术栈 | 负责人 | 核心职责 |
|------|--------|--------|----------|
| Frontend | HTML/CSS/JS 原生 | 前端开发 | 新标签页 UI + 知识库管理页 |
| Backend Core | Python FastAPI | 后端开发 | API 路由 + 数据库 + 生命周期 |
| AI Client | Python httpx | 后端开发 | 多 AI Provider 统一适配 |
| RAG 知识库 | ChromaDB + sentence-transformers | 后端开发 | 文档分块 + 向量化 + 语义搜索 |
| Chrome 扩展 | JS (MV3) | 扩展开发 | AI 对话自动采集 + 注入按钮 |
| MCP Server | Python mcp | 集成开发 | Claude Desktop 双向集成 |
| Inbox Watcher | Python watchdog | 后端开发 | 文件夹监听 + 自动入库 |
| 每日复盘 | Python + AI | 后端开发 | AI 润色 + 周报生成 |

---

## 快速启动（Docker，推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url> && cd study-hub

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入一个 AI API Key（CLAUDE_API_KEY）

# 3. 一键启动
docker compose up -d

# 4. 打开浏览器
# 访问 http://localhost:8741
```

首次启动会自动下载中文 embedding 模型（~95MB），后续启动无需等待。

## 快速启动（本地 Python）

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env，填入 API Key

# 4. 启动
cd backend && python main.py
# 访问 http://localhost:8741
```

## Claude Desktop 深度集成（MCP）

### 配置 MCP Server

在 Claude Desktop 配置文件中添加（Windows 路径：`%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "study-hub": {
      "command": "python",
      "args": ["F:\\360MoveData\\Users\\Administrator\\Desktop\\study web\\study-hub\\mcp_server.py"],
      "env": {
        "STUDY_HUB_API_BASE": "http://localhost:8741"
      }
    }
  }
}
```

配置后重启 Claude Desktop，在对话中即可使用以下工具：

| 工具 | 用途 | 示例 |
|------|------|------|
| `search_knowledge_base` | 搜索知识库 | "帮我搜一下装饰器相关内容" |
| `list_documents` | 列出最近文档 | "知识库里有哪些文档" |
| `get_document` | 读取文档全文 | "打开文档 3" |
| `save_to_knowledge_base` | 保存到知识库 | "把这段对话存入知识库" |
| `polish_review` | AI 润色笔记 | "帮我润色今天的学习笔记" |
| `get_review_list` | 查看历史复盘 | "看看之前的复盘记录" |
| `get_weekly_report` | 生成周报 | "生成本周学习周报" |

### 依赖安装

```bash
pip install -r requirements-mcp.txt
```

## 收件箱自动入库

把任意 `txt / md / pdf` 文件丢进 `backend/data/inbox/` 文件夹，自动导入知识库（分块 + 向量化）。

**适用场景：**
- Claude Desktop 对话导出后拖入
- 网页文章另存为 txt/md 拖入
- 任何文本内容只要丢进去就自动入库

## Web 端补充

### 知识库 → Claude Desktop
- 知识库文档旁「发送到 Claude Desktop」→ 复制全文，Ctrl+V 粘贴到 Claude Desktop

### Claude → 知识库（三种方式）
1. **收件箱**：Claude Desktop 导出对话 → 拖入 inbox 文件夹 → 自动入库
2. **MCP 对话中保存**：在 Claude 中说「保存到知识库」
3. **手动粘贴**：前端「粘贴 Claude 对话」入口

## 安装浏览器扩展

1. 打开 `chrome://extensions`，开启开发者模式
2. 「加载已解压的扩展程序」→ 选择 `extension/` 目录
3. 点扩展图标，配置后端地址

## 环境变量（.env）

| 变量 | 说明 | 示例 |
|------|------|------|
| `CLAUDE_API_KEY` | Claude API Key | `sk-ant-...` |
| `CLAUDE_MODEL` | Claude 模型 | `claude-sonnet-4-6` |
| `AI_DEFAULT_PROVIDER` | 默认 AI | `claude` |
| `HF_ENDPOINT` | HF 镜像（国内） | `https://hf-mirror.com` |
| `PORT` | 服务端口 | `8741` |

## 使用说明

- **搜索框**：直接输入搜知识库，`!` 前缀搜全网，`>` 前缀快捷命令
- **常用网站**：右键编辑/删除，点击 + 添加
- **AI 启动器**：点击打开 AI 网站，扩展自动采集对话
- **知识库**：上传 txt/md/pdf，AI 基于你的资料回答
- **每日复盘**：写笔记 → AI 润色 → 关联知识库

## 项目结构

```
study-hub/
├── frontend/
│   ├── index.html             # 新标签页（仪表盘）
│   └── kb.html                # 知识库管理页
├── backend/                   # Python 后端
│   ├── main.py                # FastAPI 入口 + 生命周期
│   ├── ai_client.py           # 多 AI Provider 适配层
│   ├── database.py            # SQLite 数据库初始化
│   ├── watcher.py             # 收件箱文件夹监听
│   ├── requirements.txt       # Python 依赖
│   ├── start.bat              # Windows 启动脚本
│   ├── endpoints/
│   │   ├── upload.py          # 文件上传 / 文本存入
│   │   ├── rag.py             # RAG 语义搜索
│   │   ├── review.py          # 每日复盘 / 周报
│   │   └── categories.py      # 分类管理 CRUD
│   ├── processing/
│   │   ├── chunker.py         # 文本分块
│   │   └── vector_store.py   # ChromaDB 向量存储
│   └── data/                  # 运行时数据（SQLite / Chroma / inbox）
├── extension/                 # Chrome 扩展 (MV3)
│   ├── manifest.json          # 扩展配置
│   ├── background.js          # Service Worker (标签关闭时回流)
│   ├── content.js             # 对话提取 + 注入浮动按钮
│   ├── popup.html / popup.js  # 扩展弹窗
│   └── adapters.js           # 各 AI 网站 DOM 适配器
├── mcp_server.py              # MCP Server (Claude Desktop ↔ Study Hub)
├── requirements-mcp.txt       # MCP 依赖
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── 启动.bat
└── README.md
```

<!-- AUTO-GENERATED-START -->

<!-- 自动生成于 2026-05-01 19:33 UTC，请勿手动编辑此区块 -->

## API 路由全览

### 端点 (endpoints/)

| 方法 | 路径 | 处理函数 | 关键参数 | 文件 |
|------|------|----------|----------|------|
| GET | `/automation/modules` | `list_modules()` |  | `21` |
| POST | `/automation/run` | `run_automation()` | payload | `29` |
| GET | `/categories` | `list_categories()` |  | `8` |
| POST | `/categories` | `create_category()` | payload | `22` |
| PUT | `/categories/{cat_id}` | `update_category()` | cat_id, payload | `47` |
| DELETE | `/categories/{cat_id}` | `delete_category()` | cat_id | `69` |
| PUT | `/documents/{doc_id}/move` | `move_document()` | doc_id, payload | `84` |
| PUT | `/documents/batch-move` | `batch_move_documents()` | payload | `124` |
| PUT | `/documents/{doc_id}/tags` | `update_document_tags()` | doc_id, payload | `167` |
| POST | `/rag/query` | `rag_query()` | payload | `26` |
| POST | `/review/polish` | `polish_review()` | payload | `24` |
| GET | `/review/list` | `list_reviews()` |  | `94` |
| GET | `/review/weekly` | `weekly_report()` |  | `104` |
| POST | `/upload` | `upload_file()` | file | `18` |
| POST | `/upload/text` | `upload_text()` | payload | `62` |
| GET | `/documents` | `list_documents()` | category_id | `104` |
| GET | `/documents/{doc_id}` | `get_document()` | doc_id | `127` |
| DELETE | `/documents/{doc_id}` | `delete_document()` | doc_id | `143` |
| POST | `/documents/batch-delete` | `batch_delete_documents()` | payload | `168` |

### MCP Server 工具（供 Claude Desktop 调用）

| 工具名 | 用途 |
|--------|------|
| `search_knowledge_base` | 在知识库中语义搜索。输入自然语言问题，返回基于你已上传文档的 AI 回答和相关来源。可指定分类名缩小搜索范围。 |
| `list_categories` | 列出知识库的所有分类及其文档数量。 |
| `list_documents` | 列出知识库中最近上传的文档列表。可按分类筛选。 |
| `get_document` | 获取指定文档的完整内容。 |
| `save_to_knowledge_base` | 将文本内容保存到知识库。适用于保存 Claude 对话总结、分析结果、或任何你想日后检索的内容。 |
| `polish_review` | AI 润色学习笔记。输入原始笔记，返回润色后的总结 + 学习建议 + 知识库关联推荐。 |
| `get_review_list` | 获取历史每日复盘列表。 |
| `get_weekly_report` | 生成本周学习周报。基于本周的每日复盘，AI 汇总生成。 |

## 数据库表结构

### `categories` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `name` | TEXT |
| `icon` | TEXT DEFAULT '📁' |
| `color` | TEXT ' |
| `sort_order` | INTEGER |
| `created_at` | TIMESTAMP |

### `documents` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `title` | TEXT |
| `content` | TEXT |
| `content_type` | TEXT ' |
| `source` | TEXT ' |
| `category_id` | INTEGER |
| `tags` | TEXT DEFAULT '[]' |
| `content_hash` | TEXT DEFAULT '' |
| `char_count` | INTEGER |
| `chunk_count` | INTEGER |
| `created_at` | TIMESTAMP |

### `daily_reviews` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `date` | TEXT |
| `raw_text` | TEXT |
| `polished` | TEXT |
| `suggestions` | TEXT |
| `related_docs` | TEXT |
| `created_at` | TIMESTAMP |

## 环境变量 (.env)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CLAUDE_API_KEY` | `sk-ant-xxx` |  |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` |  |
| `AI_DEFAULT_PROVIDER` | `claude` |  |
| `HF_ENDPOINT` | `https://hf-mirror.com` |  |
| `PORT` | `8741` |  |

## 后端核心文件

#### `backend/main.py` (74 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/health` | `health()` |  |
| GET | `/inbox/open` | `open_inbox()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `lifespan` | `(app: FastAPI)` | - |
| `health` | `()` | - |
| `open_inbox` | `()` | - |

**关键依赖：**
- `from fastapi import FastAPI`
- `from fastapi.middleware.cors import CORSMiddleware`
- `from fastapi.staticfiles import StaticFiles`
- `from database import init_db`
- `from endpoints.upload import router as upload_router`
- `from endpoints.rag import router as rag_router`
- `from endpoints.review import router as review_router`
- `from endpoints.categories import router as categories_router`
- `from endpoints.automation import router as automation_router`
- `from watcher import start_watcher`

---
#### `backend/ai_client.py` (152 行)

**类 `AIClient`** — 行 29

| 函数 | 签名 | 说明 |
|------|------|------|
|   ⮑ `__init__` | `(self)` | - |
|   ⮑ `default_provider` | `(self)` | - |
|   ⮑ `chat` | `(self, messages, provider=None, temperature=0.7, max_tokens=2048)` | messages: [{"role": "system"|"user"|"assistant", "content": "..."}] 返回: str |
|   ⮑ `embed` | `(self, texts: list[str], provider=None) -> list[list[float]]` | 文本向量化。使用 OpenAI 兼容的 /embeddings 接口。 Claude 不支持 embeddings，会自动选择其他可用 provider。 |
|   ⮑ `list_providers` | `(self)` | - |

**关键依赖：**
- `import httpx`

---
#### `backend/database.py` (63 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_db` | `()` | - |
| `init_db` | `()` | - |

---
#### `backend/watcher.py` (118 行)

**类 `InboxHandler`** (继承 `FileSystemEventHandler`) — 行 16

| 函数 | 签名 | 说明 |
|------|------|------|
|   ⮑ `on_created` | `(self, event)` | - |
|   ⮑ `on_moved` | `(self, event)` | - |
| `start_watcher` | `()` | - |
| `stop_watcher` | `()` | - |

**关键依赖：**
- `from watchdog.observers import Observer`
- `from watchdog.events import FileSystemEventHandler`
- `from processing.processors import can_handle, process_path, is_duplicate`
- `from database import get_db`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`

---
## 后端处理层 (processing/)

#### `backend/processing/chunker.py` (37 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `chunk_text` | `(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]` | 将文本按句子边界分块，每块约 chunk_size 字符。 在句号、换行等自然断点处切开，不截断句子。 |

---
#### `backend/processing/processors.py` (71 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `register` | `(*extensions)` | 装饰器：把函数注册为指定扩展名的处理器 |
|   ⮑ `decorator` | `(fn)` | - |
| `can_handle` | `(ext: str) -> bool` | - |
| `process_bytes` | `(data: bytes, ext: str) -> str` | 二进制入口（PDF 等），按扩展名分发 |
| `sha256` | `(text: str) -> str` | - |
| `is_duplicate` | `(content_hash: str) -> bool` | 检查内容哈希是否已存在于数据库 |

**关键依赖：**
- `from database import get_db`

---
#### `backend/processing/vector_store.py` (98 行)

**类 `VectorStore`** — 行 12

| 函数 | 签名 | 说明 |
|------|------|------|
|   ⮑ `__init__` | `(self)` | - |
|   ⮑ `embed_fn` | `(self)` | - |
|   ⮑ `add_document` | `(self, doc_id: int, title: str, chunks: list[str], category: str = "", tags: str = "")` | - |
|   ⮑ `query` | `(self, question: str, top_k: int = 5, category: str = "") -> list[dict]` | - |
|   ⮑ `count` | `(self) -> int` | - |
| `get_vector_store` | `() -> VectorStore` | - |

**关键依赖：**
- `import chromadb`
- `from chromadb.config import Settings`
- `from sentence_transformers import SentenceTransformer`
- `from ai_client import ai_client`

---
## 后端端点层 (endpoints/)

#### `backend/endpoints/automation.py` (103 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/automation/modules` | `list_modules()` |  |
| POST | `/automation/run` | `run_automation()` | payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_modules` | `()` | - |
| `run_automation` | `(payload: dict)` | - |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`

---
#### `backend/endpoints/categories.py` (197 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/categories` | `list_categories()` |  |
| POST | `/categories` | `create_category()` | payload |
| PUT | `/categories/{cat_id}` | `update_category()` | cat_id, payload |
| DELETE | `/categories/{cat_id}` | `delete_category()` | cat_id |
| PUT | `/documents/{doc_id}/move` | `move_document()` | doc_id, payload |
| PUT | `/documents/batch-move` | `batch_move_documents()` | payload |
| PUT | `/documents/{doc_id}/tags` | `update_document_tags()` | doc_id, payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_categories` | `()` | - |
| `create_category` | `(payload: dict)` | - |
| `update_category` | `(cat_id: int, payload: dict)` | - |
| `delete_category` | `(cat_id: int)` | - |
| `move_document` | `(doc_id: int, payload: dict)` | 移动文档到指定分类，同时更新向量库 metadata |
| `batch_move_documents` | `(payload: dict)` | 批量移动文档到指定分类 |
| `update_document_tags` | `(doc_id: int, payload: dict)` | 更新文档标签 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`

---
#### `backend/endpoints/rag.py` (67 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/rag/query` | `rag_query()` | payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `rag_query` | `(payload: dict)` | - |

**关键依赖：**
- `from fastapi import APIRouter`
- `from processing.vector_store import get_vector_store`
- `from ai_client import ai_client`
- `from database import get_db`

---
#### `backend/endpoints/review.py` (129 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/review/polish` | `polish_review()` | payload |
| GET | `/review/list` | `list_reviews()` |  |
| GET | `/review/weekly` | `weekly_report()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `polish_review` | `(payload: dict)` | - |
| `list_reviews` | `()` | - |
| `weekly_report` | `()` | - |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`
- `from ai_client import ai_client`
- `from processing.vector_store import get_vector_store`

---
#### `backend/endpoints/upload.py` (191 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/upload` | `upload_file()` | file |
| POST | `/upload/text` | `upload_text()` | payload |
| GET | `/documents` | `list_documents()` | category_id |
| GET | `/documents/{doc_id}` | `get_document()` | doc_id |
| DELETE | `/documents/{doc_id}` | `delete_document()` | doc_id |
| POST | `/documents/batch-delete` | `batch_delete_documents()` | payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `upload_text` | `(payload: dict)` | - |
| `list_documents` | `(category_id: int = None)` | - |
| `get_document` | `(doc_id: int)` | - |
| `delete_document` | `(doc_id: int)` | - |
| `batch_delete_documents` | `(payload: dict)` | - |

**关键依赖：**
- `from fastapi import APIRouter, UploadFile, File, Form`
- `from database import get_db`
- `from processing.processors import can_handle, process_bytes, sha256, is_duplicate`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`

---
## MCP Server

#### `mcp_server.py` (287 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `api_get` | `(path: str) -> dict` | - |
| `api_post` | `(path: str, body: dict) -> dict` | - |
| `list_tools` | `() -> list[Tool]` | - |
| `call_tool` | `(name: str, arguments: dict) -> list[TextContent]` | - |
| `handle_search` | `(args: dict) -> list[TextContent]` | - |
| `handle_list_categories` | `(args: dict) -> list[TextContent]` | - |
| `handle_list_docs` | `(args: dict) -> list[TextContent]` | - |
| `handle_get_doc` | `(args: dict) -> list[TextContent]` | - |
| `handle_save` | `(args: dict) -> list[TextContent]` | - |
| `handle_polish` | `(args: dict) -> list[TextContent]` | - |
| `handle_review_list` | `(args: dict) -> list[TextContent]` | - |
| `handle_weekly` | `(args: dict) -> list[TextContent]` | - |
| `main` | `()` | - |

**关键依赖：**
- `import httpx`

---
## 前端页面

#### `extension/popup.html` (29 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `apiBase`, `saveBtn`, `captureBtn`, `status`

---
#### `frontend/index.html` (944 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **调用的 API：**
  - `/automation/run`
  - `/categories`
  - `/documents`
  - `/documents/${docId}`
  - `/documents/${id}`
  - `/inbox/open`
  - `/rag/query`
  - `/review/list`
  - `/review/polish`
  - `/review/weekly`
  - `/upload`
  - `/upload/text`
- **关键 DOM ID：** `searchInput`, `searchCategory`, `searchHint`, `searchResult`, `shortcutsGrid`, `aiGrid`, `fileInput`, `kbSearchBtn`, `pasteClaudeBtn`, `kbDocList`, `reviewInput`, `reviewPolishBtn`, `reviewWeeklyBtn`, `reviewStatus`, `reviewResult`, `reviewPolished`, `reviewSuggestions`, `reviewRelated`, `reviewHistory`, `reviewHistoryList`
- **JS 函数：**
  - `API_BASE(()` → 行 382
  - `qs(sel)` → 行 410
  - `qsa(sel)` → 行 411
  - `toast(msg, isError)` → 行 413
  - `getData(key, def)` → 行 421
  - `setData(key, val)` → 行 425
  - `renderShortcuts()` → 行 433
  - `deleteShortcut(e, idx)` → 行 451
  - `openShortcutModal(idx)` → 行 457
  - `renderAIs()` → 行 495
  - `launchAI(idx)` → 行 512
  - `openAIModal()` → 行 527
  - `doKBQuery(question)` → 行 573
  - `handleCommand(cmd)` → 行 605
  - `loadDocuments()` → 行 653
  - `openInbox()` → 行 681
  - `sendToClaude(docId, title)` → 行 706
  - `viewDocument(id)` → 行 752
  - `loadReviewHistory()` → 行 817
  - `viewReview(id)` → 行 831

---
#### `frontend/kb.html` (808 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **调用的 API：**
  - `/categories`
  - `/categories/${catId}`
  - `/categories/${editingCatId}`
  - `/documents`
  - `/documents/${docId}`
  - `/documents/${docId}/move`
  - `/documents/${editingTagDocId}/tags`
  - `/documents/${id}`
  - `/documents/batch-delete`
  - `/documents/batch-move`
  - `/upload`
  - `/upload/text`
- **关键 DOM ID：** `categoryList`, `currentTitle`, `docCount`, `searchBox`, `fileInput`, `pasteBtn`, `batchDeleteBtn`, `batchBar`, `batchCount`, `batchMoveSelect`, `batchMoveBtn`, `selectAll`, `docTableBody`, `emptyState`, `catModal`, `catModalTitle`, `catName`, `catIcon`, `colorPick`, `catColor`
- **JS 函数：**
  - `API_BASE(()` → 行 302
  - `toast(msg, isError)` → 行 310
  - `escapeHtml(str)` → 行 317
  - `pickColor(c)` → 行 332
  - `loadCategories()` → 行 349
  - `loadDocuments()` → 行 357
  - `renderCategories()` → 行 368
  - `selectCategory(catId)` → 行 414
  - `renderDocs()` → 行 426
  - `toggleDoc(id)` → 行 479
  - `toggleSelectAll()` → 行 487
  - `updateSelectAllCheckbox()` → 行 502
  - `clearSelection()` → 行 509
  - `updateBatchBar()` → 行 515
  - `moveDocPrompt(docId)` → 行 547
  - `batchDelete()` → 行 569
  - `deleteDoc(docId)` → 行 584
  - `openCatModal(catId)` → 行 598
  - `deleteCat(catId)` → 行 654
  - `viewDoc(id)` → 行 667

---
## Chrome 扩展

### 扩展配置
- **名称**: 学习中枢 - 对话采集
- **版本**: 1.1
- **权限**: `storage`, `tabs`, `scripting`, `activeTab`
- **Host 权限**: `https://claude.ai/*`, `https://chat.openai.com/*`, `https://chat.deepseek.com/*`, `https://kimi.moonshot.cn/*`, `https://www.doubao.com/*`

#### `extension/adapters.js` (68 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `getAdapter()` |  | 61 |

---
#### `extension/background.js` (42 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `getApiBase()` |  | 6 |

---
#### `extension/content.js` (129 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `extractCurrentDialogue()` |  | 14 |
| `scan()` |  | 31 |
| `injectCaptureButton()` |  | 50 |
| `getApiBase()` |  | 108 |

---
#### `extension/popup.js` (82 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `adapter()` | ( | 38 |

---
## 配置文件

### `backend/requirements.txt` (10 行, hash: `af77d8e1`)

```
python-dotenv>=1.0.0
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
PyMuPDF>=1.23.0
python-multipart>=0.0.6
httpx>=0.25.0
watchdog>=4.0.0

```

### `docker-compose.yml` (16 行, hash: `78dbf45d`)

```
services:
  study-hub:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "${PORT:-8741}:8741"
    volumes:
      - study-hub-data:/app/data
    env_file:
      - .env
    restart: unless-stopped

volumes:
  study-hub-data:

```

### `Dockerfile` (25 行, hash: `8aaaac61`)

```
FROM python:3.12-slim

WORKDIR /app

# 设置 HF 镜像（国内网络加速）
ENV HF_ENDPOINT=https://hf-mirror.com

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 MCP 依赖（供 mcp_server.py 使用）
COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

# 预下载 embedding 模型（避免首次启动等待）
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY backend/ .
COPY frontend/ /frontend
COPY mcp_server.py .

EXPOSE 8741

CMD ["python", "main.py"]

```

### `requirements-mcp.txt` (3 行, hash: `ecc021c2`)

```
mcp>=1.0.0
httpx>=0.25.0

```

## 文件完整性指纹

| 文件 | MD5 (前8位) | 行数 |
|------|-------------|------|
| `backend/ai_client.py` | `395258cd` | 152 |
| `backend/database.py` | `d6d1c5a7` | 63 |
| `backend/endpoints/__init__.py` | `d41d8cd9` | 1 |
| `backend/endpoints/automation.py` | `37ae55a3` | 103 |
| `backend/endpoints/categories.py` | `dd0573bd` | 197 |
| `backend/endpoints/rag.py` | `4960089e` | 67 |
| `backend/endpoints/review.py` | `cb81a7e6` | 129 |
| `backend/endpoints/upload.py` | `9598ab45` | 191 |
| `backend/main.py` | `63c1e9e7` | 74 |
| `backend/processing/__init__.py` | `d41d8cd9` | 1 |
| `backend/processing/chunker.py` | `3cebfd14` | 37 |
| `backend/processing/processors.py` | `733919b8` | 71 |
| `backend/processing/vector_store.py` | `7129c3ac` | 98 |
| `backend/watcher.py` | `8cf30998` | 118 |
| `extension/adapters.js` | `ae148a47` | 68 |
| `extension/background.js` | `28d6c291` | 42 |
| `extension/content.js` | `00de1e82` | 129 |
| `extension/popup.html` | `df2f95d0` | 29 |
| `extension/popup.js` | `f1d1d90a` | 82 |
| `frontend/index.html` | `b2495a38` | 944 |
| `frontend/kb.html` | `77027b79` | 808 |
| `mcp_server.py` | `b8673c50` | 287 |

<!-- 文件总数: 22, 生成时间: 2026-05-01 19:33 UTC -->
<!-- AUTO-GENERATED-END -->

## 技术选型决策记录

| 决策点 | 选择 | 理由 | 备选 |
|--------|------|------|------|
| 后端框架 | FastAPI | 异步支持好，自动生成 OpenAPI 文档 | Flask |
| 向量数据库 | ChromaDB | 嵌入式部署，零运维，适合单机场景 | Pinecone / Weaviate |
| Embedding 模型 | BAAI/bge-small-zh-v1.5 | 轻量本地运行，512 维，中文优化 | BAAI/bge-large-zh-v1.5 / API |
| 前端 | 原生 HTML/CSS/JS | 零构建步骤，新标签页对性能敏感 | React / Vue |
| 数据库 | SQLite | 单机部署，零配置，WAL 模式支持并发读 | PostgreSQL |
| AI 接入 | 统一适配层 | 支持 Claude / Kimi / DeepSeek / 豆包多 Provider | 单一 Provider |

## 待办事项 (Roadmap)

### P0
- [x] 文档删除 / 批量删除 API
- [x] 前端批量删除联调
- [x] 搜索分类筛选联调
- [ ] Docker 镜像瘦身（当前 ~3GB，目标 <2GB）

### P1
- [ ] 文档编辑功能
- [ ] 搜索历史记录
- [ ] 知识库全量导出
- [ ] 前端 API_BASE 配置 UI

### P2
- [ ] 多标签页支持
- [ ] 文档关联图谱
- [ ] 学习数据统计仪表盘
- [ ] 移动端适配
- [ ] 暗色/亮色主题切换
