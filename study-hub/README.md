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

<!-- 自动生成于 2026-05-09 18:30 UTC，请勿手动编辑此区块 -->

## API 路由全览

### 端点 (endpoints/)

| 方法 | 路径 | 处理函数 | 关键参数 | 文件 |
|------|------|----------|----------|------|
| POST | `/ai-search` | `ai_search()` | payload | `126` |
| GET | `/automation/modules` | `list_modules()` |  | `399` |
| POST | `/automation/run` | `run_automation()` | payload | `404` |
| POST | `/automation/queue` | `queue_tasks()` | payload | `434` |
| GET | `/automation/queue/status` | `queue_status()` |  | `474` |
| GET | `/automation/queue/{task_id}` | `task_status()` | task_id | `510` |
| DELETE | `/automation/queue/clear` | `clear_completed()` |  | `527` |
| POST | `/automation/reparse/{doc_id}` | `reparse_document()` | doc_id | `539` |
| GET | `/automation/reparseable` | `list_reparseable()` |  | `589` |
| POST | `/documents/cleanup` | `cleanup_documents()` | payload | `621` |
| POST | `/brainstorm/step2` | `brainstorm_step2()` | payload | `237` |
| POST | `/brainstorm/step3` | `brainstorm_step3()` | payload | `262` |
| GET | `/categories` | `list_categories()` |  | `8` |
| POST | `/categories` | `create_category()` | payload | `22` |
| PUT | `/categories/{cat_id}` | `update_category()` | cat_id, payload | `47` |
| DELETE | `/categories/{cat_id}` | `delete_category()` | cat_id | `69` |
| PUT | `/documents/{doc_id}/move` | `move_document()` | doc_id, payload | `84` |
| PUT | `/documents/batch-move` | `batch_move_documents()` | payload | `124` |
| PUT | `/documents/{doc_id}/tags` | `update_document_tags()` | doc_id, payload | `167` |
| POST | `/evolution/analyze` | `trigger_analysis()` | payload | `13` |
| GET | `/evolution/patches` | `list_patches()` | status, risk_level, limit | `38` |
| GET | `/evolution/patches/{patch_id}` | `get_patch()` | patch_id | `57` |
| POST | `/evolution/patches/{patch_id}/apply` | `apply_patch()` | patch_id | `68` |
| POST | `/evolution/patches/{patch_id}/reject` | `reject_patch()` | patch_id, payload | `99` |
| GET | `/evolution/snapshots` | `list_snapshots()` | limit | `121` |
| GET | `/evolution/snapshots/{snapshot_id}` | `get_snapshot()` | snapshot_id | `134` |
| POST | `/evolution/snapshots` | `create_manual_snapshot()` |  | `151` |
| GET | `/evolution/skills` | `get_skills()` |  | `193` |
| GET | `/evolution/skills/{skill_name}` | `get_skill()` | skill_name | `199` |
| GET | `/evolution/config` | `get_config()` |  | `208` |
| GET | `/export/all` | `export_all()` |  | `41` |
| GET | `/export/document/{doc_id}` | `export_document()` | doc_id | `95` |
| GET | `/documents/{doc_id}/links` | `get_document_links()` | doc_id | `43` |
| GET | `/documents/{doc_id}/backlinks` | `get_document_backlinks()` | doc_id | `68` |
| POST | `/rag/query` | `rag_query()` | payload | `65` |
| POST | `/review/polish` | `polish_review()` | payload | `24` |
| GET | `/review/list` | `list_reviews()` |  | `117` |
| GET | `/review/weekly` | `weekly_report()` |  | `127` |
| POST | `/upload` | `upload_file()` | file | `19` |
| POST | `/upload/text` | `upload_text()` | payload | `70` |
| GET | `/documents` | `()` |  | `118` |
| GET | `/documents/{doc_id}` | `get_document()` | doc_id | `160` |
| DELETE | `/documents/{doc_id}` | `delete_document()` | doc_id | `176` |
| POST | `/documents/batch-delete` | `batch_delete_documents()` | payload | `201` |
| POST | `/wiki/compile` | `compile_wiki()` | payload | `173` |
| GET | `/wiki/pages` | `list_wiki_pages()` | category, search | `309` |
| GET | `/wiki/pages/{page_id}` | `get_wiki_page()` | page_id | `338` |
| GET | `/wiki/graph` | `get_wiki_graph()` |  | `368` |
| GET | `/wiki/categories` | `get_wiki_categories()` |  | `406` |
| DELETE | `/wiki/pages/{page_id}` | `delete_wiki_page()` | page_id | `417` |
| PUT | `/wiki/pages/{page_id}` | `update_wiki_page()` | page_id, payload | `432` |
| DELETE | `/wiki/pages` | `delete_all_wiki_pages()` |  | `492` |
| POST | `/wiki/regenerate` | `regenerate_wiki()` |  | `502` |
| POST | `/wiki/search` | `search_wiki()` | payload | `520` |
| POST | `/wiki/reindex` | `reindex_wiki()` |  | `551` |
| POST | `/wiki/learning-paths` | `generate_learning_paths()` |  | `571` |
| POST | `/wiki/category-overviews` | `generate_category_overviews()` |  | `699` |

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
| `parse_bilibili_video_info` | 解析B站分享链接，获取视频基本信息（标题、封面、UP主、播放量、分P列表等）。支持 b23.tv 短链接、bilibili.com/video/ 完整链接、或直接BV号。 |
| `get_bilibili_download_link` | 获取B站视频/音频的下载链接。返回 Dash 流（音视频分离）和 durl 流（含音频的单文件），可指定分P和清晰度。 |
| `extract_bilibili_text` | 从B站视频中提取语音文本（AI语音识别）。自动获取音频流并使用阿里云百炼 qwen3-asr-flash 模型转为文字。需要 DASHSCOPE_API_KEY。 |
| `parse_xiaohongshu_note_info` | 解析小红书分享链接，获取笔记基本信息（标题、正文、图片、视频、作者、互动数据等）。支持 xhslink.com 短链接和 xiaohongshu.com/explore/ 标准链接。 |
| `extract_xiaohongshu_text` | 提取小红书笔记中的文字内容（标题 + 正文 + 标签 + 互动数据），返回Markdown格式。 |
| `get_xiaohongshu_media` | 获取小红书笔记中的图片和视频链接。返回封面、所有图片URL、视频URL等信息。 |
| `extract_xiaohongshu_video_text` | 从小红书视频笔记中提取语音文本（AI语音识别）。需要 DASHSCOPE_API_KEY。 |
| `recognize_audio_file` | 识别本地音频文件中的文本。支持 aac/amr/avi/flac/flv/m4a/mkv/mp3/mp4/wav/webm 等格式。需要 DASHSCOPE_API_KEY。 |
| `recognize_audio_url` | 识别在线音频URL中的文本。直接传入音频链接即可转文字。需要 DASHSCOPE_API_KEY。 |
| `compile_wiki` | 将知识库中的原始文档编译为结构化的 LLM Wiki 页面。AI 会自动提取知识点、建立交叉引用、检测矛盾。可指定文档 ID 列表编译特定文档，不指定则编译所有未编译过的文档。 |
| `search_wiki` | 搜索 Wiki 页面。返回匹配的 Wiki 页面列表。 |
| `get_wiki_page` | 获取指定 Wiki 页面的完整内容。包含页面正文、入链/出链、标签等。 |
| `list_wiki_pages` | 列出所有 Wiki 页面，可按分类筛选。 |
| `get_wiki_graph` | 获取 Wiki 知识图谱数据。返回所有页面节点和交叉引用边，用于可视化知识网络。 |
| `analyze_evolution` | 触发学习系统进化分析。基于最近学习的知识（Wiki页面、复盘内容），分析现有 Skills 可以如何改进，生成技能补丁。低风险补丁自动应用。 |
| `list_evolution_patches` | 列出所有技能补丁。可按状态和风险级别筛选。 |
| `apply_evolution_patch` | 手动应用一个待处理的技能补丁。 |
| `list_system_snapshots` | 列出系统快照。快照记录了 Skills、配置、Wiki 统计的每日状态。 |
| `get_system_snapshot` | 获取指定系统快照的完整内容。 |

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

### `wiki_pages` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `title` | TEXT |
| `slug` | TEXT |
| `content` | TEXT |
| `summary` | TEXT DEFAULT '' |
| `source_doc_ids` | TEXT DEFAULT '[]' |
| `cross_refs` | TEXT DEFAULT '[]' |
| `contradictions` | TEXT DEFAULT '[]' |
| `tags` | TEXT DEFAULT '[]' |
| `category` | TEXT DEFAULT '' |
| `version` | INTEGER |
| `char_count` | INTEGER |
| `created_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `wiki_links` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `source_page_id` | INTEGER |
| `target_page_slug` | TEXT |
| `link_type` | TEXT ' |
| `context` | TEXT DEFAULT '' |

### `skill_patches` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `skill_name` | TEXT |
| `patch_type` | TEXT  CHECK(patch_type IN ('add','replace','insert_after','insert_before','append')) |
| `target_section` | TEXT DEFAULT '' |
| `patch_content` | TEXT |
| `rationale` | TEXT DEFAULT '' |
| `source_event_type` | TEXT DEFAULT '' CHECK(source_event_type IN ('wiki_compile','review_polish','manual','')) |
| `source_event_id` | INTEGER |
| `risk_level` | TEXT  CHECK(risk_level IN ('low','medium','high')) |
| `status` | TEXT  ' CHECK(status IN ('pending','applied','rejected','superseded')) |
| `file_path` | TEXT DEFAULT '' |
| `created_at` | TIMESTAMP |
| `applied_at` | TIMESTAMP |
| `rejected_at` | TIMESTAMP |

### `document_links` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `source_doc_id` | INTEGER |
| `target_title` | TEXT |
| `target_doc_id` | INTEGER |
| `link_text` | TEXT DEFAULT '' |

### `system_snapshots` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `snapshot_type` | TEXT  CHECK(snapshot_type IN ('daily','weekly','manual')) |
| `snapshot_date` | TEXT |
| `skills_json` | TEXT  DEFAULT '[]' |
| `config_json` | TEXT  DEFAULT '{}' |
| `wiki_stats_json` | TEXT  DEFAULT '{}' |
| `review_summary` | TEXT DEFAULT '' |
| `evolution_notes` | TEXT DEFAULT '' |
| `patch_ids_applied` | TEXT DEFAULT '[]' |
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

#### `backend/main.py` (94 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/health` | `health()` |  |
| GET | `/inbox/open` | `open_inbox()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `lifespan` | `(app: FastAPI)` | - |
| `health` | `()` | - |
| `global_exception_handler` | `(request: Request, exc: Exception)` | - |
| `open_inbox` | `()` | - |

**关键依赖：**
- `from fastapi import FastAPI, Request`
- `from fastapi.middleware.cors import CORSMiddleware`
- `from fastapi.responses import JSONResponse`
- `from fastapi.staticfiles import StaticFiles`
- `from database import init_db`
- `from endpoints.upload import router as upload_router`
- `from endpoints.rag import router as rag_router`
- `from endpoints.review import router as review_router`
- `from endpoints.categories import router as categories_router`
- `from endpoints.automation import router as automation_router`

---
#### `backend/ai_client.py` (49 行)

**类 `AIClient`** — 行 10

| 函数 | 签名 | 说明 |
|------|------|------|
|   ⮑ `chat` | `(self, messages, temperature=0.7, max_tokens=2048)` | - |
|   ⮑ `embed` | `(self, texts: list[str]) -> list[list[float]]` | - |

**关键依赖：**
- `import httpx`

---
#### `backend/database.py` (139 行)

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
#### `backend/evolution_files.py` (169 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_skills` | `() -> list[dict]` | Return [{skill_name, file_path, frontmatter, body}] for every installed skill. |
| `read_skill_file` | `(skill_name: str) -> Optional[dict]` | Read one SKILL.md, returning {skill_name, file_path, frontmatter, body} or None. |
| `write_patch_file` | `(patch_id: int, skill_name: str, patch_type: str, content: str) -> str` | Write a skill-patch file to .claude/skill-patches/. Returns the file path. |
| `apply_patch_to_skill` | `(skill_name: str, patch_type: str, target_section: str, patch_content: str) -> bool` | Actually modify the SKILL.md file on disk. Returns True on success. |
| `compute_skill_fingerprint` | `(skill_name: str) -> str` | MD5 hash of the SKILL.md file content. |
| `read_config_files` | `() -> dict` | Read settings.json and .mcp.json, return as dict. |

---
#### `backend/evolution_pipeline.py` (289 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `classify_risk` | `(text: str) -> str` | - |
| `should_auto_apply` | `(risk_level: str) -> bool` | - |

**关键依赖：**
- `from database import get_db`
- `from ai_client import ai_client`

---
#### `backend/tests/test_main.py` (82 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `test_health` | `()` | - |
| `test_list_modules` | `()` | - |
| `test_list_documents` | `()` | - |
| `test_list_categories` | `()` | - |
| `test_automation_invalid_module` | `()` | - |
| `test_automation_empty_input` | `()` | - |
| `test_rag_empty_query` | `()` | - |

**关键依赖：**
- `from httpx import AsyncClient, ASGITransport`

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
#### `backend/processing/vector_store.py` (163 行)

**类 `VectorStore`** — 行 12

| 函数 | 签名 | 说明 |
|------|------|------|
|   ⮑ `__init__` | `(self)` | - |
|   ⮑ `embed_fn` | `(self)` | - |
|   ⮑ `add_document` | `(self, doc_id: int, title: str, chunks: list[str], category: str = "", tags: str = "")` | - |
|   ⮑ `query` | `(self, question: str, top_k: int = 5, category: str = "") -> list[dict]` | - |
|   ⮑ `count` | `(self) -> int` | - |
|   ⮑ `index_wiki_page` | `(self, page_id: int, title: str, content: str, category: str = "", tags: str = "")` | 将 Wiki 页面全文嵌入后存入向量库 |
|   ⮑ `remove_wiki_page` | `(self, page_id: int)` | 从向量库中删除指定 Wiki 页面 |
|   ⮑ `search_wiki` | `(self, query: str, top_k: int = 10) -> list[dict]` | 语义搜索 Wiki 页面 |
| `get_vector_store` | `() -> VectorStore` | - |

**关键依赖：**
- `import chromadb`
- `from chromadb.config import Settings`
- `from sentence_transformers import SentenceTransformer`
- `from sentence_transformers import SentenceTransformer`
- `from ai_client import ai_client`

---
## 后端端点层 (endpoints/)

#### `backend/endpoints/ai_search.py` (157 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/ai-search` | `ai_search()` | payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `ai_search` | `(payload: dict)` | - |

**关键依赖：**
- `from fastapi import APIRouter`
- `from ai_client import ai_client`
- `import httpx`

---
#### `backend/endpoints/automation.py` (721 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/automation/modules` | `list_modules()` |  |
| POST | `/automation/run` | `run_automation()` | payload |
| POST | `/automation/queue` | `queue_tasks()` | payload |
| GET | `/automation/queue/status` | `queue_status()` |  |
| GET | `/automation/queue/{task_id}` | `task_status()` | task_id |
| DELETE | `/automation/queue/clear` | `clear_completed()` |  |
| POST | `/automation/reparse/{doc_id}` | `reparse_document()` | doc_id |
| GET | `/automation/reparseable` | `list_reparseable()` |  |
| POST | `/documents/cleanup` | `cleanup_documents()` | payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_modules` | `()` | - |
| `run_automation` | `(payload: dict)` | 同步执行（保持向后兼容）—— 单任务阻塞等待。 |
| `queue_tasks` | `(payload: dict)` | 批量提交任务，立即返回任务 ID 列表。支持多个链接（\\n 分隔或数组）。 |
| `queue_status` | `()` | 获取所有任务状态（最近 50 个）。 |
| `task_status` | `(task_id: str)` | 查询单个任务状态。 |
| `clear_completed` | `()` | 清除已完成和失败的任务。 |
| `reparse_document` | `(doc_id: int)` | 重新解析失败的抖音摘要文档。 提取原始抖音链接 → 删除旧文档 → 重新提交自动化任务。 |
| `list_reparseable` | `()` | 列出可以重新解析的文档（ASR 失败或内容不完整）。 |
| `cleanup_documents` | `(payload: dict = None)` | 批量清理测试文档、重复文档、无意义短文档。 支持模式： - test: 标题含 test/测试 的文档 - short: 少于 50 字的文档 - duplic |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`

---
#### `backend/endpoints/brainstorm.py` (279 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/brainstorm/step2` | `brainstorm_step2()` | payload |
| POST | `/brainstorm/step3` | `brainstorm_step3()` | payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `parse_step2_response` | `(text)` | Parse the AI's step-2 response into (question, options, dig_recommended). |
|   ⮑ `clean_opt` | `(s)` | - |
| `brainstorm_step2` | `(payload: dict)` | Iterative question phase. Returns next question + options. |
| `brainstorm_step3` | `(payload: dict)` | Final output generation phase. |

**关键依赖：**
- `from fastapi import APIRouter`
- `from ai_client import ai_client`

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
#### `backend/endpoints/evolution.py` (212 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/evolution/analyze` | `trigger_analysis()` | payload |
| GET | `/evolution/patches` | `list_patches()` | status, risk_level, limit |
| GET | `/evolution/patches/{patch_id}` | `get_patch()` | patch_id |
| POST | `/evolution/patches/{patch_id}/apply` | `apply_patch()` | patch_id |
| POST | `/evolution/patches/{patch_id}/reject` | `reject_patch()` | patch_id, payload |
| GET | `/evolution/snapshots` | `list_snapshots()` | limit |
| GET | `/evolution/snapshots/{snapshot_id}` | `get_snapshot()` | snapshot_id |
| POST | `/evolution/snapshots` | `create_manual_snapshot()` |  |
| GET | `/evolution/skills` | `get_skills()` |  |
| GET | `/evolution/skills/{skill_name}` | `get_skill()` | skill_name |
| GET | `/evolution/config` | `get_config()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `trigger_analysis` | `(payload: dict)` | Trigger evolution analysis manually or from wiki/review hooks. Request: {source_ |
| `list_patches` | `(status: str = None, risk_level: str = None, limit: int = 50)` | List skill patches. Optional filters: status, risk_level. |
| `get_patch` | `(patch_id: int)` | Get a single patch with full content. |
| `apply_patch` | `(patch_id: int)` | Manually apply a pending patch. |
| `reject_patch` | `(patch_id: int, payload: dict = None)` | Reject a pending patch. |
| `list_snapshots` | `(limit: int = 30)` | List recent system snapshots. |
| `get_snapshot` | `(snapshot_id: int)` | Get a full snapshot. |
| `create_manual_snapshot` | `()` | Create a manual snapshot of the current system state. |
| `get_skills` | `()` | List all installed skills. |
| `get_skill` | `(skill_name: str)` | Get a single skill's full content. |
| `get_config` | `()` | Get current configuration snapshot. |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`

---
#### `backend/endpoints/export.py` (123 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/export/all` | `export_all()` |  |
| GET | `/export/document/{doc_id}` | `export_document()` | doc_id |

| 函数 | 签名 | 说明 |
|------|------|------|
| `export_all` | `()` | 导出所有文档为 ZIP 文件，按分类组织文件夹。 |
| `export_document` | `(doc_id: int)` | 导出单个文档为 Markdown 文件。 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from fastapi.responses import StreamingResponse, Response`
- `from database import get_db`

---
#### `backend/endpoints/links.py` (92 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/documents/{doc_id}/links` | `get_document_links()` | doc_id |
| GET | `/documents/{doc_id}/backlinks` | `get_document_backlinks()` | doc_id |

| 函数 | 签名 | 说明 |
|------|------|------|
| `parse_wiki_links` | `(content: str) -> list[dict]` | 从文本中提取所有 [[...]] 链接，返回 [{target_title, link_text}]. |
| `sync_document_links` | `(doc_id: int, content: str)` | 解析文档内容中的 [[...]] 并同步到 document_links 表。 |
| `get_document_links` | `(doc_id: int)` | 获取文档的出链（它指向了哪些文档）。 |
| `get_document_backlinks` | `(doc_id: int)` | 获取文档的反链（哪些文档指向了它）。 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`

---
#### `backend/endpoints/rag.py` (106 行)

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
#### `backend/endpoints/review.py` (205 行)

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
#### `backend/endpoints/upload.py` (224 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/upload` | `upload_file()` | file |
| POST | `/upload/text` | `upload_text()` | payload |
| GET | `/documents` | `()` |  |
| GET | `/documents/{doc_id}` | `get_document()` | doc_id |
| DELETE | `/documents/{doc_id}` | `delete_document()` | doc_id |
| POST | `/documents/batch-delete` | `batch_delete_documents()` | payload |

| 函数 | 签名 | 说明 |
|------|------|------|
| `upload_text` | `(payload: dict)` | - |
| `get_document` | `(doc_id: int)` | - |
| `delete_document` | `(doc_id: int)` | - |
| `batch_delete_documents` | `(payload: dict)` | - |

**关键依赖：**
- `from fastapi import APIRouter, UploadFile, File, Form`
- `from database import get_db`
- `from processing.processors import can_handle, process_bytes, sha256, is_duplicate`
- `from endpoints.links import sync_document_links, parse_wiki_links`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`

---
#### `backend/endpoints/wiki.py` (957 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/wiki/compile` | `compile_wiki()` | payload |
| GET | `/wiki/pages` | `list_wiki_pages()` | category, search |
| GET | `/wiki/pages/{page_id}` | `get_wiki_page()` | page_id |
| GET | `/wiki/graph` | `get_wiki_graph()` |  |
| GET | `/wiki/categories` | `get_wiki_categories()` |  |
| DELETE | `/wiki/pages/{page_id}` | `delete_wiki_page()` | page_id |
| PUT | `/wiki/pages/{page_id}` | `update_wiki_page()` | page_id, payload |
| DELETE | `/wiki/pages` | `delete_all_wiki_pages()` |  |
| POST | `/wiki/regenerate` | `regenerate_wiki()` |  |
| POST | `/wiki/search` | `search_wiki()` | payload |
| POST | `/wiki/reindex` | `reindex_wiki()` |  |
| POST | `/wiki/learning-paths` | `generate_learning_paths()` |  |
| POST | `/wiki/category-overviews` | `generate_category_overviews()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `slugify` | `(title: str) -> str` | - |
| `compile_wiki` | `(payload: dict)` | 编译所有或指定文档为 Wiki 页面。支持增量模式：跳过内容未变更的文档。 |
| `list_wiki_pages` | `(category: str = None, search: str = None)` | - |
| `get_wiki_page` | `(page_id)` | - |
| `get_wiki_graph` | `()` | 返回知识图谱数据：nodes + edges |
| `get_wiki_categories` | `()` | - |
| `delete_wiki_page` | `(page_id: int)` | - |
| `update_wiki_page` | `(page_id: int, payload: dict)` | 手动编辑 Wiki 页面 |
| `delete_all_wiki_pages` | `()` | - |
| `regenerate_wiki` | `()` | 清空 Wiki 并重新编译所有文档 |
| `search_wiki` | `(payload: dict)` | 语义搜索 Wiki 页面 |
| `reindex_wiki` | `()` | 重建所有 Wiki 页面的向量索引 |
| `generate_learning_paths` | `()` | 分析所有 Wiki 页面，自动生成学习路径 |
| `generate_category_overviews` | `()` | 为每个分类生成综述 hub 页面 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`
- `from ai_client import ai_client`
- `from processing.vector_store import get_vector_store`

---
## MCP Server

#### `mcp_server.py` (818 行)

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
| `handle_parse_bilibili` | `(args: dict) -> list[TextContent]` | - |
| `handle_bilibili_download` | `(args: dict) -> list[TextContent]` | - |
| `handle_extract_bilibili_text` | `(args: dict) -> list[TextContent]` | - |
| `handle_parse_xhs` | `(args: dict) -> list[TextContent]` | - |
| `handle_extract_xhs_text` | `(args: dict) -> list[TextContent]` | - |
| `handle_xhs_media` | `(args: dict) -> list[TextContent]` | - |
| `handle_extract_xhs_video_text` | `(args: dict) -> list[TextContent]` | - |
| `handle_recognize_audio_file` | `(args: dict) -> list[TextContent]` | - |
| `handle_recognize_audio_url` | `(args: dict) -> list[TextContent]` | - |
| `handle_compile_wiki` | `(args: dict) -> list[TextContent]` | - |
| `handle_search_wiki` | `(args: dict) -> list[TextContent]` | - |
| `handle_get_wiki_page` | `(args: dict) -> list[TextContent]` | - |
| `handle_list_wiki_pages` | `(args: dict) -> list[TextContent]` | - |
| `handle_wiki_graph` | `(args: dict) -> list[TextContent]` | - |
| `handle_analyze_evolution` | `(args: dict) -> list[TextContent]` | - |
| `handle_list_evolution_patches` | `(args: dict) -> list[TextContent]` | - |
| `handle_apply_evolution_patch` | `(args: dict) -> list[TextContent]` | - |
| `handle_list_system_snapshots` | `(args: dict) -> list[TextContent]` | - |
| `handle_get_system_snapshot` | `(args: dict) -> list[TextContent]` | - |
| `main` | `()` | - |

**关键依赖：**
- `import httpx`

---
#### `social_parsers.py` (339 行)

**类 `QwenASR`** — 行 33

**类 `BilibiliParser`** — 行 86

**类 `XiaohongshuParser`** — 行 218

| 函数 | 签名 | 说明 |
|------|------|------|
|   ⮑ `__init__` | `(self, api_key: Optional[str] = None, model: str = DEFAULT_ASR_MODEL)` | - |
|   ⮑ `recognize` | `(self, audio_input, context=None, language=None, enable_lid=True, enable_itn=False) -> dict` | - |
|   ⮑ `extract_bvid` | `(share_text: str) -> str` | - |
|   ⮑ `get_video_info` | `(share_text: str) -> dict` | - |
|   ⮑ `get_play_url` | `(bvid: str, cid: int, quality: int = 80) -> dict` | - |
|   ⮑ `get_audio_url` | `(share_text: str, cid: Optional[int] = None) -> tuple` | 返回 (audio_url, video_info_dict) |
|   ⮑ `extract_note_id` | `(share_text: str) -> str` | - |
|   ⮑ `get_note_info` | `(share_text: str) -> dict` | - |
|   ⮑ `get_video_url` | `(share_text: str) -> tuple` | 返回 (video_url, note_info_dict) |

---
## 前端页面

#### `extension/popup.html` (29 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `apiBase`, `saveBtn`, `captureBtn`, `status`

---
#### `frontend/brainstorm.html` (411 行)

- 2 个 `<script>` 块, 1 个 `<style>` 块
- **调用的 API：**
  - `/brainstorm/step2`
  - `/brainstorm/step3`
- **关键 DOM ID：** `app`, `ideaInput`, `customInput`, `convEnd`
- **JS 函数：**
  - `API_BASE(()` → 行 148
  - `toast(msg, isError)` → 行 167
  - `callStep2()` → 行 176
  - `callStep3()` → 行 206
  - `selectMode(mode)` → 行 227
  - `startBrainstorm()` → 行 232
  - `chooseOption(opt)` → 行 243
  - `chooseCustom()` → 行 249
  - `goToStep3()` → 行 258
  - `reset()` → 行 263
  - `goBackToStep2()` → 行 268
  - `render()` → 行 279
  - `esc(s)` → 行 392
  - `escAttr(s)` → 行 393
  - `renderMd(str)` → 行 395
  - `copyOutput()` → 行 402

---
#### `frontend/index.html` (1446 行)

- 3 个 `<script>` 块, 1 个 `<style>` 块
- **调用的 API：**
  - `/ai-search`
  - `/automation/run`
  - `/categories`
  - `/documents`
  - `/documents/${docId}`
  - `/documents/${id}`
  - `/evolution/analyze`
  - `/evolution/patches/${patchId}/apply`
  - `/evolution/patches/${patchId}/reject`
  - `/evolution/patches?status=pending&limit=5`
  - `/evolution/snapshots`
  - `/evolution/snapshots/${snapshotId}`
  - `/evolution/snapshots?limit=10`
  - `/inbox/open`
  - `/rag/query`
  - `/review/list`
  - `/review/polish`
  - `/review/weekly`
  - `/upload`
  - `/upload/text`
- **关键 DOM ID：** `themeToggle`, `searchMode`, `searchInput`, `searchCategory`, `searchResult`, `shortcutsGrid`, `aiGrid`, `fileInput`, `kbSearchBtn`, `pasteClaudeBtn`, `kbDocList`, `reviewInput`, `reviewPolishBtn`, `reviewWeeklyBtn`, `reviewStatus`, `reviewResult`, `reviewPolished`, `reviewSuggestions`, `reviewRelated`, `reviewHistory`
- **JS 函数：**
  - `API_BASE(()` → 行 530
  - `qs(sel)` → 行 558
  - `qsa(sel)` → 行 559
  - `toast(msg, isError)` → 行 561
  - `getData(key, def)` → 行 569
  - `setData(key, val)` → 行 573
  - `renderShortcuts()` → 行 581
  - `deleteShortcut(e, idx)` → 行 599
  - `openShortcutModal(idx)` → 行 605
  - `renderAIs()` → 行 643
  - `launchAI(idx)` → 行 660
  - `openAIModal()` → 行 675
  - `doAISearch(question)` → 行 717
  - `doKBQuery(question)` → 行 753
  - `handleCommand(cmd)` → 行 785
  - `loadDocuments()` → 行 831
  - `deleteDocument(id)` → 行 860
  - `openInbox()` → 行 876
  - `sendToClaude(docId, title)` → 行 901
  - `viewDocument(id)` → 行 947

---
#### `frontend/kb.html` (849 行)

- 3 个 `<script>` 块, 1 个 `<style>` 块
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
- **关键 DOM ID：** `themeToggle`, `editToggleBtn`, `categoryList`, `currentTitle`, `docCount`, `searchBox`, `fileInput`, `pasteBtn`, `batchDeleteBtn`, `batchBar`, `batchCount`, `batchMoveSelect`, `batchMoveBtn`, `selectAll`, `docTableBody`, `emptyState`, `catModal`, `catModalTitle`, `catName`, `catIcon`
- **JS 函数：**
  - `API_BASE(()` → 行 278
  - `toast(msg, isError)` → 行 286
  - `escapeHtml(str)` → 行 293
  - `renderMd(str)` → 行 299
  - `pickColor(c)` → 行 319
  - `toggleEditMode()` → 行 336
  - `loadCategories()` → 行 352
  - `loadDocuments()` → 行 360
  - `renderCategories()` → 行 371
  - `selectCategory(catId)` → 行 417
  - `renderDocs()` → 行 429
  - `toggleDoc(id)` → 行 482
  - `toggleSelectAll()` → 行 490
  - `updateSelectAllCheckbox()` → 行 505
  - `clearSelection()` → 行 512
  - `updateBatchBar()` → 行 518
  - `moveDocPrompt(docId)` → 行 550
  - `batchDelete()` → 行 572
  - `deleteDoc(docId)` → 行 587
  - `openCatModal(catId)` → 行 601

---
#### `frontend/learning-checklist.html` (371 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `search`, `stats`, `list`, `empty`
- **JS 函数：**
  - `init()` → 行 239
  - `save()` → 行 256
  - `render()` → 行 260
  - `toggle(ti, ii)` → 行 309
  - `toggleSection(ti)` → 行 314
  - `expandAll()` → 行 319
  - `collapseAll()` → 行 320
  - `resetData()` → 行 322
  - `exportData()` → 行 329
  - `importData()` → 行 337
  - `doSearch()` → 行 355

---
#### `frontend/learning-plan.html` (80 行)

- 2 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `content`

---
#### `frontend/learning.html` (91 行)

- 0 个 `<script>` 块, 1 个 `<style>` 块

---
#### `frontend/suit/index.html` (21 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `root`

---
#### `frontend/wiki.html` (1050 行)

- 3 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `themeToggle`, `compileBtn`, `regenBtn`, `pathBtn`, `overviewBtn`, `wikiStats`, `statPages`, `statLinks`, `statCats`, `searchBox`, `catFilter`, `pageList`, `viewTitle`, `editPageBtn`, `delPageBtn`, `pageView`, `pageEmpty`, `pageContent`, `pageMeta`, `wikiContent`
- **JS 函数：**
  - `API(()` → 行 267
  - `get(path)` → 行 269
  - `post(path, body)` → 行 273
  - `put(path, body)` → 行 279
  - `del(path)` → 行 285
  - `init()` → 行 296
  - `loadPages()` → 行 319
  - `loadCategories()` → 行 324
  - `loadGraph()` → 行 329
  - `renderCatFilter()` → 行 336
  - `setupSearch()` → 行 350
  - `doSearch(query)` → 行 367
  - `filterByCat(cat)` → 行 378
  - `renderPageList()` → 行 386
  - `updateStats()` → 行 457
  - `openPage(id)` → 行 464
  - `openPageBySlug(slug)` → 行 521
  - `deletePage()` → 行 527
  - `openEditModal()` → 行 546
  - `closeEditModal()` → 行 558

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

### `docker-compose.yml` (21 行, hash: `c5427baf`)

```
services:
  study-hub:
    build:
      context: .
      args:
        # 轻量中文模型 (~95MB)；换成 BAAI/bge-large-zh-v1.5 效果更好但首次拉取 ~1.3GB
        EMBED_MODEL: BAAI/bge-small-zh-v1.5
    container_name: study-hub
    ports:
      - "${PORT:-8741}:8741"
    volumes:
      - study-hub-data:/app/data
      - model-cache:/root/.cache/huggingface
    env_file:
      - .env
    restart: unless-stopped

volumes:
  study-hub-data:
  model-cache:

```

### `Dockerfile` (39 行, hash: `8ea83b65`)

```
FROM python:3.12-slim

WORKDIR /app

# 系统依赖：PyMuPDF + sentence-transformers 编译
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# HF 镜像（国内网络加速）
ENV HF_ENDPOINT=https://hf-mirror.com

# 先用 CPU 版 PyTorch，避免拉 CUDA 版本导致镜像膨胀
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

# 预下载中文 embedding 模型（首次启动零等待）
# 轻量 bge-small-zh-v1.5 (~95MB)；追求效果可改为 bge-base-zh 或 bge-large-zh
ARG EMBED_MODEL=BAAI/bge-small-zh-v1.5
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBED_MODEL}')"

COPY backend/ .
COPY frontend/ /frontend
COPY mcp_server.py .

# Cleanup to reduce image size
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    pip cache purge 2>/dev/null || true && \
    rm -rf /root/.cache/pip

EXPOSE 8741

CMD ["python", "main.py"]

```

### `requirements-mcp.txt` (5 行, hash: `e5b54302`)

```
mcp>=1.0.0
httpx>=0.25.0
requests>=2.28.0
dashscope

```

## 工具百宝箱 (mods/)

### brainstorm

| 文件 | 行数 |
|------|------|
| `.gitignore` | 22 |
| `ai-fanwen.py` | 1594 |
| `docs/PROJECT.md` | 502 |
| `docs/superpowers/specs/2026-05-07-ai-fanwen-redesign-design.md` | 95 |
| `error.log` | 1 |
| `neko_sprites/1.gif` | 1 |
| `neko_sprites/10.gif` | 1 |
| `neko_sprites/11.gif` | 3 |
| `neko_sprites/12.gif` | 1 |
| `neko_sprites/13.gif` | 3 |
| `neko_sprites/14.gif` | 3 |
| `neko_sprites/15.gif` | 2 |
| `neko_sprites/16.gif` | 2 |
| `neko_sprites/17.gif` | 3 |
| `neko_sprites/18.gif` | 3 |
| `neko_sprites/19.gif` | 1 |
| `neko_sprites/2.gif` | 1 |
| `neko_sprites/20.gif` | 5 |
| `neko_sprites/21.gif` | 2 |
| `neko_sprites/22.gif` | 2 |
| `neko_sprites/23.gif` | 1 |
| `neko_sprites/24.gif` | 1 |
| `neko_sprites/25.gif` | 3 |
| `neko_sprites/26.gif` | 2 |
| `neko_sprites/27.gif` | 1 |
| `neko_sprites/28.gif` | 2 |
| `neko_sprites/29.gif` | 2 |
| `neko_sprites/3.gif` | 1 |
| `neko_sprites/30.gif` | 1 |
| `neko_sprites/31.gif` | 1 |
| `neko_sprites/32.gif` | 3 |
| `neko_sprites/4.gif` | 4 |
| `neko_sprites/5.gif` | 2 |
| `neko_sprites/6.gif` | 2 |
| `neko_sprites/7.gif` | 2 |
| `neko_sprites/8.gif` | 1 |
| `neko_sprites/9.gif` | 2 |
| `README.md` | 105 |
| `start.bat` | 40 |
| `test_app.py` | 305 |
| `test_gui.py` | 296 |
| `护眼仪小助手.spec` | 39 |

### learning

| 文件 | 行数 |
|------|------|
| `vibe-coding-learning-plan.md` | 397 |
| `学习清单生成器.html` | 351 |
| `超级学习管家-全栈VibeCoding路线.md` | 730 |

### suit

| 文件 | 行数 |
|------|------|
| `.gitignore` | 25 |
| `build-err.txt` | 1 |
| `build-out.txt` | 1 |
| `eslint.config.js` | 23 |
| `index.html` | 19 |
| `package-lock.json` | 6842 |
| `package.json` | 45 |
| `postcss.config.js` | 7 |
| `public/favicon.svg` | 1 |
| `public/icon-192.png` | 22 |
| `public/icon-192.svg` | 7 |
| `public/icon-512.png` | 95 |
| `public/icons.svg` | 25 |
| `public/manifest.json` | 23 |
| `public/sw.js` | 37 |
| `README.md` | 74 |
| `REQUIREMENTS.md` | 230 |
| `src/App.css` | 185 |
| `src/App.tsx` | 43 |
| `src/assets/hero.png` | 98 |
| `src/assets/react.svg` | 1 |
| `src/assets/vite.svg` | 2 |
| `src/components/Layout.tsx` | 89 |
| `src/db/index.ts` | 18 |
| `src/db/seed.ts` | 70 |
| `src/index.css` | 56 |
| `src/main.tsx` | 20 |
| `src/pages/Dashboard/DashboardPage.tsx` | 191 |
| `src/pages/Diet/DietPage.tsx` | 11 |
| `src/pages/Diet/DietSchedule.tsx` | 102 |
| `src/pages/Settings/SettingsPage.tsx` | 306 |
| `src/pages/Today/TodayPage.tsx` | 220 |
| `src/pages/Workout/WorkoutPage.tsx` | 11 |
| `src/pages/Workout/WorkoutSchedule.tsx` | 95 |
| `src/types/index.ts` | 97 |
| `src/utils/suggestions.test.ts` | 204 |
| `src/utils/suggestions.ts` | 449 |
| `tailwind.config.js` | 30 |
| `test-build.mjs` | 8 |
| `tsconfig.app.json` | 31 |
| `tsconfig.json` | 8 |
| `tsconfig.node.json` | 25 |
| `vite-build.txt` | 1 |
| `vite-err.txt` | 1 |
| `vite-log.txt` | 5 |
| `vite-log2.txt` | 1 |
| `vite-out.txt` | 1 |
| `vite-out2.txt` | 1 |
| `vite-out3.txt` | 17 |
| `vite-out4.txt` | 1 |
| ... | 还有 5 个文件 |

## 文件完整性指纹

| 文件 | MD5 (前8位) | 行数 |
|------|-------------|------|
| `backend/ai_client.py` | `4162e68b` | 49 |
| `backend/database.py` | `25e1e94c` | 139 |
| `backend/endpoints/__init__.py` | `d41d8cd9` | 1 |
| `backend/endpoints/ai_search.py` | `b903d460` | 157 |
| `backend/endpoints/automation.py` | `aafdcdf8` | 721 |
| `backend/endpoints/brainstorm.py` | `b5bb66fc` | 279 |
| `backend/endpoints/categories.py` | `dd0573bd` | 197 |
| `backend/endpoints/evolution.py` | `922a09da` | 212 |
| `backend/endpoints/export.py` | `3b9000b4` | 123 |
| `backend/endpoints/links.py` | `72532e04` | 92 |
| `backend/endpoints/rag.py` | `8c1a86d4` | 106 |
| `backend/endpoints/review.py` | `66f4eda8` | 205 |
| `backend/endpoints/upload.py` | `23ff8a59` | 224 |
| `backend/endpoints/wiki.py` | `235fe681` | 957 |
| `backend/evolution_files.py` | `f28b1274` | 169 |
| `backend/evolution_pipeline.py` | `8fcc61e2` | 289 |
| `backend/main.py` | `b0b87980` | 94 |
| `backend/processing/__init__.py` | `d41d8cd9` | 1 |
| `backend/processing/chunker.py` | `3cebfd14` | 37 |
| `backend/processing/processors.py` | `733919b8` | 71 |
| `backend/processing/vector_store.py` | `5c089bbc` | 163 |
| `backend/tests/__init__.py` | `d41d8cd9` | 1 |
| `backend/tests/test_main.py` | `9d0d1b32` | 82 |
| `backend/watcher.py` | `8cf30998` | 118 |
| `extension/adapters.js` | `ae148a47` | 68 |
| `extension/background.js` | `28d6c291` | 42 |
| `extension/content.js` | `00de1e82` | 129 |
| `extension/popup.html` | `df2f95d0` | 29 |
| `extension/popup.js` | `f1d1d90a` | 82 |
| `frontend/brainstorm.html` | `c5f93810` | 411 |
| `frontend/index.html` | `978c37c6` | 1446 |
| `frontend/kb.html` | `ddf2ab85` | 849 |
| `frontend/learning-checklist.html` | `57f519f4` | 371 |
| `frontend/learning-plan.html` | `cdd7e6ce` | 80 |
| `frontend/learning.html` | `0993c1b9` | 91 |
| `frontend/suit/index.html` | `5727fd6e` | 21 |
| `frontend/wiki.html` | `1fdcfb61` | 1050 |
| `mcp_server.py` | `b820af22` | 818 |
| `social_parsers.py` | `5da1fae7` | 339 |

<!-- 文件总数: 39, 生成时间: 2026-05-09 18:30 UTC -->
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
