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

### Windows（推荐）

项目根目录只保留一套推荐入口：双击 **`后台启动.bat`** 启动，双击
**`后台停止.bat`** 停止；也可以在 PowerShell 中执行：

```powershell
后台启动.bat
后台停止.bat
```

脚本会自动：
- 通过系统 `py -3` 定位并验证 Python 的绝对路径，不使用项目 venv
- 拒绝占用 8741 的非本项目进程，清理无效或陈旧 PID
- 等待健康检查成功后写入有效数字 PID
- 停止时只终止当前目录启动的 Study Hub，并清理 PID 文件

### macOS / Linux

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r backend/requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env，填入 API Key

# 4. 启动
cd backend && python main.py
```

### 访问

- 主页面：**http://localhost:8741**
- 管理控制台：**http://localhost:8741/admin.html** ← 看状态、日志、数据量
- API 文档：**http://localhost:8741/docs**

> 首次启动会自动下载中文 embedding 模型（~95MB），日志会显示进度。

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

## 遇到问题？

👉 先看 **[排障手册 TROUBLESHOOTING.md](TROUBLESHOOTING.md)** —— 按症状查原因，不懂代码也能修。

常见场景：服务启动失败、上传没反应、搜索不准、扩展不采集、数据备份恢复。

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
│   ├── start-background.ps1   # Windows 后台启动实现
│   ├── stop-background.ps1    # Windows 后台停止实现
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
├── 后台启动.bat               # Windows 唯一推荐启动入口
├── 后台停止.bat               # Windows 唯一推荐停止入口
└── README.md
```

<!-- AUTO-GENERATED-START -->

<!-- 自动生成于 2026-06-07 01:10 UTC，请勿手动编辑此区块 -->

## API 路由全览

### 端点 (endpoints/)

| 方法 | 路径 | 处理函数 | 关键参数 | 文件 |
|------|------|----------|----------|------|
| GET | `/stats` | `admin_stats()` |  | `13` |
| GET | `/logs` | `admin_logs()` | lines | `58` |
| GET | `/documents/recent` | `recent_documents()` | limit | `77` |
| GET | `/system/info` | `system_info()` |  | `95` |
| GET | `/monitored-urls` | `list_monitored_urls()` |  | `118` |
| POST | `/monitored-urls` | `add_monitored_url()` | payload | `128` |
| DELETE | `/monitored-urls/{url_id}` | `delete_monitored_url()` | url_id | `152` |
| POST | `/monitored-urls/check` | `check_monitored_urls()` |  | `162` |
| GET | `/monitored-urls/changes` | `get_url_changes()` |  | `209` |
| POST | `/ai-search` | `ai_search()` | payload | `126` |
| GET | `/automation/modules` | `list_modules()` |  | `1276` |
| POST | `/automation/run` | `run_automation()` | payload | `1281` |
| POST | `/automation/queue` | `queue_tasks()` | payload | `1320` |
| GET | `/automation/queue/status` | `queue_status()` |  | `1385` |
| GET | `/automation/queue/{task_id}` | `task_status()` | task_id | `1425` |
| POST | `/automation/queue/retry/{task_id}` | `retry_task()` | task_id | `1479` |
| DELETE | `/automation/queue/clear` | `clear_completed()` |  | `1518` |
| POST | `/automation/reparse/{doc_id}` | `reparse_document()` | doc_id | `1565` |
| GET | `/automation/reparseable` | `list_reparseable()` |  | `1634` |
| POST | `/documents/cleanup` | `cleanup_documents()` | payload | `1666` |
| POST | `/automation/extract-webpage` | `extract_webpage()` | payload | `1784` |
| POST | `/brainstorm/step2` | `brainstorm_step2()` | payload | `237` |
| POST | `/brainstorm/step3` | `brainstorm_step3()` | payload | `262` |
| GET | `/categories` | `list_categories()` |  | `8` |
| POST | `/categories` | `create_category()` | payload | `22` |
| PUT | `/categories/{cat_id}` | `update_category()` | cat_id, payload | `48` |
| DELETE | `/categories/{cat_id}` | `delete_category()` | cat_id | `71` |
| PUT | `/documents/{doc_id}/move` | `move_document()` | doc_id, payload | `86` |
| PUT | `/documents/batch-move` | `batch_move_documents()` | payload | `126` |
| PUT | `/documents/{doc_id}/tags` | `update_document_tags()` | doc_id, payload | `169` |
| POST | `/documents/{doc_id}/auto-tags` | `auto_tag_document()` | doc_id | `201` |
| GET | `/services` | `list_services()` |  | `84` |
| GET | `/services/{service_id}` | `get_service_status()` | service_id | `108` |
| GET | `/ddl/tasks` | `list_tasks()` | status, task_type, project_id, plan_date, plan_type | `8` |
| POST | `/ddl/tasks` | `create_task()` | payload | `53` |
| PUT | `/ddl/tasks/{task_id}` | `update_task()` | task_id, payload | `103` |
| DELETE | `/ddl/tasks/{task_id}` | `delete_task()` | task_id | `136` |
| PUT | `/ddl/tasks/reorder` | `reorder_tasks()` | payload | `151` |
| GET | `/ddl/stats` | `ddl_stats()` |  | `166` |
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
| POST | `/images/generate-cover` | `generate_cover()` | req | `25` |
| GET | `/journal/entries` | `list_entries()` | year, month, tag, mood | `56` |
| GET | `/journal/entries/{entry_id}` | `get_entry()` | entry_id | `81` |
| GET | `/journal/today` | `get_today()` |  | `91` |
| POST | `/journal/entries` | `create_entry()` | payload | `102` |
| PUT | `/journal/entries/{entry_id}` | `update_entry()` | entry_id, payload | `133` |
| DELETE | `/journal/entries/{entry_id}` | `delete_entry()` | entry_id | `161` |
| GET | `/journal/stats` | `get_stats()` |  | `170` |
| GET | `/journal/tags` | `list_tags()` |  | `200` |
| GET | `/documents/{doc_id}/links` | `get_document_links()` | doc_id | `43` |
| GET | `/documents/{doc_id}/backlinks` | `get_document_backlinks()` | doc_id | `68` |
| POST | `/topics` | `create_topic()` | req | `94` |
| GET | `/topics` | `list_topics()` | limit, unused_only | `108` |
| POST | `/topics/ai-discover` | `ai_discover_topics()` | keyword, count | `136` |
| POST | `/accounts` | `add_account()` | req | `190` |
| GET | `/accounts` | `list_accounts()` | platform | `204` |
| POST | `/projects` | `create_project()` | req | `232` |
| GET | `/projects` | `list_projects()` | status, platform, limit | `255` |
| GET | `/projects/{project_id}` | `get_project()` | project_id | `289` |
| POST | `/projects/{project_id}/status` | `update_project_status()` | project_id, status | `315` |
| POST | `/projects/{project_id}/script/generate` | `generate_script()` | project_id, req | `332` |
| POST | `/projects/{project_id}/script/update` | `update_script()` | project_id, req | `382` |
| POST | `/projects/{project_id}/script/polish` | `polish_script()` | project_id, style | `395` |
| POST | `/projects/{project_id}/video/editing-plan` | `generate_editing_plan()` | project_id | `434` |
| POST | `/projects/{project_id}/video/upload` | `upload_video_path()` | project_id, video_path | `476` |
| POST | `/projects/{project_id}/cover/generate` | `generate_cover_for_project()` | project_id, req | `493` |
| GET | `/images/{filename}` | `serve_cover_image()` | filename | `609` |
| POST | `/projects/{project_id}/publish` | `publish_project()` | project_id, req | `623` |
| POST | `/projects/{project_id}/publish/confirm` | `confirm_published()` | project_id, platform, url | `720` |
| POST | `/projects/{project_id}/auto-edit` | `auto_edit_video()` | project_id, req | `768` |
| GET | `/video/{filename}` | `serve_video()` | filename | `907` |
| POST | `/projects/{project_id}/video/capcut-export` | `capcut_export_guide()` | project_id | `917` |
| POST | `/projects/{project_id}/auto-publish` | `auto_publish()` | project_id, req | `993` |
| GET | `/publish/config` | `get_publish_config()` |  | `1169` |
| POST | `/projects/{project_id}/tts/generate` | `generate_tts()` | project_id, req | `1212` |
| GET | `/audio/{filename}` | `serve_audio()` | filename | `1317` |
| GET | `/tts/voices` | `list_tts_voices()` |  | `1327` |
| GET | `/dashboard` | `operations_dashboard()` |  | `1342` |
| POST | `/rag/query` | `rag_query()` | payload | `65` |
| POST | `/review/polish` | `polish_review()` | payload | `24` |
| GET | `/review/list` | `list_reviews()` |  | `117` |
| GET | `/review/weekly` | `weekly_report()` |  | `127` |
| GET | `/api/files` | `list_files()` |  | `79` |
| GET | `/api/file` | `read_file()` | path, description="相对路径" | `92` |
| POST | `/api/file` | `write_file()` | path, description="相对路径" | `100` |
| GET | `/api/self` | `get_self_layer()` |  | `115` |
| POST | `/api/decide` | `decide()` | body | `124` |
| POST | `/api/chat` | `chat()` | body | `143` |
| POST | `/api/chat/stream` | `chat_stream()` | body | `185` |
| GET | `/api/memory/stats` | `memory_stats()` |  | `239` |
| GET | `/api/memory` | `search_memory_api()` | q, description="搜索关键词" | `248` |
| POST | `/api/lint` | `run_lint()` |  | `309` |
| POST | `/api/ingest` | `ingest_api()` | body | `335` |
| POST | `/api/ingest/enhanced` | `ingest_enhanced_api()` | body | `377` |
| POST | `/api/self/scan-changes` | `scan_self_changes_api()` |  | `396` |
| GET | `/api/pending-captures` | `get_pending_captures_api()` |  | `409` |
| POST | `/api/pending-captures/confirm` | `confirm_pending_api()` | body | `419` |
| POST | `/api/project/scan` | `scan_project_api()` |  | `437` |
| POST | `/api/social/ingest` | `social_ingest_api()` | body | `450` |
| POST | `/api/chat/distill` | `chat_distill_api()` | body | `470` |
| POST | `/api/batch-import` | `batch_import_api()` | body | `490` |
| POST | `/api/chat/batch-distill` | `()` |  | `594` |
| GET | `/community` | `()` |  | `98` |
| GET | `/community/categories` | `list_categories()` |  | `146` |
| POST | `/community/sync` | `sync_community()` |  | `152` |
| GET | `/community/stats` | `community_stats()` |  | `159` |
| GET | `/local` | `list_local_skills()` |  | `168` |
| POST | `/local/scan` | `scan_local()` |  | `176` |
| POST | `/local/{skill_id}/toggle` | `toggle_local_skill()` | skill_id, req | `183` |
| DELETE | `/local/{skill_id}` | `delete_local_skill()` | skill_id | `190` |
| POST | `/local/install` | `install_skill()` | req | `197` |
| GET | `/sop/blocks` | `list_blocks()` | search, tag | `14` |
| GET | `/sop/blocks/{block_id}` | `get_block()` | block_id | `32` |
| POST | `/sop/blocks` | `create_block()` | payload | `42` |
| PUT | `/sop/blocks/{block_id}` | `update_block()` | block_id, payload | `64` |
| DELETE | `/sop/blocks/{block_id}` | `delete_block()` | block_id | `91` |
| GET | `/sop/chains` | `list_chains()` |  | `104` |
| GET | `/sop/chains/{chain_id}` | `get_chain()` | chain_id | `118` |
| POST | `/sop/chains` | `create_chain()` | payload | `165` |
| PUT | `/sop/chains/{chain_id}` | `update_chain()` | chain_id, payload | `194` |
| DELETE | `/sop/chains/{chain_id}` | `delete_chain()` | chain_id | `218` |
| POST | `/sop/chains/{chain_id}/blocks` | `add_block_to_chain()` | chain_id, payload | `231` |
| PUT | `/sop/chains/{chain_id}/blocks/{cb_id}` | `update_chain_block()` | chain_id, cb_id, payload | `267` |
| DELETE | `/sop/chains/{chain_id}/blocks/{cb_id}` | `remove_block_from_chain()` | chain_id, cb_id | `292` |
| PUT | `/sop/chains/{chain_id}/reorder` | `reorder_chain_blocks()` | chain_id, payload | `303` |
| GET | `/sop/suggestions` | `list_suggestions()` | status, suggestion_type, limit | `322` |
| GET | `/sop/suggestions/{sug_id}` | `get_suggestion()` | sug_id | `340` |
| POST | `/sop/suggestions/{sug_id}/confirm` | `confirm_suggestion()` | sug_id | `350` |
| POST | `/sop/suggestions/{sug_id}/reject` | `reject_suggestion()` | sug_id, payload | `474` |
| POST | `/sop/evolution/analyze` | `trigger_analysis()` | payload | `499` |
| GET | `/sop/wiki-unmatched` | `list_unmatched_wiki()` |  | `513` |
| POST | `/upload` | `upload_file()` | file | `72` |
| POST | `/upload/text` | `upload_text()` | payload | `148` |
| GET | `/documents` | `()` |  | `221` |
| GET | `/documents/{doc_id}` | `get_document()` | doc_id | `296` |
| DELETE | `/documents/{doc_id}` | `delete_document()` | doc_id | `312` |
| POST | `/documents/batch-delete` | `batch_delete_documents()` | payload | `337` |
| POST | `/wiki/compile` | `compile_wiki()` | payload | `174` |
| GET | `/wiki/pages` | `list_wiki_pages()` | category, search | `297` |
| GET | `/wiki/pages/{page_id}` | `get_wiki_page()` | page_id | `326` |
| GET | `/wiki/graph` | `get_wiki_graph()` |  | `356` |
| GET | `/wiki/categories` | `get_wiki_categories()` |  | `394` |
| DELETE | `/wiki/pages/{page_id}` | `delete_wiki_page()` | page_id | `405` |
| POST | `/wiki/pages` | `create_wiki_page()` | request | `420` |
| PUT | `/wiki/pages/{page_id}` | `update_wiki_page()` | page_id, payload | `481` |
| DELETE | `/wiki/pages` | `delete_all_wiki_pages()` |  | `544` |
| POST | `/wiki/regenerate` | `regenerate_wiki()` |  | `554` |
| POST | `/wiki/search` | `search_wiki()` | payload | `572` |
| POST | `/wiki/reindex` | `reindex_wiki()` |  | `603` |
| POST | `/wiki/learning-paths` | `generate_learning_paths()` |  | `623` |
| POST | `/wiki/category-overviews` | `generate_category_overviews()` |  | `751` |
| POST | `/workflow/run` | `workflow_run()` | req | `48` |
| GET | `/workflow/status/{task_id}` | `workflow_status()` | task_id | `69` |
| POST | `/workflow/pause/{task_id}` | `workflow_pause()` | task_id | `78` |
| POST | `/workflow/resume/{task_id}` | `workflow_resume()` | task_id, req | `87` |
| GET | `/workflow/templates` | `workflow_templates()` |  | `97` |
| GET | `/workflow/templates/{filename}` | `workflow_template_get()` | filename | `138` |
| PUT | `/workflow/templates/{filename}` | `workflow_template_save()` | filename, req | `163` |
| DELETE | `/workflow/templates/{filename}` | `workflow_template_delete()` | filename | `184` |
| POST | `/workflow/templates/{filename}/copy` | `workflow_template_copy()` | filename | `195` |
| POST | `/workflow/create-from-text` | `workflow_create_from_text()` | req | `217` |
| GET | `/workflow/queue/status` | `workflow_queue_status()` | show_archived | `265` |
| POST | `/workflow/archive/{task_id}` | `workflow_archive()` | task_id | `284` |
| GET | `/workflow/tools` | `workflow_tools()` |  | `293` |
| GET | `/workflow/output/{task_id}/{filename}` | `workflow_download()` | task_id, filename | `300` |

## 数据库表结构

### `categories` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `name` | TEXT |
| `icon` | TEXT DEFAULT '📁' |
| `color` | TEXT ' |
| `sort_order` | INTEGER |
| `tag_rules` | TEXT DEFAULT '[]' |
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
| `cover_image` | TEXT DEFAULT '' |
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

### `ddl_tasks` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `title` | TEXT |
| `description` | TEXT DEFAULT '' |
| `due_date` | TEXT |
| `task_type` | TEXT ' CHECK(task_type IN ('milestone','todo','learning')) |
| `project_id` | INTEGER |
| `status` | TEXT ' CHECK(status IN ('todo','in_progress','done')) |
| `sort_order` | INTEGER |
| `created_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `task_queue` 表

| 列名 | 类型 |
|------|------|
| `task_id` | TEXT |
| `module_id` | TEXT |
| `module_name` | TEXT DEFAULT '' |
| `input_text` | TEXT |
| `input_hash` | TEXT DEFAULT '' |
| `status` | TEXT ' CHECK(status IN ('pending','extracting','summarizing','importing','done','error')) |
| `progress` | TEXT DEFAULT '' |
| `error` | TEXT DEFAULT '' |
| `result_doc_id` | INTEGER |
| `result_title` | TEXT DEFAULT '' |
| `steps_json` | TEXT DEFAULT '[]' |
| `current_step` | TEXT DEFAULT '' |
| `api_key_error` | INTEGER |
| `api_key_error_msg` | TEXT DEFAULT '' |
| `replace_doc_id` | INTEGER |
| `created_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `sop_blocks` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `title` | TEXT |
| `description` | TEXT DEFAULT '' |
| `content` | TEXT DEFAULT '' |
| `tags` | TEXT DEFAULT '[]' |
| `source_wiki_page_id` | INTEGER |
| `source_type` | TEXT ' CHECK(source_type IN ('manual','wiki')) |
| `created_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `sop_chains` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `name` | TEXT |
| `description` | TEXT DEFAULT '' |
| `created_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `sop_chain_blocks` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `chain_id` | INTEGER |
| `block_id` | INTEGER |
| `sort_order` | INTEGER |
| `parent_id` | INTEGER |
| `branch_label` | TEXT DEFAULT '' |

### `sop_suggestions` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `suggestion_type` | TEXT |
| `wiki_page_id` | INTEGER |
| `block_id` | INTEGER |
| `chain_id` | INTEGER |
| `suggested_title` | TEXT DEFAULT '' |
| `suggested_content` | TEXT DEFAULT '' |
| `rationale` | TEXT DEFAULT '' |
| `status` | TEXT ' CHECK(status IN ('pending','confirmed','rejected')) |
| `created_at` | TIMESTAMP |
| `resolved_at` | TIMESTAMP |

### `community_skills` 表

| 列名 | 类型 |
|------|------|
| `id` | TEXT |
| `display_name` | TEXT |
| `category` | TEXT DEFAULT '' |
| `sub_category` | TEXT DEFAULT '' |
| `primary_link` | TEXT |
| `secondary_link` | TEXT DEFAULT '' |
| `author_name` | TEXT DEFAULT '' |
| `author_link` | TEXT DEFAULT '' |
| `license` | TEXT DEFAULT '' |
| `description` | TEXT DEFAULT '' |
| `stars` | INTEGER |
| `active` | INTEGER |
| `date_added` | TEXT DEFAULT '' |
| `last_modified` | TEXT DEFAULT '' |
| `last_checked` | TEXT DEFAULT '' |
| `repo_created` | TEXT DEFAULT '' |
| `latest_release` | TEXT DEFAULT '' |
| `release_version` | TEXT DEFAULT '' |
| `release_source` | TEXT DEFAULT '' |
| `synced_at` | TIMESTAMP |

### `local_skills` 表

| 列名 | 类型 |
|------|------|
| `id` | TEXT |
| `name` | TEXT |
| `display_name` | TEXT DEFAULT '' |
| `source` | TEXT ' CHECK(source IN ('claude','agents','kimi')) |
| `install_path` | TEXT |
| `github_url` | TEXT DEFAULT '' |
| `enabled` | INTEGER |
| `config_json` | TEXT DEFAULT '{}' |
| `installed_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `journal_entries` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `date` | TEXT |
| `content` | TEXT  DEFAULT '' |
| `mood` | TEXT ' CHECK(mood IN ('happy','excited','calm','neutral','tired','sad','angry','loved')) |
| `tags` | TEXT DEFAULT '[]' |
| `weather` | TEXT DEFAULT '' |
| `location` | TEXT DEFAULT '' |
| `sticker` | TEXT DEFAULT '' |
| `created_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `content_projects` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `title` | TEXT |
| `topic_idea` | TEXT DEFAULT '' |
| `platform` | TEXT DEFAULT '' |
| `status` | TEXT ' CHECK(status IN ('idea','script','recording','editing','cover','ready','published','archived')) |
| `script_content` | TEXT DEFAULT '' |
| `script_audio_url` | TEXT DEFAULT '' |
| `video_path` | TEXT DEFAULT '' |
| `cover_image_url` | TEXT DEFAULT '' |
| `published_urls` | TEXT DEFAULT '{}' |
| `tags` | TEXT DEFAULT '[]' |
| `scheduled_at` | TIMESTAMP |
| `created_at` | TIMESTAMP |
| `updated_at` | TIMESTAMP |

### `topic_ideas` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `title` | TEXT |
| `source` | TEXT DEFAULT '' |
| `trend_score` | INTEGER |
| `used_in_project_id` | INTEGER |
| `tags` | TEXT DEFAULT '[]' |
| `created_at` | TIMESTAMP |

### `platform_accounts` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `platform` | TEXT |
| `account_name` | TEXT |
| `account_id` | TEXT DEFAULT '' |
| `avatar_url` | TEXT DEFAULT '' |
| `followers_count` | INTEGER |
| `is_active` | INTEGER |
| `config_json` | TEXT DEFAULT '{}' |
| `created_at` | TIMESTAMP |

### `monitored_urls` 表

| 列名 | 类型 |
|------|------|
| `id` | INTEGER |
| `url` | TEXT |
| `title` | TEXT DEFAULT '' |
| `last_content_hash` | TEXT DEFAULT '' |
| `last_content` | TEXT DEFAULT '' |
| `last_checked` | TIMESTAMP |
| `change_detected` | INTEGER |
| `change_count` | INTEGER |
| `notify_enabled` | INTEGER |
| `created_at` | TIMESTAMP |

## 环境变量 (.env)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HF_ENDPOINT` | `https://hf-mirror.com` |  |
| `PORT` | `8741` |  |

## 后端核心文件

#### `backend/main.py` (458 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/health` | `health()` |  |
| GET | `/learning/plans` | `list_learning_plans()` |  |
| GET | `/learning/checklist/{filename}` | `get_checklist()` | filename |
| GET | `/inbox/open` | `open_inbox()` |  |
| GET | `/{full_path:path}` | `serve_spa()` | full_path |

**类 `StripApiPrefixMiddleware`** (继承 `BaseHTTPMiddleware`) — 行 175

| 函数 | 签名 | 说明 |
|------|------|------|
| `lifespan` | `(app: FastAPI)` | - |
|   \u2b91 `dispatch` | `(self, request, call_next)` | - |
| `health` | `()` | - |
| `global_exception_handler` | `(request: Request, exc: Exception)` | - |
| `list_learning_plans` | `()` | - |
| `parse_checklist_md` | `(path: str) -> dict` | Parse a markdown file into checklist format. Supports: - # Title -> plan name -  |
|   \u2b91 `flush_topic` | `()` | - |
|   \u2b91 `extract_tag` | `(text: str) -> tuple` | - |
| `get_checklist` | `(filename: str)` | - |
| `open_inbox` | `()` | - |
|   \u2b91 `serve_spa` | `(full_path: str)` | - |

**关键依赖：**
- `from fastapi import FastAPI, Request`
- `from fastapi.middleware.cors import CORSMiddleware`
- `from fastapi.responses import JSONResponse`
- `from fastapi.staticfiles import StaticFiles`
- `from fastapi.responses import FileResponse, HTMLResponse`
- `from database import init_db`
- `from endpoints.upload import router as upload_router`
- `from endpoints.rag import router as rag_router`
- `from endpoints.review import router as review_router`
- `from endpoints.categories import router as categories_router`

---
#### `backend/ai_client.py` (49 行)

**类 `AIClient`** — 行 10

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `chat` | `(self, messages, temperature=0.7, max_tokens=2048)` | - |
|   \u2b91 `embed` | `(self, texts: list[str]) -> list[list[float]]` | - |

**关键依赖：**
- `import httpx`

---
#### `backend/database.py` (421 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_db` | `()` | - |
| `init_db` | `()` | - |

---
#### `backend/watcher.py` (118 行)

**类 `InboxHandler`** (继承 `FileSystemEventHandler`) — 行 16

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `on_created` | `(self, event)` | - |
|   \u2b91 `on_moved` | `(self, event)` | - |
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
#### `backend/__init__.py` (2 行)

---
#### `backend/core/skills_scanner.py` (212 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `scan_claude_skills` | `(project_root: str) -> List[Dict]` | 扫描 .claude/skills/ 目录下的 Skill |
| `scan_agents_skills` | `(project_root: str) -> List[Dict]` | 扫描 .agents/skills/ 目录下的 Skill |
| `scan_all_local_skills` | `(project_root: str) -> List[Dict]` | 扫描所有本地 Skill |
| `sync_local_skills_to_db` | `(db_path: str, project_root: str) -> Dict` | 将本地 Skill 扫描结果同步到数据库 |
| `get_local_skills_from_db` | `(db_path: str) -> List[Dict]` | 从数据库获取本地 Skill 列表 |
| `toggle_skill` | `(db_path: str, skill_id: str, enabled: bool) -> Dict` | 启用/禁用 Skill |
| `uninstall_skill` | `(db_path: str, skill_id: str, project_root: str) -> Dict` | 卸载 Skill：删除文件 + 删除数据库记录 |

---
#### `backend/core/skills_sync.py` (244 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `sync_from_awesome_claude_code` | `(db_path: str) -> Dict` | 从 awesome-claude-code 同步 Skill 目录  Returns: {"success": bool, "added": int, "upd |
| `get_skill_categories` | `(db_path: str) -> List[str]` | 获取所有分类列表 |
| `get_sync_stats` | `(db_path: str) -> Dict` | 获取同步统计信息 |

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
#### `backend/mcp_server.py` (823 行)

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
- `from mcp.server import Server`
- `from mcp.server.models import InitializationOptions, ServerCapabilities`
- `from mcp.server.stdio import stdio_server`
- `from mcp.types import Tool, TextContent`

---
#### `backend/social_parsers.py` (352 行)

**类 `QwenASR`** — 行 33

**类 `BilibiliParser`** — 行 99

**类 `XiaohongshuParser`** — 行 231

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, api_key: Optional[str] = None, model: str = DEFAULT_ASR_MODEL)` | - |
|   \u2b91 `recognize` | `(self, audio_input, context=None, language=None, enable_lid=True, enable_itn=False) -> dict` | - |
|   \u2b91 `extract_bvid` | `(share_text: str) -> str` | - |
|   \u2b91 `get_video_info` | `(share_text: str) -> dict` | - |
|   \u2b91 `get_play_url` | `(bvid: str, cid: int, quality: int = 80) -> dict` | - |
|   \u2b91 `get_audio_url` | `(share_text: str, cid: Optional[int] = None) -> tuple` | 返回 (audio_url, video_info_dict) |
|   \u2b91 `extract_note_id` | `(share_text: str) -> str` | - |
|   \u2b91 `get_note_info` | `(share_text: str) -> dict` | - |
|   \u2b91 `get_video_url` | `(share_text: str) -> tuple` | 返回 (video_url, note_info_dict) |

---
#### `backend/sop_evolution.py` (297 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `analyze_wiki_for_sop` | `(wiki_page_ids: list[int] = None, force: bool = False, limit: int = 100) -> dict` | Analyze wiki pages and generate SOP suggestions.  Args: wiki_page_ids: Optional  |

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
#### `backend/workflow/__init__.py` (3 行)

---
#### `backend/workflow/engine.py` (343 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `launch` | `(yaml_path: str, params: dict | None = None) -> str` | 启动一个 workflow，返回 task_id。 |
| `pause` | `(task_id: str) -> bool` | - |
| `resume` | `(task_id: str, user_input: dict | None = None) -> bool` | - |
| `list_recent` | `(limit: int = 20, include_archived: bool = False) -> list[dict]` | - |
| `archive` | `(task_id: str) -> bool` | 切换归档状态。 |

---
#### `backend/workflow/executors.py` (362 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `setup_builtin_tools` | `()` | - |

**关键依赖：**
- `import httpx`
- `from ai_client import API_KEY, API_BASE, MODEL`

---
#### `backend/workflow/loader.py` (226 行)

**类 `ParamDef`** — 行 22

**类 `GateDef`** — 行 30

**类 `StepDef`** — 行 37

**类 `WorkflowTemplate`** — 行 50

| 函数 | 签名 | 说明 |
|------|------|------|
| `resolve_template` | `(text: str, context: dict) -> str` | 解析字符串中的所有 {{.xxx}} 模板变量。 |
| `resolve_in` | `(obj, context: dict)` | 递归解析对象中所有字符串的模板变量。 |
| `load` | `(yaml_path: str) -> WorkflowTemplate` | 加载并校验一个 YAML workflow 模板。 |

---
#### `backend/workflow/registry.py` (75 行)

**类 `ToolDef`** — 行 10

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `to_dict` | `(self)` | - |
| `register` | `(name: str, desc: str, inputs: dict, outputs: dict, executor) -> None` | 注册一个工具。 |
| `list_tools` | `() -> list[dict]` | 列出所有已注册工具的信息（给前端）。 |
| `execute` | `(name: str, input_data: dict, context: dict, workspace: str) -> dict` | 执行工具调用。  参数： name       —— 工具名 input_data —— 步骤的 input 字段（模板变量已解析） context    —— |

---
#### `venv/Lib/site-packages/anyio/_backends/_asyncio.py` (2997 行)

**类 `_State`** (继承 `enum.Enum`) — 行 123

**类 `Runner`** — 行 128

**类 `CancelScope`** (继承 `BaseCancelScope`) — 行 389

**类 `TaskState`** — 行 693

**类 `_AsyncioTaskStatus`** (继承 `abc.TaskStatus`) — 行 714

**类 `TaskGroup`** (继承 `abc.TaskGroup`) — 行 738

**类 `WorkerThread`** (继承 `Thread`) — 行 950

**类 `StreamReaderWrapper`** (继承 `abc.ByteReceiveStream`) — 行 1040

**类 `StreamWriterWrapper`** (继承 `abc.ByteSendStream`) — 行 1056

**类 `Process`** (继承 `abc.Process`) — 行 1087

**类 `StreamProtocol`** (继承 `asyncio.Protocol`) — 行 1195

**类 `DatagramProtocol`** (继承 `asyncio.DatagramProtocol`) — 行 1233

**类 `SocketStream`** (继承 `abc.SocketStream`) — 行 1264

**类 `_RawSocketMixin`** — 行 1349

**类 `UNIXSocketStream`** (继承 `_RawSocketMixin, abc.UNIXSocketStream`) — 行 1395

**类 `TCPSocketListener`** (继承 `abc.SocketListener`) — 行 1511

**类 `UNIXSocketListener`** (继承 `abc.SocketListener`) — 行 1571

**类 `UDPSocket`** (继承 `abc.UDPSocket`) — 行 1608

**类 `ConnectedUDPSocket`** (继承 `abc.ConnectedUDPSocket`) — 行 1656

**类 `UNIXDatagramSocket`** (继承 `_RawSocketMixin, abc.UNIXDatagramSocket`) — 行 1706

**类 `ConnectedUNIXDatagramSocket`** (继承 `_RawSocketMixin, abc.ConnectedUNIXDatagramSocket`) — 行 1742

**类 `Event`** (继承 `BaseEvent`) — 行 1787

**类 `Lock`** (继承 `BaseLock`) — 行 1810

**类 `Semaphore`** (继承 `BaseSemaphore`) — 行 1884

**类 `CapacityLimiter`** (继承 `BaseCapacityLimiter`) — 行 1965

**类 `_SignalReceiver`** — 行 2093

**类 `AsyncIOTaskInfo`** (继承 `TaskInfo`) — 行 2139

**类 `TestRunner`** (继承 `abc.TestRunner`) — 行 2172

**类 `AsyncIOBackend`** (继承 `AsyncBackend`) — 行 2325

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `close` | `(self) -> None` | Shutdown and close event loop. |
|   \u2b91 `get_loop` | `(self) -> AbstractEventLoop` | Return embedded event loop. |
|   \u2b91 `run` | `(self, coro: Coroutine[T_Retval], *, context=None) -> T_Retval` | Run a coroutine inside the embedded event loop. |
| `find_root_task` | `() -> asyncio.Task` | - |
| `get_callable_name` | `(func: Callable) -> str` | - |
| `is_anyio_cancellation` | `(exc: CancelledError) -> bool` | - |
|   \u2b91 `__init__` | `(self, deadline: float = math.inf, shield: bool = False)` | - |
|   \u2b91 `cancel` | `(self, reason: str | None = None) -> None` | - |
|   \u2b91 `deadline` | `(self) -> float` | - |
|   \u2b91 `deadline` | `(self, value: float) -> None` | - |
|   \u2b91 `cancel_called` | `(self) -> bool` | - |
|   \u2b91 `cancelled_caught` | `(self) -> bool` | - |
|   \u2b91 `shield` | `(self) -> bool` | - |
|   \u2b91 `shield` | `(self, value: bool) -> None` | - |
|   \u2b91 `__init__` | `(self, parent_id: int | None, cancel_scope: CancelScope | None)` | - |
|   \u2b91 `__init__` | `(self, future: asyncio.Future, parent_id: int)` | - |
|   \u2b91 `started` | `(self, value: T_contra | None = None) -> None` | - |
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `task_done` | `(_task: asyncio.Task) -> None` | - |
|   \u2b91 `run` | `(self) -> None` | - |
|   \u2b91 `stop` | `(self, f: asyncio.Task | None = None) -> None` | - |
|   \u2b91 `receive` | `(self, max_bytes: int = 65536) -> bytes` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `wait` | `(self) -> int` | - |
|   \u2b91 `terminate` | `(self) -> None` | - |
|   \u2b91 `kill` | `(self) -> None` | - |
|   \u2b91 `send_signal` | `(self, signal: int) -> None` | - |
|   \u2b91 `pid` | `(self) -> int` | - |
|   \u2b91 `connection_made` | `(self, transport: asyncio.BaseTransport) -> None` | - |
|   \u2b91 `connection_lost` | `(self, exc: Exception | None) -> None` | - |
|   \u2b91 `data_received` | `(self, data: bytes) -> None` | - |
|   \u2b91 `pause_writing` | `(self) -> None` | - |
|   \u2b91 `resume_writing` | `(self) -> None` | - |
|   \u2b91 `connection_made` | `(self, transport: asyncio.BaseTransport) -> None` | - |
|   \u2b91 `connection_lost` | `(self, exc: Exception | None) -> None` | - |
|   \u2b91 `datagram_received` | `(self, data: bytes, addr: IPSockAddrType) -> None` | - |
|   \u2b91 `error_received` | `(self, exc: Exception) -> None` | - |
|   \u2b91 `pause_writing` | `(self) -> None` | - |
|   \u2b91 `resume_writing` | `(self) -> None` | - |
|   \u2b91 `__init__` | `(self, transport: asyncio.Transport, protocol: StreamProtocol)` | - |
|   \u2b91 `receive` | `(self, max_bytes: int = 65536) -> bytes` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `send_eof` | `(self) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `__init__` | `(self, raw_socket: socket.socket)` | - |
|   \u2b91 `callback` | `(f: object) -> None` | - |
|   \u2b91 `callback` | `(f: object) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `send_eof` | `(self) -> None` | - |
|   \u2b91 `receive` | `(self, max_bytes: int = 65536) -> bytes` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `send_fds` | `(self, message: bytes, fds: Collection[int | IOBase]) -> None` | - |
|   \u2b91 `__init__` | `(self, raw_socket: socket.socket)` | - |
|   \u2b91 `accept` | `(self) -> abc.SocketStream` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `__init__` | `(self, raw_socket: socket.socket)` | - |
|   \u2b91 `accept` | `(self) -> abc.SocketStream` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `send` | `(self, item: UDPPacketType) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `receive` | `(self) -> bytes` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `receive` | `(self) -> UNIXDatagramPacketType` | - |
|   \u2b91 `send` | `(self, item: UNIXDatagramPacketType) -> None` | - |
|   \u2b91 `receive` | `(self) -> bytes` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `set` | `(self) -> None` | - |
|   \u2b91 `is_set` | `(self) -> bool` | - |
|   \u2b91 `wait` | `(self) -> None` | - |
|   \u2b91 `statistics` | `(self) -> EventStatistics` | - |
|   \u2b91 `__init__` | `(self, *, fast_acquire: bool = False) -> None` | - |
|   \u2b91 `acquire` | `(self) -> None` | - |
|   \u2b91 `acquire_nowait` | `(self) -> None` | - |
|   \u2b91 `locked` | `(self) -> bool` | - |
|   \u2b91 `release` | `(self) -> None` | - |
|   \u2b91 `statistics` | `(self) -> LockStatistics` | - |
|   \u2b91 `acquire` | `(self) -> None` | - |
|   \u2b91 `acquire_nowait` | `(self) -> None` | - |
|   \u2b91 `release` | `(self) -> None` | - |
|   \u2b91 `value` | `(self) -> int` | - |
|   \u2b91 `statistics` | `(self) -> SemaphoreStatistics` | - |
|   \u2b91 `__init__` | `(self, total_tokens: float)` | - |
|   \u2b91 `total_tokens` | `(self) -> float` | - |
|   \u2b91 `total_tokens` | `(self, value: float) -> None` | - |
|   \u2b91 `borrowed_tokens` | `(self) -> int` | - |
|   \u2b91 `available_tokens` | `(self) -> float` | - |
|   \u2b91 `acquire_nowait` | `(self) -> None` | - |
|   \u2b91 `acquire_on_behalf_of_nowait` | `(self, borrower: object) -> None` | - |
|   \u2b91 `acquire` | `(self) -> None` | - |
|   \u2b91 `acquire_on_behalf_of` | `(self, borrower: object) -> None` | - |
|   \u2b91 `release` | `(self) -> None` | - |
|   \u2b91 `release_on_behalf_of` | `(self, borrower: object) -> None` | - |
|   \u2b91 `statistics` | `(self) -> CapacityLimiterStatistics` | - |
|   \u2b91 `__init__` | `(self, signals: tuple[Signals, ...])` | - |
|   \u2b91 `__init__` | `(self, task: asyncio.Task)` | - |
|   \u2b91 `has_pending_cancellation` | `(self) -> bool` | - |
|   \u2b91 `get_loop` | `(self) -> AbstractEventLoop` | - |
|   \u2b91 `wrapper` | `() -> T_Retval` | - |
|   \u2b91 `current_token` | `(cls) -> object` | - |
|   \u2b91 `current_time` | `(cls) -> float` | - |
|   \u2b91 `cancelled_exception_class` | `(cls) -> type[BaseException]` | - |
|   \u2b91 `checkpoint` | `(cls) -> None` | - |
|   \u2b91 `checkpoint_if_cancelled` | `(cls) -> None` | - |
|   \u2b91 `cancel_shielded_checkpoint` | `(cls) -> None` | - |
|   \u2b91 `sleep` | `(cls, delay: float) -> None` | - |
|   \u2b91 `current_effective_deadline` | `(cls) -> float` | - |
|   \u2b91 `create_task_group` | `(cls) -> abc.TaskGroup` | - |
|   \u2b91 `create_event` | `(cls) -> abc.Event` | - |
|   \u2b91 `create_lock` | `(cls, *, fast_acquire: bool) -> abc.Lock` | - |
|   \u2b91 `create_capacity_limiter` | `(cls, total_tokens: float) -> abc.CapacityLimiter` | - |
|   \u2b91 `check_cancelled` | `(cls) -> None` | - |
|   \u2b91 `task_wrapper` | `() -> T_Retval` | - |
|   \u2b91 `wrapper` | `() -> None` | - |
|   \u2b91 `setup_process_pool_exit_at_shutdown` | `(cls, workers: set[abc.Process]) -> None` | - |
|   \u2b91 `connect_unix` | `(cls, path: str | bytes) -> abc.UNIXSocketStream` | - |
|   \u2b91 `create_tcp_listener` | `(cls, sock: socket.socket) -> SocketListener` | - |
|   \u2b91 `create_unix_listener` | `(cls, sock: socket.socket) -> SocketListener` | - |
|   \u2b91 `wait_readable` | `(cls, obj: FileDescriptorLike) -> None` | - |
|   \u2b91 `cb` | `() -> None` | - |
|   \u2b91 `wait_writable` | `(cls, obj: FileDescriptorLike) -> None` | - |
|   \u2b91 `cb` | `() -> None` | - |
|   \u2b91 `notify_closing` | `(cls, obj: FileDescriptorLike) -> None` | - |
|   \u2b91 `wrap_listener_socket` | `(cls, sock: socket.socket) -> SocketListener` | - |
|   \u2b91 `wrap_stream_socket` | `(cls, sock: socket.socket) -> SocketStream` | - |
|   \u2b91 `wrap_unix_stream_socket` | `(cls, sock: socket.socket) -> UNIXSocketStream` | - |
|   \u2b91 `wrap_udp_socket` | `(cls, sock: socket.socket) -> UDPSocket` | - |
|   \u2b91 `wrap_connected_udp_socket` | `(cls, sock: socket.socket) -> ConnectedUDPSocket` | - |
|   \u2b91 `wrap_unix_datagram_socket` | `(cls, sock: socket.socket) -> UNIXDatagramSocket` | - |
|   \u2b91 `current_default_thread_limiter` | `(cls) -> CapacityLimiter` | - |
|   \u2b91 `get_current_task` | `(cls) -> TaskInfo` | - |
|   \u2b91 `get_running_tasks` | `(cls) -> Sequence[TaskInfo]` | - |
|   \u2b91 `wait_all_tasks_blocked` | `(cls) -> None` | - |
|   \u2b91 `create_test_runner` | `(cls, options: dict[str, Any]) -> TestRunner` | - |

---
#### `venv/Lib/site-packages/anyio/_backends/_trio.py` (1344 行)

**类 `CancelScope`** (继承 `BaseCancelScope`) — 行 113

**类 `TaskGroup`** (继承 `abc.TaskGroup`) — 行 167

**类 `ReceiveStreamWrapper`** (继承 `abc.ByteReceiveStream`) — 行 227

**类 `SendStreamWrapper`** (继承 `abc.ByteSendStream`) — 行 248

**类 `Process`** (继承 `abc.Process`) — 行 264

**类 `_ProcessPoolShutdownInstrument`** (继承 `trio.abc.Instrument`) — 行 320

**类 `_TrioSocketMixin`** (继承 `Generic[T_SockAddr]`) — 行 348

**类 `SocketStream`** (继承 `_TrioSocketMixin, abc.SocketStream`) — 行 379

**类 `UNIXSocketStream`** (继承 `SocketStream, abc.UNIXSocketStream`) — 行 412

**类 `TCPSocketListener`** (继承 `_TrioSocketMixin, abc.SocketListener`) — 行 479

**类 `UNIXSocketListener`** (继承 `_TrioSocketMixin, abc.SocketListener`) — 行 495

**类 `UDPSocket`** (继承 `_TrioSocketMixin[IPSockAddrType], abc.UDPSocket`) — 行 510

**类 `ConnectedUDPSocket`** (继承 `_TrioSocketMixin[IPSockAddrType], abc.ConnectedUDPSocket`) — 行 532

**类 `UNIXDatagramSocket`** (继承 `_TrioSocketMixin[str], abc.UNIXDatagramSocket`) — 行 553

**类 `Event`** (继承 `BaseEvent`) — 行 603

**类 `Lock`** (继承 `BaseLock`) — 行 624

**类 `Semaphore`** (继承 `BaseSemaphore`) — 行 680

**类 `CapacityLimiter`** (继承 `BaseCapacityLimiter`) — 行 734

**类 `_SignalReceiver`** — 行 818

**类 `TestRunner`** (继承 `abc.TestRunner`) — 行 850

**类 `TrioTaskInfo`** (继承 `TaskInfo`) — 行 938

**类 `TrioBackend`** (继承 `AsyncBackend`) — 行 956

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, original: trio.CancelScope | None = None, **kwargs: Any) -> None` | - |
|   \u2b91 `cancel` | `(self, reason: str | None = None) -> None` | - |
|   \u2b91 `deadline` | `(self) -> float` | - |
|   \u2b91 `deadline` | `(self, value: float) -> None` | - |
|   \u2b91 `cancel_called` | `(self) -> bool` | - |
|   \u2b91 `cancelled_caught` | `(self) -> bool` | - |
|   \u2b91 `shield` | `(self) -> bool` | - |
|   \u2b91 `shield` | `(self, value: bool) -> None` | - |
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `receive` | `(self, max_bytes: int | None = None) -> bytes` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `wait` | `(self) -> int` | - |
|   \u2b91 `terminate` | `(self) -> None` | - |
|   \u2b91 `kill` | `(self) -> None` | - |
|   \u2b91 `send_signal` | `(self, signal: Signals) -> None` | - |
|   \u2b91 `pid` | `(self) -> int` | - |
|   \u2b91 `after_run` | `(self) -> None` | - |
|   \u2b91 `__init__` | `(self, trio_socket: TrioSocketType) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `__init__` | `(self, trio_socket: TrioSocketType) -> None` | - |
|   \u2b91 `receive` | `(self, max_bytes: int = 65536) -> bytes` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `send_eof` | `(self) -> None` | - |
|   \u2b91 `send_fds` | `(self, message: bytes, fds: Collection[int | IOBase]) -> None` | - |
|   \u2b91 `__init__` | `(self, raw_socket: socket.socket)` | - |
|   \u2b91 `accept` | `(self) -> SocketStream` | - |
|   \u2b91 `__init__` | `(self, raw_socket: socket.socket)` | - |
|   \u2b91 `accept` | `(self) -> UNIXSocketStream` | - |
|   \u2b91 `__init__` | `(self, trio_socket: TrioSocketType) -> None` | - |
|   \u2b91 `send` | `(self, item: UDPPacketType) -> None` | - |
|   \u2b91 `__init__` | `(self, trio_socket: TrioSocketType) -> None` | - |
|   \u2b91 `receive` | `(self) -> bytes` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `__init__` | `(self, trio_socket: TrioSocketType) -> None` | - |
|   \u2b91 `receive` | `(self) -> UNIXDatagramPacketType` | - |
|   \u2b91 `send` | `(self, item: UNIXDatagramPacketType) -> None` | - |
|   \u2b91 `__init__` | `(self, trio_socket: TrioSocketType) -> None` | - |
|   \u2b91 `receive` | `(self) -> bytes` | - |
|   \u2b91 `send` | `(self, item: bytes) -> None` | - |
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `is_set` | `(self) -> bool` | - |
|   \u2b91 `wait` | `(self) -> None` | - |
|   \u2b91 `statistics` | `(self) -> EventStatistics` | - |
|   \u2b91 `set` | `(self) -> None` | - |
|   \u2b91 `__init__` | `(self, *, fast_acquire: bool = False) -> None` | - |
|   \u2b91 `acquire` | `(self) -> None` | - |
|   \u2b91 `acquire_nowait` | `(self) -> None` | - |
|   \u2b91 `locked` | `(self) -> bool` | - |
|   \u2b91 `release` | `(self) -> None` | - |
|   \u2b91 `statistics` | `(self) -> LockStatistics` | - |
|   \u2b91 `acquire` | `(self) -> None` | - |
|   \u2b91 `acquire_nowait` | `(self) -> None` | - |
|   \u2b91 `value` | `(self) -> int` | - |
|   \u2b91 `release` | `(self) -> None` | - |
|   \u2b91 `statistics` | `(self) -> SemaphoreStatistics` | - |
|   \u2b91 `total_tokens` | `(self) -> float` | - |
|   \u2b91 `total_tokens` | `(self, value: float) -> None` | - |
|   \u2b91 `borrowed_tokens` | `(self) -> int` | - |
|   \u2b91 `available_tokens` | `(self) -> float` | - |
|   \u2b91 `acquire_nowait` | `(self) -> None` | - |
|   \u2b91 `acquire_on_behalf_of_nowait` | `(self, borrower: object) -> None` | - |
|   \u2b91 `acquire` | `(self) -> None` | - |
|   \u2b91 `acquire_on_behalf_of` | `(self, borrower: object) -> None` | - |
|   \u2b91 `release` | `(self) -> None` | - |
|   \u2b91 `release_on_behalf_of` | `(self, borrower: object) -> None` | - |
|   \u2b91 `statistics` | `(self) -> CapacityLimiterStatistics` | - |
|   \u2b91 `__init__` | `(self, signals: tuple[Signals, ...])` | - |
|   \u2b91 `__init__` | `(self, **options: Any) -> None` | - |
|   \u2b91 `__init__` | `(self, task: trio.lowlevel.Task)` | - |
|   \u2b91 `has_pending_cancellation` | `(self) -> bool` | - |
|   \u2b91 `current_token` | `(cls) -> object` | - |
|   \u2b91 `current_time` | `(cls) -> float` | - |
|   \u2b91 `cancelled_exception_class` | `(cls) -> type[BaseException]` | - |
|   \u2b91 `checkpoint` | `(cls) -> None` | - |
|   \u2b91 `checkpoint_if_cancelled` | `(cls) -> None` | - |
|   \u2b91 `cancel_shielded_checkpoint` | `(cls) -> None` | - |
|   \u2b91 `sleep` | `(cls, delay: float) -> None` | - |
|   \u2b91 `current_effective_deadline` | `(cls) -> float` | - |
|   \u2b91 `create_task_group` | `(cls) -> abc.TaskGroup` | - |
|   \u2b91 `create_event` | `(cls) -> abc.Event` | - |
|   \u2b91 `create_lock` | `(cls, *, fast_acquire: bool) -> Lock` | - |
|   \u2b91 `create_capacity_limiter` | `(cls, total_tokens: float) -> CapacityLimiter` | - |
|   \u2b91 `wrapper` | `() -> T_Retval` | - |
|   \u2b91 `check_cancelled` | `(cls) -> None` | - |
|   \u2b91 `convert_item` | `(item: StrOrBytesPath) -> str` | - |
|   \u2b91 `setup_process_pool_exit_at_shutdown` | `(cls, workers: set[abc.Process]) -> None` | - |
|   \u2b91 `connect_unix` | `(cls, path: str | bytes) -> abc.UNIXSocketStream` | - |
|   \u2b91 `create_tcp_listener` | `(cls, sock: socket.socket) -> abc.SocketListener` | - |
|   \u2b91 `create_unix_listener` | `(cls, sock: socket.socket) -> abc.SocketListener` | - |
|   \u2b91 `wait_readable` | `(cls, obj: FileDescriptorLike) -> None` | - |
|   \u2b91 `wait_writable` | `(cls, obj: FileDescriptorLike) -> None` | - |
|   \u2b91 `notify_closing` | `(cls, obj: FileDescriptorLike) -> None` | - |
|   \u2b91 `wrap_listener_socket` | `(cls, sock: socket.socket) -> abc.SocketListener` | - |
|   \u2b91 `wrap_stream_socket` | `(cls, sock: socket.socket) -> SocketStream` | - |
|   \u2b91 `wrap_unix_stream_socket` | `(cls, sock: socket.socket) -> UNIXSocketStream` | - |
|   \u2b91 `wrap_udp_socket` | `(cls, sock: socket.socket) -> UDPSocket` | - |
|   \u2b91 `wrap_connected_udp_socket` | `(cls, sock: socket.socket) -> ConnectedUDPSocket` | - |
|   \u2b91 `wrap_unix_datagram_socket` | `(cls, sock: socket.socket) -> UNIXDatagramSocket` | - |
|   \u2b91 `current_default_thread_limiter` | `(cls) -> CapacityLimiter` | - |
|   \u2b91 `get_current_task` | `(cls) -> TaskInfo` | - |
|   \u2b91 `get_running_tasks` | `(cls) -> Sequence[TaskInfo]` | - |
|   \u2b91 `wait_all_tasks_blocked` | `(cls) -> None` | - |
|   \u2b91 `create_test_runner` | `(cls, options: dict[str, Any]) -> TestRunner` | - |

---
#### `venv/Lib/site-packages/cffi/backend_ctypes.py` (1122 行)

**类 `CTypesType`** (继承 `type`) — 行 12

**类 `CTypesData`** (继承 `object`) — 行 15

**类 `CTypesGenericPrimitive`** (继承 `CTypesData`) — 行 146

**类 `CTypesGenericArray`** (继承 `CTypesData`) — 行 156

**类 `CTypesGenericPtr`** (继承 `CTypesData`) — 行 171

**类 `CTypesBaseStructOrUnion`** (继承 `CTypesData`) — 行 238

**类 `CTypesBackend`** (继承 `object`) — 行 273

**类 `CTypesVoid`** (继承 `CTypesData`) — 行 328

**类 `CTypesPrimitive`** (继承 `CTypesGenericPrimitive`) — 行 375

**类 `CTypesPtr`** (继承 `CTypesGenericPtr`) — 行 509

**类 `CTypesArray`** (继承 `CTypesGenericArray`) — 行 608

**类 `struct_or_union`** (继承 `base_ctypes_class`) — 行 716

**类 `CTypesStructOrUnion`** (继承 `CTypesBaseStructOrUnion`) — 行 721

**类 `CTypesFunctionPtr`** (继承 `CTypesGenericPtr`) — 行 854

**类 `CTypesEnum`** (继承 `CTypesInt`) — 行 954

**类 `MyRef`** (继承 `weakref.ref`) — 行 1015

**类 `CTypesLibrary`** (继承 `object`) — 行 1097

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, *args)` | - |
|   \u2b91 `cmp` | `(self, other)` | - |
|   \u2b91 `__init__` | `(self)` | - |
|   \u2b91 `set_ffi` | `(self, ffi)` | - |
|   \u2b91 `load_library` | `(self, path, flags=0)` | - |
|   \u2b91 `new_void_type` | `(self)` | - |
|   \u2b91 `new_primitive_type` | `(self, name)` | - |
|   \u2b91 `__init__` | `(self, value)` | - |
|   \u2b91 `new_pointer_type` | `(self, BItem)` | - |
|   \u2b91 `__init__` | `(self, init)` | - |
|   \u2b91 `new_array_type` | `(self, CTypesPtr, length)` | - |
|   \u2b91 `__init__` | `(self, init)` | - |
|   \u2b91 `new_struct_type` | `(self, name)` | - |
|   \u2b91 `new_union_type` | `(self, name)` | - |
|   \u2b91 `initialize` | `(blob, init)` | - |
|   \u2b91 `setter` | `(self, value, fname=fname, BField=BField)` | - |
|   \u2b91 `getter` | `(self, fname=fname, BField=BField)` | - |
|   \u2b91 `setter` | `(self, value, fname=fname, BField=BField)` | - |
|   \u2b91 `getter` | `(self, fname=fname)` | - |
|   \u2b91 `setter` | `(self, value, fname=fname)` | - |
|   \u2b91 `new_function_type` | `(self, BArgs, BResult, has_varargs)` | - |
|   \u2b91 `__init__` | `(self, init, error=None)` | - |
|   \u2b91 `callback` | `(*args)` | - |
|   \u2b91 `new_enum_type` | `(self, name, enumerators, enumvalues, CTypesInt)` | - |
|   \u2b91 `get_errno` | `(self)` | - |
|   \u2b91 `set_errno` | `(self, value)` | - |
|   \u2b91 `string` | `(self, b, maxlen=-1)` | - |
|   \u2b91 `buffer` | `(self, bptr, size=-1)` | - |
|   \u2b91 `sizeof` | `(self, cdata_or_BType)` | - |
|   \u2b91 `alignof` | `(self, BType)` | - |
|   \u2b91 `newp` | `(self, BType, source)` | - |
|   \u2b91 `cast` | `(self, BType, source)` | - |
|   \u2b91 `callback` | `(self, BType, source, error, onerror)` | - |
|   \u2b91 `gcp` | `(self, cdata, destructor, size=0)` | - |
|   \u2b91 `remove` | `(k)` | - |
|   \u2b91 `getcname` | `(self, BType, replace_with)` | - |
|   \u2b91 `typeoffsetof` | `(self, BType, fieldname, num=0)` | - |
|   \u2b91 `rawaddressof` | `(self, BTypePtr, cdata, offset=None)` | - |
|   \u2b91 `__init__` | `(self, backend, cdll)` | - |
|   \u2b91 `load_function` | `(self, BType, name)` | - |
|   \u2b91 `read_variable` | `(self, BType, name)` | - |
|   \u2b91 `write_variable` | `(self, BType, name, value)` | - |

---
#### `venv/Lib/site-packages/cryptography/hazmat/backends/__init__.py` (14 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `default_backend` | `() -> Any` | - |

---
#### `venv/Lib/site-packages/cryptography/hazmat/backends/openssl/__init__.py` (10 行)

---
#### `venv/Lib/site-packages/cryptography/hazmat/backends/openssl/backend.py` (313 行)

**类 `Backend`** — 行 31

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `openssl_assert` | `(self, ok: bool) -> None` | - |
|   \u2b91 `openssl_version_text` | `(self) -> str` | Friendly string name of the loaded OpenSSL library. This is not necessarily the  |
|   \u2b91 `openssl_version_number` | `(self) -> int` | - |
|   \u2b91 `hash_supported` | `(self, algorithm: hashes.HashAlgorithm) -> bool` | - |
|   \u2b91 `scrypt_supported` | `(self) -> bool` | - |
|   \u2b91 `argon2_supported` | `(self) -> bool` | - |
|   \u2b91 `hmac_supported` | `(self, algorithm: hashes.HashAlgorithm) -> bool` | - |
|   \u2b91 `cipher_supported` | `(self, cipher: CipherAlgorithm, mode: Mode) -> bool` | - |
|   \u2b91 `pbkdf2_hmac_supported` | `(self, algorithm: hashes.HashAlgorithm) -> bool` | - |
|   \u2b91 `rsa_padding_supported` | `(self, padding: AsymmetricPadding) -> bool` | - |
|   \u2b91 `rsa_encryption_supported` | `(self, padding: AsymmetricPadding) -> bool` | - |
|   \u2b91 `dsa_supported` | `(self) -> bool` | - |
|   \u2b91 `dsa_hash_supported` | `(self, algorithm: hashes.HashAlgorithm) -> bool` | - |
|   \u2b91 `cmac_algorithm_supported` | `(self, algorithm) -> bool` | - |
|   \u2b91 `elliptic_curve_supported` | `(self, curve: ec.EllipticCurve) -> bool` | - |
|   \u2b91 `dh_supported` | `(self) -> bool` | - |
|   \u2b91 `dh_x942_serialization_supported` | `(self) -> bool` | - |
|   \u2b91 `x25519_supported` | `(self) -> bool` | - |
|   \u2b91 `x448_supported` | `(self) -> bool` | - |
|   \u2b91 `mlkem_supported` | `(self) -> bool` | - |
|   \u2b91 `mldsa_supported` | `(self) -> bool` | - |
|   \u2b91 `ed25519_supported` | `(self) -> bool` | - |
|   \u2b91 `ed448_supported` | `(self) -> bool` | - |
|   \u2b91 `ecdsa_deterministic_supported` | `(self) -> bool` | - |
|   \u2b91 `poly1305_supported` | `(self) -> bool` | - |
|   \u2b91 `pkcs7_supported` | `(self) -> bool` | - |

---
#### `venv/Lib/site-packages/google/api/backend_pb2.py` (61 行)

---
#### `venv/Lib/site-packages/httpcore/_backends/anyio.py` (147 行)

**类 `AnyIOStream`** (继承 `AsyncNetworkStream`) — 行 21

**类 `AnyIOBackend`** (继承 `AsyncNetworkBackend`) — 行 97

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, stream: anyio.abc.ByteStream) -> None` | - |
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |
|   \u2b91 `sleep` | `(self, seconds: float) -> None` | - |

---
#### `venv/Lib/site-packages/httpcore/_backends/auto.py` (53 行)

**类 `AutoBackend`** (继承 `AsyncNetworkBackend`) — 行 9

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `sleep` | `(self, seconds: float) -> None` | - |

---
#### `venv/Lib/site-packages/httpcore/_backends/base.py` (102 行)

**类 `NetworkStream`** — 行 14

**类 `NetworkBackend`** — 行 36

**类 `AsyncNetworkStream`** — 行 59

**类 `AsyncNetworkBackend`** — 行 81

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `close` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |
|   \u2b91 `sleep` | `(self, seconds: float) -> None` | - |
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |
|   \u2b91 `sleep` | `(self, seconds: float) -> None` | - |

---
#### `venv/Lib/site-packages/httpcore/_backends/mock.py` (144 行)

**类 `MockSSLObject`** — 行 16

**类 `MockStream`** (继承 `NetworkStream`) — 行 24

**类 `MockBackend`** (继承 `NetworkBackend`) — 行 58

**类 `AsyncMockStream`** (继承 `AsyncNetworkStream`) — 行 85

**类 `AsyncMockBackend`** (继承 `AsyncNetworkBackend`) — 行 119

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, http2: bool)` | - |
|   \u2b91 `selected_alpn_protocol` | `(self) -> str` | - |
|   \u2b91 `__init__` | `(self, buffer: list[bytes], http2: bool = False) -> None` | - |
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `close` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |
|   \u2b91 `__init__` | `(self, buffer: list[bytes], http2: bool = False) -> None` | - |
|   \u2b91 `sleep` | `(self, seconds: float) -> None` | - |
|   \u2b91 `__init__` | `(self, buffer: list[bytes], http2: bool = False) -> None` | - |
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |
|   \u2b91 `__init__` | `(self, buffer: list[bytes], http2: bool = False) -> None` | - |
|   \u2b91 `sleep` | `(self, seconds: float) -> None` | - |

---
#### `venv/Lib/site-packages/httpcore/_backends/sync.py` (242 行)

**类 `TLSinTLSStream`** (继承 `NetworkStream`) — 行 23

**类 `SyncStream`** (继承 `NetworkStream`) — 行 120

**类 `SyncBackend`** (继承 `NetworkBackend`) — 行 187

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `close` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |
|   \u2b91 `__init__` | `(self, sock: socket.socket) -> None` | - |
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `close` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |

---
#### `venv/Lib/site-packages/httpcore/_backends/trio.py` (160 行)

**类 `TrioStream`** (继承 `AsyncNetworkStream`) — 行 21

**类 `TrioBackend`** (继承 `AsyncNetworkBackend`) — 行 109

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, stream: trio.abc.Stream) -> None` | - |
|   \u2b91 `read` | `(self, max_bytes: int, timeout: float | None = None) -> bytes` | - |
|   \u2b91 `write` | `(self, buffer: bytes, timeout: float | None = None) -> None` | - |
|   \u2b91 `aclose` | `(self) -> None` | - |
|   \u2b91 `get_extra_info` | `(self, info: str) -> typing.Any` | - |
|   \u2b91 `sleep` | `(self, seconds: float) -> None` | - |

---
#### `venv/Lib/site-packages/joblib/_parallel_backends.py` (754 行)

**类 `ParallelBackendBase`** (继承 `metaclass=ABCMeta`) — 行 29

**类 `SequentialBackend`** (继承 `ParallelBackendBase`) — 行 272

**类 `PoolManagerMixin`** (继承 `object`) — 行 306

**类 `AutoBatchingMixin`** (继承 `object`) — 行 365

**类 `ThreadingBackend`** (继承 `PoolManagerMixin, ParallelBackendBase`) — 行 471

**类 `MultiprocessingBackend`** (继承 `PoolManagerMixin, AutoBatchingMixin, ParallelBackendBase`) — 行 511

**类 `LokyBackend`** (继承 `AutoBatchingMixin, ParallelBackendBase`) — 行 604

**类 `FallbackToBackend`** (继承 `Exception`) — 行 732

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `supports_return_generator` | `(self)` | - |
|   \u2b91 `supports_timeout` | `(self)` | - |
|   \u2b91 `effective_n_jobs` | `(self, n_jobs)` | Determine the number of jobs that can actually run in parallel  n_jobs is the nu |
|   \u2b91 `apply_async` | `(self, func, callback=None)` | Deprecated: implement `submit` instead. |
|   \u2b91 `submit` | `(self, func, callback=None)` | Schedule a function to be run and return a future-like object.  This method shou |
|   \u2b91 `retrieve_result_callback` | `(self, out)` | Called within the callback function passed to `submit`.  This method can customi |
|   \u2b91 `retrieve_result` | `(self, out, timeout=None)` | Hook to retrieve the result when support_retrieve_callback=False.  The argument  |
|   \u2b91 `start_call` | `(self)` | Call-back method called at the beginning of a Parallel call |
|   \u2b91 `stop_call` | `(self)` | Call-back method called at the end of a Parallel call |
|   \u2b91 `terminate` | `(self)` | Shutdown the workers and free the shared memory. |
|   \u2b91 `compute_batch_size` | `(self)` | Determine the optimal batch size |
|   \u2b91 `batch_completed` | `(self, batch_size, duration)` | Callback indicate how long it took to run a batch |
|   \u2b91 `abort_everything` | `(self, ensure_ready=True)` | Abort any running tasks  This is called when an exception has been raised when e |
|   \u2b91 `get_nested_backend` | `(self)` | Backend instance to be used by nested Parallel calls.  By default a thread-based |
|   \u2b91 `retrieval_context` | `(self)` | Context manager to manage an execution context.  Calls to Parallel.retrieve will |
|   \u2b91 `in_main_thread` | `()` | - |
|   \u2b91 `effective_n_jobs` | `(self, n_jobs)` | Determine the number of jobs which are going to run in parallel |
|   \u2b91 `submit` | `(self, func, callback=None)` | Schedule a func to be run |
|   \u2b91 `retrieve_result_callback` | `(self, out)` | - |
|   \u2b91 `get_nested_backend` | `(self)` | - |
|   \u2b91 `effective_n_jobs` | `(self, n_jobs)` | Determine the number of jobs which are going to run in parallel |
|   \u2b91 `terminate` | `(self)` | Shutdown the process or thread pool |
|   \u2b91 `submit` | `(self, func, callback=None)` | Schedule a func to be run |
|   \u2b91 `retrieve_result_callback` | `(self, result)` | Mimic concurrent.futures results, raising an error if needed. |
|   \u2b91 `abort_everything` | `(self, ensure_ready=True)` | Shutdown the pool and restart a new one with the same parameters |
|   \u2b91 `__init__` | `(self, **kwargs)` | - |
|   \u2b91 `compute_batch_size` | `(self)` | Determine the optimal batch size |
|   \u2b91 `batch_completed` | `(self, batch_size, duration)` | Callback indicate how long it took to run a batch |
|   \u2b91 `reset_batch_stats` | `(self)` | Reset batch statistics to default values.  This avoids interferences with future |
|   \u2b91 `configure` | `(self, n_jobs=1, parallel=None, **backend_kwargs)` | Build a process or thread pool and return the number of workers |
|   \u2b91 `effective_n_jobs` | `(self, n_jobs)` | Determine the number of jobs which are going to run in parallel.  This also chec |
|   \u2b91 `terminate` | `(self)` | Shutdown the process or thread pool |
|   \u2b91 `effective_n_jobs` | `(self, n_jobs)` | Determine the number of jobs which are going to run in parallel |
|   \u2b91 `submit` | `(self, func, callback=None)` | Schedule a func to be run |
|   \u2b91 `retrieve_result_callback` | `(self, future)` | Retrieve the result, here out is the future given by submit |
|   \u2b91 `terminate` | `(self)` | - |
|   \u2b91 `abort_everything` | `(self, ensure_ready=True)` | Shutdown the workers and restart a new one with the same parameters |
|   \u2b91 `__init__` | `(self, backend)` | - |
| `inside_dask_worker` | `()` | Check whether the current function is executed inside a Dask worker. |

---
#### `venv/Lib/site-packages/joblib/_store_backends.py` (501 行)

**类 `CacheWarning`** (继承 `Warning`) — 行 26

**类 `StoreBackendBase`** (继承 `metaclass=ABCMeta`) — 行 47

**类 `StoreBackendMixin`** (继承 `object`) — 行 152

**类 `FileSystemStoreBackend`** (继承 `StoreBackendBase, StoreBackendMixin`) — 行 403

| 函数 | 签名 | 说明 |
|------|------|------|
| `concurrency_safe_write` | `(object_to_write, filename, write_func)` | Writes an object into a unique file in a concurrency-safe way. |
|   \u2b91 `create_location` | `(self, location)` | Creates a location on the store.  Parameters ---------- location: string The loc |
|   \u2b91 `clear_location` | `(self, location)` | Clears a location on the store.  Parameters ---------- location: string The loca |
|   \u2b91 `get_items` | `(self)` | Returns the whole list of items available in the store.  Returns ------- The lis |
|   \u2b91 `load_item` | `(self, call_id, verbose=1, timestamp=None, metadata=None)` | Load an item from the store given its id as a list of str. |
|   \u2b91 `dump_item` | `(self, call_id, item, verbose=1)` | Dump an item in the store at the id given as a list of str. |
|   \u2b91 `write_func` | `(to_write, dest_filename)` | - |
|   \u2b91 `clear_item` | `(self, call_id)` | Clear the item at the id, given as a list of str. |
|   \u2b91 `contains_item` | `(self, call_id)` | Check if there is an item at the id, given as a list of str. |
|   \u2b91 `get_item_info` | `(self, call_id)` | Return information about item. |
|   \u2b91 `get_metadata` | `(self, call_id)` | Return actual metadata of an item. |
|   \u2b91 `store_metadata` | `(self, call_id, metadata)` | Store metadata of a computation. |
|   \u2b91 `write_func` | `(to_write, dest_filename)` | - |
|   \u2b91 `contains_path` | `(self, call_id)` | Check cached function is available in store. |
|   \u2b91 `clear_path` | `(self, call_id)` | Clear all items with a common path in the store. |
|   \u2b91 `store_cached_func_code` | `(self, call_id, func_code=None)` | Store the code of the cached function. |
|   \u2b91 `get_cached_func_code` | `(self, call_id)` | Store the code of the cached function. |
|   \u2b91 `get_cached_func_info` | `(self, call_id)` | Return information related to the cached function if it exists. |
|   \u2b91 `clear` | `(self)` | Clear the whole store content. |
|   \u2b91 `enforce_store_limits` | `(self, bytes_limit, items_limit=None, age_limit=None)` | Remove the store's oldest files to enforce item, byte, and age limits. |
|   \u2b91 `clear_location` | `(self, location)` | Delete location on store. |
|   \u2b91 `create_location` | `(self, location)` | Create object location on store |
|   \u2b91 `get_items` | `(self)` | Returns the whole list of items available in the store. |
|   \u2b91 `configure` | `(self, location, verbose=1, backend_options=None)` | Configure the store backend.  For this backend, valid store options are 'compres |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/__init__.py` (15 行)

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/_posix_reduction.py` (68 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `DupFd` | `(fd)` | Return a wrapper for an fd. |
| `rebuild_connection` | `(df, readable, writable)` | - |
| `reduce_connection` | `(conn)` | - |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/_win_reduction.py` (19 行)

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/context.py` (406 行)

**类 `LokyContext`** (继承 `BaseContext`) — 行 321

**类 `LokyInitMainContext`** (继承 `LokyContext`) — 行 383

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_context` | `(method=None)` | - |
| `set_start_method` | `(method, force=False)` | - |
| `get_start_method` | `()` | - |
| `cpu_count` | `(only_physical_cores=False)` | Return the number of CPUs the current process can use.  The returned number of C |
|   \u2b91 `Queue` | `(self, maxsize=0, reducers=None)` | Returns a queue object |
|   \u2b91 `SimpleQueue` | `(self, reducers=None)` | Returns a queue object |
|   \u2b91 `Semaphore` | `(self, value=1)` | Returns a semaphore object |
|   \u2b91 `BoundedSemaphore` | `(self, value)` | Returns a bounded semaphore object |
|   \u2b91 `Lock` | `(self)` | Returns a lock object |
|   \u2b91 `RLock` | `(self)` | Returns a recurrent lock object |
|   \u2b91 `Condition` | `(self, lock=None)` | Returns a condition object |
|   \u2b91 `Event` | `(self)` | Returns an event object |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/fork_exec.py` (74 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `fork_exec` | `(cmd, keep_fds, env=None)` | - |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/popen_loky_posix.py` (194 行)

**类 `_DupFd`** — 行 26

**类 `Popen`** — 行 39

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, fd)` | - |
|   \u2b91 `detach` | `(self)` | - |
|   \u2b91 `__init__` | `(self, process_obj)` | - |
|   \u2b91 `duplicate_for_child` | `(self, fd)` | - |
|   \u2b91 `poll` | `(self, flag=os.WNOHANG)` | - |
|   \u2b91 `wait` | `(self, timeout=None)` | - |
|   \u2b91 `terminate` | `(self)` | - |
|   \u2b91 `thread_is_spawning` | `()` | - |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/popen_loky_win32.py` (174 行)

**类 `Popen`** (继承 `_Popen`) — 行 40

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, process_obj)` | - |
| `get_command_line` | `(pipe_handle, parent_pid, **kwds)` | Returns prefix of command line used for spawning a child process. |
| `is_forking` | `(argv)` | Return whether commandline indicates we are forking. |
| `main` | `(pipe_handle, parent_pid=None)` | Run code specified by data received over pipe. |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/process.py` (86 行)

**类 `LokyProcess`** (继承 `BaseProcess`) — 行 13

**类 `LokyInitMainProcess`** (继承 `LokyProcess`) — 行 48

**类 `AuthenticationKey`** (继承 `bytes`) — 行 76

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/queues.py` (237 行)

**类 `Queue`** (继承 `mp_Queue`) — 行 30

**类 `SimpleQueue`** (继承 `mp_SimpleQueue`) — 行 196

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, maxsize=0, reducers=None, ctx=None)` | - |
|   \u2b91 `__init__` | `(self, reducers=None, ctx=None)` | - |
|   \u2b91 `close` | `(self)` | - |
|   \u2b91 `put` | `(self, obj)` | - |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/reduction.py` (224 行)

**类 `_C`** — 行 43

**类 `CustomizablePickler`** (继承 `loky_pickler_cls`) — 行 132

| 函数 | 签名 | 说明 |
|------|------|------|
| `register` | `(type_, reduce_function)` | - |
|   \u2b91 `f` | `(self)` | - |
|   \u2b91 `h` | `(cls)` | - |
| `set_loky_pickler` | `(loky_pickler=None)` | - |
|   \u2b91 `__init__` | `(self, writer, reducers=None, protocol=HIGHEST_PROTOCOL)` | - |
|   \u2b91 `register` | `(self, type, reduce_func)` | Attach a reducer function to a given type in the dispatch table. |
| `get_loky_pickler_name` | `()` | - |
| `get_loky_pickler` | `()` | - |
| `dump` | `(obj, file, reducers=None, protocol=None)` | Replacement for pickle.dump() using _LokyPickler. |
| `dumps` | `(obj, reducers=None, protocol=None)` | - |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/resource_tracker.py` (412 行)

**类 `ResourceTracker`** (继承 `_ResourceTracker`) — 行 94

| 函数 | 签名 | 说明 |
|------|------|------|
| `cleanup_noop` | `(name)` | - |
|   \u2b91 `maybe_unlink` | `(self, name, rtype)` | Decrement the refcount of a resource, and delete it if it hits 0 |
|   \u2b91 `ensure_running` | `(self)` | Make sure that resource tracker process is running.  This can be run from any pr |
| `main` | `(fd, verbose=0)` | Run resource tracker. |
| `spawnv_passfds` | `(path, args, passfds)` | - |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/spawn.py` (245 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_executable` | `()` | - |
| `get_preparation_data` | `(name, init_main_module=True)` | Return info about parent needed by child to unpickle process object. |
| `prepare` | `(data, parent_sentinel=None)` | Try to get current process ready to unpickle process object. |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/synchronize.py` (410 行)

**类 `SemLock`** — 行 61

**类 `Semaphore`** (继承 `SemLock`) — 行 148

**类 `BoundedSemaphore`** (继承 `Semaphore`) — 行 170

**类 `Lock`** (继承 `SemLock`) — 行 190

**类 `RLock`** (继承 `SemLock`) — 行 216

**类 `Condition`** — 行 243

**类 `Event`** — 行 377

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, kind, value, maxvalue, name=None)` | - |
|   \u2b91 `__init__` | `(self, value=1)` | - |
|   \u2b91 `get_value` | `(self)` | - |
|   \u2b91 `__init__` | `(self, value=1)` | - |
|   \u2b91 `__init__` | `(self)` | - |
|   \u2b91 `__init__` | `(self)` | - |
|   \u2b91 `__init__` | `(self, lock=None)` | - |
|   \u2b91 `wait` | `(self, timeout=None)` | - |
|   \u2b91 `notify` | `(self)` | - |
|   \u2b91 `notify_all` | `(self)` | - |
|   \u2b91 `wait_for` | `(self, predicate, timeout=None)` | - |
|   \u2b91 `__init__` | `(self)` | - |
|   \u2b91 `is_set` | `(self)` | - |
|   \u2b91 `set` | `(self)` | - |
|   \u2b91 `clear` | `(self)` | - |
|   \u2b91 `wait` | `(self, timeout=None)` | - |

---
#### `venv/Lib/site-packages/joblib/externals/loky/backend/utils.py` (182 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `kill_process_tree` | `(process, use_psutil=True)` | Terminate process and its descendants with SIGKILL |
| `recursive_terminate` | `(process, use_psutil=True)` | - |
| `get_exitcodes_terminated_worker` | `(processes)` | Return a formatted string with the exitcodes of terminated workers.  If necessar |

---
#### `venv/Lib/site-packages/joblib/test/test_store_backends.py` (95 行)

**类 `UnpicklableObject`** (继承 `object`) — 行 70

**类 `UnpicklableObject`** (继承 `object`) — 行 85

| 函数 | 签名 | 说明 |
|------|------|------|
| `write_func` | `(output, filename)` | - |
| `load_func` | `(expected, filename)` | - |
| `concurrency_safe_write_rename` | `(to_write, filename, write_func)` | - |
| `test_concurrency_safe_write` | `(tmpdir, backend)` | - |
| `test_warning_on_dump_failure` | `(tmpdir)` | - |
| `test_warning_on_pickling_error` | `(tmpdir)` | - |

---
#### `venv/Lib/site-packages/kubernetes/client/models/v1_ingress_backend.py` (147 行)

**类 `V1IngressBackend`** (继承 `object`) — 行 21

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, resource=None, service=None, local_vars_configuration=None)` | V1IngressBackend - a model defined in OpenAPI"""  # noqa: E501 |
|   \u2b91 `resource` | `(self)` | Gets the resource of this V1IngressBackend.  # noqa: E501   :return: The resourc |
|   \u2b91 `resource` | `(self, resource)` | Sets the resource of this V1IngressBackend.   :param resource: The resource of t |
|   \u2b91 `service` | `(self)` | Gets the service of this V1IngressBackend.  # noqa: E501   :return: The service  |
|   \u2b91 `service` | `(self, service)` | Sets the service of this V1IngressBackend.   :param service: The service of this |
|   \u2b91 `to_dict` | `(self)` | Returns the model properties as a dict |
|   \u2b91 `to_str` | `(self)` | Returns the string representation of the model |

---
#### `venv/Lib/site-packages/kubernetes/client/models/v1_ingress_service_backend.py` (150 行)

**类 `V1IngressServiceBackend`** (继承 `object`) — 行 21

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, name=None, port=None, local_vars_configuration=None)` | V1IngressServiceBackend - a model defined in OpenAPI"""  # noqa: E501 |
|   \u2b91 `name` | `(self)` | Gets the name of this V1IngressServiceBackend.  # noqa: E501  name is the refere |
|   \u2b91 `name` | `(self, name)` | Sets the name of this V1IngressServiceBackend.  name is the referenced service.  |
|   \u2b91 `port` | `(self)` | Gets the port of this V1IngressServiceBackend.  # noqa: E501   :return: The port |
|   \u2b91 `port` | `(self, port)` | Sets the port of this V1IngressServiceBackend.   :param port: The port of this V |
|   \u2b91 `to_dict` | `(self)` | Returns the model properties as a dict |
|   \u2b91 `to_str` | `(self)` | Returns the string representation of the model |

---
#### `venv/Lib/site-packages/kubernetes/client/models/v1_service_backend_port.py` (151 行)

**类 `V1ServiceBackendPort`** (继承 `object`) — 行 21

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, name=None, number=None, local_vars_configuration=None)` | V1ServiceBackendPort - a model defined in OpenAPI"""  # noqa: E501 |
|   \u2b91 `name` | `(self)` | Gets the name of this V1ServiceBackendPort.  # noqa: E501  name is the name of t |
|   \u2b91 `name` | `(self, name)` | Sets the name of this V1ServiceBackendPort.  name is the name of the port on the |
|   \u2b91 `number` | `(self)` | Gets the number of this V1ServiceBackendPort.  # noqa: E501  number is the numer |
|   \u2b91 `number` | `(self, number)` | Sets the number of this V1ServiceBackendPort.  number is the numerical port numb |
|   \u2b91 `to_dict` | `(self)` | Returns the model properties as a dict |
|   \u2b91 `to_str` | `(self)` | Returns the string representation of the model |

---
#### `venv/Lib/site-packages/mpmath/libmp/backend.py` (116 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `exec_` | `(_code_, _globs_=None, _locs_=None)` | Execute code in a namespace. |

---
#### `venv/Lib/site-packages/networkx/utils/backends.py` (2172 行)

**类 `_dispatchable`** — 行 215

**类 `_LazyArgsRepr`** — 行 2135

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `check_result` | `(val, depth=0)` | - |
|   \u2b91 `check_iterator` | `(it)` | - |
|   \u2b91 `assert_graphs_equal` | `(G1, G2, strict=True)` | - |
|   \u2b91 `__init__` | `(self, func, args, kwargs)` | - |

---
#### `venv/Lib/site-packages/networkx/utils/tests/test_backends.py` (226 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `test_dispatch_kwds_vs_args` | `()` | - |
| `test_pickle` | `()` | - |
| `test_graph_converter_needs_backend` | `()` | - |
|   \u2b91 `from_scipy_sparse_array` | `(self, *args, **kwargs)` | - |
|   \u2b91 `convert_to_nx` | `(obj, *, name=None)` | - |
| `test_networkx_backend` | `()` | Test using `backend="networkx"` in a dispatchable function. |
|   \u2b91 `convert_to_nx` | `(obj, *, name=None)` | - |
| `test_dispatchable_are_functions` | `()` | - |
| `test_mixing_backend_graphs` | `()` | - |
| `test_bad_backend_name` | `()` | Using `backend=` raises with unknown backend even if there are no backends. |
| `test_not_implemented_by_nx` | `()` | - |
|   \u2b91 `stub_func_implementation` | `(G)` | - |
| `test_dispatch_graph_new` | `()` | - |

---
#### `venv/Lib/site-packages/numpy/f2py/_backends/__init__.py` (10 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `f2py_build_generator` | `(name)` | - |

---
#### `venv/Lib/site-packages/numpy/f2py/_backends/_backend.py` (45 行)

**类 `Backend`** (继承 `ABC`) — 行 4

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `compile` | `(self) -> None` | Compile the wrapper. |

---
#### `venv/Lib/site-packages/numpy/f2py/_backends/_distutils.py` (77 行)

**类 `DistutilsBackend`** (继承 `Backend`) — 行 14

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(sef, *args, **kwargs)` | - |
|   \u2b91 `compile` | `(self)` | - |

---
#### `venv/Lib/site-packages/numpy/f2py/_backends/_meson.py` (245 行)

**类 `MesonTemplate`** — 行 14

**类 `MesonBackend`** (继承 `Backend`) — 行 137

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `meson_build_template` | `(self) -> str` | - |
|   \u2b91 `initialize_template` | `(self) -> None` | - |
|   \u2b91 `sources_substitution` | `(self) -> None` | - |
|   \u2b91 `objects_substitution` | `(self) -> None` | - |
|   \u2b91 `deps_substitution` | `(self) -> None` | - |
|   \u2b91 `libraries_substitution` | `(self) -> None` | - |
|   \u2b91 `include_substitution` | `(self) -> None` | - |
|   \u2b91 `fortran_args_substitution` | `(self) -> None` | - |
|   \u2b91 `generate_meson_build` | `(self)` | - |
|   \u2b91 `__init__` | `(self, *args, **kwargs)` | - |
|   \u2b91 `write_meson_build` | `(self, build_dir: Path) -> None` | Writes the meson build file at specified location |
|   \u2b91 `run_meson` | `(self, build_dir: Path)` | - |
|   \u2b91 `compile` | `(self) -> None` | - |

---
#### `venv/Lib/site-packages/oauthlib/oauth2/rfc6749/clients/backend_application.py` (75 行)

**类 `BackendApplicationClient`** (继承 `Client`) — 行 13

---
#### `venv/Lib/site-packages/onnxruntime/backend/__init__.py` (7 行)

---
#### `venv/Lib/site-packages/onnxruntime/backend/backend.py` (215 行)

**类 `OnnxRuntimeBackend`** (继承 `Backend`) — 行 44

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `is_compatible` | `(cls, model, device=None, **kwargs)` | Return whether the model is compatible with the backend.  :param model: unused : |
|   \u2b91 `is_opset_supported` | `(cls, model)` | Return whether the opset for the model is supported by the backend. When By defa |
|   \u2b91 `supports_device` | `(cls, device)` | Check whether the backend is compiled with particular device support. In particu |
|   \u2b91 `prepare` | `(cls, model, device=None, **kwargs)` | Load the model and creates an :class:`onnxruntime.backend.backend_rep.OnnxRuntim |
|   \u2b91 `run_model` | `(cls, model, inputs, device=None, **kwargs)` | Compute the prediction.  :param model: the model to run — accepts a file path (s |
|   \u2b91 `run_node` | `(cls, node, inputs, device=None, outputs_info=None, **kwargs)` | This method is not implemented as it is much more efficient to run a whole model |

---
#### `venv/Lib/site-packages/onnxruntime/backend/backend_rep.py` (77 行)

**类 `OnnxRuntimeBackendRep`** (继承 `BackendRep`) — 行 26

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, session)` | :param session: :class:`onnxruntime.InferenceSession` |
|   \u2b91 `run` | `(self, inputs, **kwargs)` | Computes the prediction. See :meth:`onnxruntime.InferenceSession.run`.  :param i |

---
#### `venv/Lib/site-packages/scipy/_lib/_uarray/_backend.py` (708 行)

**类 `Dispatchable`** — 行 412

| 函数 | 签名 | 说明 |
|------|------|------|
| `unpickle_function` | `(mod_name, qname, self_)` | - |
| `pickle_function` | `(func)` | - |
| `pickle_state` | `(state)` | - |
| `pickle_set_backend_context` | `(ctx)` | - |
| `pickle_skip_backend_context` | `(ctx)` | - |
| `get_state` | `()` | Returns an opaque object containing the current state of all the backends.  Can  |
| `reset_state` | `()` | Returns a context manager that resets all state once exited.  See Also --------  |
| `set_state` | `(state)` | A context manager that sets the state of the backends to one returned by :obj:`g |
| `create_multimethod` | `(*args, **kwargs)` | Creates a decorator for generating multimethods.  This function creates a decora |
|   \u2b91 `wrapper` | `(a)` | - |
| `set_backend` | `(backend, coerce=False, only=False)` | A context manager that sets the preferred backend.  Parameters ---------- backen |
| `skip_backend` | `(backend)` | A context manager that allows one to skip a given backend from processing entire |
| `get_defaults` | `(f)` | - |
| `set_global_backend` | `(backend, coerce=False, only=False, *, try_last=False)` | This utility method replaces the default backend for permanent use. It will be t |
| `register_backend` | `(backend)` | This utility method sets registers backend for permanent use. It will be tried i |
| `clear_backends` | `(domain, registered=True, globals=False)` | This utility method clears registered backends.  .. warning:: We caution library |
|   \u2b91 `__init__` | `(self, value, dispatch_type, coercible=True)` | - |
| `mark_as` | `(dispatch_type)` | Creates a utility function to mark something as a specific type.  Examples ----- |
| `all_of_type` | `(arg_type)` | Marks all unmarked arguments as a given type.  Examples -------- >>> @all_of_typ |
|   \u2b91 `outer` | `(func)` | - |
|   \u2b91 `inner` | `(*args, **kwargs)` | - |
| `wrap_single_convertor` | `(convert_single)` | Wraps a ``__ua_convert__`` defined for a single element to all elements. If any  |
| `wrap_single_convertor_instance` | `(convert_single)` | Wraps a ``__ua_convert__`` defined for a single element to all elements. If any  |
| `determine_backend` | `(value, dispatch_type, *, domain, only=True, coerce=False)` | Set the backend to the first active backend that supports ``value``  This is use |

---
#### `venv/Lib/site-packages/scipy/_lib/array_api_extra/_lib/_backends.py` (73 行)

**类 `Backend`** (继承 `Enum`) — 行 16

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `modname` | `(self) -> str` | Module name to be imported. |
|   \u2b91 `like` | `(self, *others: Backend) -> bool` | Check if this backend uses the same module as others. |
|   \u2b91 `pytest_param` | `(self) -> Any` | Backend as a pytest parameter  Returns ------- pytest.mark.ParameterSet |

---
#### `venv/Lib/site-packages/scipy/fft/_backend.py` (202 行)

**类 `_ScipyBackend`** — 行 8

| 函数 | 签名 | 说明 |
|------|------|------|
| `set_global_backend` | `(backend, coerce=False, only=False, try_last=False)` | Sets the global fft backend  This utility method replaces the default backend fo |
| `register_backend` | `(backend)` | Register a backend for permanent use.  Registered backends have the lowest prior |
| `set_backend` | `(backend, coerce=False, only=False)` | Context manager to set the backend within a fixed scope.  Upon entering the ``wi |
| `skip_backend` | `(backend)` | Context manager to skip a backend within a fixed scope.  Within the context of a |

---
#### `venv/Lib/site-packages/scipy/fft/_basic_backend.py` (198 行)

---
#### `venv/Lib/site-packages/scipy/fft/_debug_backends.py` (23 行)

**类 `NumPyBackend`** — 行 3

**类 `EchoBackend`** — 行 16

---
#### `venv/Lib/site-packages/scipy/fft/_fftlog_backend.py` (202 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `fht` | `(a, dln, mu, offset=0.0, bias=0.0)` | - |
| `ifht` | `(A, dln, mu, offset=0.0, bias=0.0)` | - |
| `fhtcoeff` | `(n, dln, mu, offset=0.0, bias=0.0, inverse=False)` | Compute the coefficient array for a fast Hankel transform. |
| `fhtoffset` | `(dln, mu, initial=0.0, bias=0.0)` | Return optimal offset for a fast Hankel transform.  Returns an offset close to ` |

---
#### `venv/Lib/site-packages/scipy/fft/_realtransforms_backend.py` (64 行)

---
#### `venv/Lib/site-packages/scipy/fft/tests/mock_backend.py` (97 行)

**类 `_MockFunction`** — 行 5

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, return_value = None)` | - |

---
#### `venv/Lib/site-packages/scipy/fft/tests/test_backend.py` (99 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `test_backend_call` | `(func, np_func, mock)` | - |
| `test_backend_plan` | `(func, mock)` | - |

---
#### `venv/Lib/site-packages/scipy/ndimage/_support_alternative_backends.py` (121 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `delegate_xp` | `(delegator, module_name)` | - |
|   \u2b91 `inner` | `(func)` | - |
|   \u2b91 `wrapper` | `(*args, **kwds)` | - |

---
#### `venv/Lib/site-packages/scipy/signal/_support_alternative_backends.py` (389 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `delegate_xp` | `(delegator, module_name)` | - |
|   \u2b91 `inner` | `(func)` | - |
|   \u2b91 `wrapper` | `(*args, **kwds)` | - |
| `get_default_capabilities` | `(func_name, delegator)` | - |

---
#### `venv/Lib/site-packages/scipy/special/_support_alternative_backends.py` (877 行)

**类 `_FuncInfo`** — 行 19

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `name` | `(self)` | - |
|   \u2b91 `wrapper` | `(self)` | - |
|   \u2b91 `wrapped` | `(*args, **kwargs)` | - |
|   \u2b91 `f` | `(*args, _f=_f, xp=xp, **kwargs)` | - |
|   \u2b91 `f` | `(*args, _f=_f, xp=xp, **kwargs)` | - |
|   \u2b91 `f` | `(*args, _f=_f, xp=xp, **kwargs)` | - |
|   \u2b91 `fun` | `(t, df, p)` | - |

---
#### `venv/Lib/site-packages/scipy/special/tests/test_support_alternative_backends.py` (403 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `test_support_alternative_backends` | `(xp, func, nfo, base_dtype, shapes)` | - |
| `test_support_alternative_backends_mismatched_dtypes` | `(xp, func, nfo)` | Test mix-n-match of int and float arguments |
| `test_support_alternative_backends_hypothesis` | `(xp, func, nfo, data)` | - |
| `test_pickle` | `(func)` | - |
| `test_repr` | `(func)` | - |
| `test_doc` | `(func)` | xp_capabilities updates the docstring in place. Make sure it does so exactly onc |
| `test_ufunc_kwargs` | `(func, n_args, int_only, is_ufunc)` | Test that numpy-specific out= and dtype= keyword arguments of ufuncs still work  |
| `test_chdtr_gh21311` | `(xp)` | - |

---
#### `venv/Lib/site-packages/sentence_transformers/backend/__init__.py` (19 行)

---
#### `venv/Lib/site-packages/sentence_transformers/backend/load.py` (176 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `load_onnx_model` | `(model_name_or_path: str, config: PretrainedConfig, task_name: str, **model_kwargs)` | Load and perhaps export an ONNX model using the Optimum library.  Args: model_na |
| `load_openvino_model` | `(model_name_or_path: str, config: PretrainedConfig, task_name: str, **model_kwargs)` | Load and perhaps export an OpenVINO model using the Optimum library.  Args: mode |

**关键依赖：**
- `from sentence_transformers.backend.utils import _save_pretrained_wrapper, backend_should_export, backend_warn_to_save`

---
#### `venv/Lib/site-packages/sentence_transformers/backend/optimize.py` (104 行)

**关键依赖：**
- `from sentence_transformers.backend.utils import save_or_push_to_hub_model`
- `from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder`

---
#### `venv/Lib/site-packages/sentence_transformers/backend/quantize.py` (219 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `preprocess_function` | `(examples)` | - |

**关键依赖：**
- `from sentence_transformers.backend.utils import save_or_push_to_hub_model`
- `from sentence_transformers.util import disable_datasets_caching, is_datasets_available`
- `from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder`

---
#### `venv/Lib/site-packages/sentence_transformers/backend/utils.py` (336 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `wrapper` | `(save_directory: str | Path, **kwargs) -> None` | - |
| `backend_warn_to_save` | `(model_name_or_path: str, is_local: bool, backend_name: str) -> None` | Warns the user to save the model if they just exported it.  Args: model_name_or_ |

**关键依赖：**
- `from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder`
- `from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder`
- `from sentence_transformers import SparseEncoder`
- `from sentence_transformers import SentenceTransformer`
- `from sentence_transformers import CrossEncoder`

---
#### `venv/Lib/site-packages/sklearn/externals/array_api_extra/_lib/_backends.py` (73 行)

**类 `Backend`** (继承 `Enum`) — 行 16

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `modname` | `(self) -> str` | Module name to be imported. |
|   \u2b91 `like` | `(self, *others: Backend) -> bool` | Check if this backend uses the same module as others. |
|   \u2b91 `pytest_param` | `(self) -> Any` | Backend as a pytest parameter  Returns ------- pytest.mark.ParameterSet |

---
#### `venv/Lib/site-packages/sympy/core/backend.py` (121 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `sympify` | `(a, *, strict=False)` | Notes =====  SymEngine's ``sympify`` does not accept keyword arguments and is th |

---
#### `venv/Lib/site-packages/sympy/plotting/backends/base_backend.py` (420 行)

**类 `Plot`** — 行 49

| 函数 | 签名 | 说明 |
|------|------|------|
| `unset_show` | `()` | Disable show(). For use in the tests. |
|   \u2b91 `check_and_set` | `(t_name, t)` | - |
|   \u2b91 `backend` | `(self)` | - |
|   \u2b91 `append` | `(self, arg)` | Adds an element from a plot's series to an existing plot.  Examples ========  Co |
|   \u2b91 `extend` | `(self, arg)` | Adds all series from another plot.  Examples ========  Consider two ``Plot`` obj |
|   \u2b91 `show` | `(self)` | - |
|   \u2b91 `save` | `(self, path)` | - |
|   \u2b91 `close` | `(self)` | - |
|   \u2b91 `markers` | `(self)` | .. deprecated:: 1.13 |
|   \u2b91 `markers` | `(self, v)` | .. deprecated:: 1.13 |
|   \u2b91 `annotations` | `(self)` | .. deprecated:: 1.13 |
|   \u2b91 `annotations` | `(self, v)` | .. deprecated:: 1.13 |
|   \u2b91 `rectangles` | `(self)` | .. deprecated:: 1.13 |
|   \u2b91 `rectangles` | `(self, v)` | .. deprecated:: 1.13 |
|   \u2b91 `fill` | `(self)` | .. deprecated:: 1.13 |
|   \u2b91 `fill` | `(self, v)` | .. deprecated:: 1.13 |

---
#### `venv/Lib/site-packages/sympy/plotting/backends/matplotlibbackend/__init__.py` (6 行)

---
#### `venv/Lib/site-packages/sympy/plotting/backends/matplotlibbackend/matplotlib.py` (319 行)

**类 `MatplotlibBackend`** (继承 `base_backend.Plot`) — 行 43

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, *series, **kwargs)` | - |
|   \u2b91 `set_spines` | `(ax)` | - |
|   \u2b91 `get_segments` | `(x, y, z=None)` | Convert two list of coordinates to a list of segments to be used with Matplotlib |
|   \u2b91 `process_series` | `(self)` | Iterates over every ``Plot`` object and further calls _process_series() |
|   \u2b91 `show` | `(self)` | - |
|   \u2b91 `save` | `(self, path)` | - |
|   \u2b91 `close` | `(self)` | - |

---
#### `venv/Lib/site-packages/sympy/plotting/backends/textbackend/__init__.py` (4 行)

---
#### `venv/Lib/site-packages/sympy/plotting/backends/textbackend/text.py` (25 行)

**类 `TextBackend`** (继承 `base_backend.Plot`) — 行 6

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, *args, **kwargs)` | - |
|   \u2b91 `show` | `(self)` | - |
|   \u2b91 `close` | `(self)` | - |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/common.py` (185 行)

**类 `AotAutograd`** — 行 44

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, **kwargs: Any) -> None` | - |
| `aot_autograd` | `(**kwargs: Any) -> AotAutograd` | - |
| `fake_tensor_unsupported` | `(fn: Callable[[Any, list[Any], Any], R]) -> Any` | Decorator for backends that need real inputs.  We swap out fake tensors for zero |
|   \u2b91 `wrapper` | `(model: Any, inputs: Any, **kwargs: Any) -> Any` | - |
| `device_from_inputs` | `(example_inputs: Iterable[Any]) -> torch.device` | - |
| `dtype_from_inputs` | `(example_inputs: Iterable[Any]) -> torch.dtype` | - |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/cudagraphs.py` (300 行)

**类 `CudagraphsBackend`** — 行 239

| 函数 | 签名 | 说明 |
|------|------|------|
| `find_input_mutations` | `(g: torch.fx.Graph) -> set[int]` | - |
|   \u2b91 `meta_fk` | `(meta: dict[str, Any]) -> Any` | - |
| `get_device_index` | `(gm: torch.fx.GraphModule) -> int` | - |
| `cudagraphs` | `(dynamo_model: torch.fx.GraphModule, dynamo_inputs: Sequence[Any]) -> Any` | - |
|   \u2b91 `fn` | `(inputs: list[Any]) -> Any` | - |
|   \u2b91 `reset` | `() -> None` | - |
|   \u2b91 `run` | `(*new_inputs: Any) -> Sequence[Any]` | - |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/debugging.py` (731 行)

**类 `AOTEagerOutputCode`** (继承 `OutputCode`) — 行 266

**类 `ReluCompileError`** (继承 `Exception`) — 行 531

**类 `TestingOnlyCompileError`** (继承 `Exception`) — 行 535

**类 `ExplainOutput`** — 行 592

**类 `ExplainWithBackend`** — 行 678

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `wrapper` | `(*args: Any, **kwargs: Any) -> Any` | - |
|   \u2b91 `inner` | `(*args: Any) -> Any` | - |
|   \u2b91 `runnable_gm` | `(*args: Any) -> Any` | - |
|   \u2b91 `inner` | `(*args: Any) -> Any` | - |
|   \u2b91 `invoke_subgraph_wrapper_unboxed` | `(*operands: Any) -> Any` | - |
|   \u2b91 `invoke_subgraph_wrapper` | `(args: list[Any]) -> Any` | - |
|   \u2b91 `invoke_subgraph_wrapper_unboxed` | `(*args: Any) -> Any` | - |
|   \u2b91 `invoke_subgraph_wrapper` | `(args: list[Any]) -> Any` | - |
|   \u2b91 `prepare_for_serialization` | `(self) -> None` | - |
|   \u2b91 `post_compile` | `(self, *args: Any, **kwargs: Any) -> None` | - |
|   \u2b91 `set_triton_bundle` | `(self, triton_bundle: Any) -> None` | - |
|   \u2b91 `run` | `(args: Any) -> Any` | - |
|   \u2b91 `run` | `(args: Any) -> Any` | - |
|   \u2b91 `run` | `(args: Any) -> Any` | - |
| `ignore_builtins` | `(op: torch._ops.OpOverload) -> bool` | - |
|   \u2b91 `fn` | `(x)` | - |
|   \u2b91 `__init__` | `(self, backend: CompilerFn | str) -> None` | - |
|   \u2b91 `output` | `(self) -> ExplainOutput` | - |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/distributed.py` (623 行)

**类 `Bucket`** — 行 59

**类 `DDPOptimizerContext`** — 行 174

**类 `SubmodCompiler`** (继承 `torch.fx.interpreter.Interpreter`) — 行 181

**类 `WrapperModule`** (继承 `torch.nn.Module`) — 行 206

**类 `FakeifyFirstAOTInvocationGuard`** — 行 310

**类 `DDPOptimizer`** — 行 371

| 函数 | 签名 | 说明 |
|------|------|------|
| `args_str` | `(args: Any) -> str` | - |
| `bucket_has_external_output` | `(bucket: Bucket) -> bool` | - |
| `pretty_print_buckets` | `(buckets: list[Bucket], bucket_bytes_cap: int) -> None` | - |
| `has_higher_order_op` | `(gm: fx.GraphModule) -> bool` | - |
| `propagate_metadata` | `(orig_gm: fx.GraphModule, split_gm: fx.GraphModule) -> None` | - |
| `propagate_dynamo_source` | `(orig_gm: fx.GraphModule, split_gm: fx.GraphModule) -> None` | - |
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `forward` | `(self, *args: Any) -> Any` | - |
|   \u2b91 `run_node` | `(self, n: Node) -> Any` | - |
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `add_param` | `(self, bucket: Bucket, param: torch.nn.Parameter, name: str) -> None` | - |
|   \u2b91 `add_param_args` | `(self, bucket: Bucket, node: fx.Node) -> None` | - |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/inductor.py` (32 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `inductor` | `(*args: Any, **kwargs: Any) -> Any` | - |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/onnxrt.py` (40 行)

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/registry.py` (207 行)

**类 `CompiledFn`** (继承 `Protocol`) — 行 74

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `my_compiler` | `(fx_graph, example_inputs)` | - |
| `my_compiler_function` | `(fx_graph, example_inputs)` | - |
| `lookup_backend` | `(compiler_fn: str | CompilerFn) -> CompilerFn` | Expand backend strings to functions |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/tensorrt.py` (13 行)

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/torchxla.py` (56 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `fwd` | `(*args: torch.Tensor) -> Any` | - |

---
#### `venv/Lib/site-packages/torch/_dynamo/backends/tvm.py` (198 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `to_torch_tensor` | `(nd_tensor: tvm.nd.array) -> torch.Tensor` | A helper function to transfer a NDArray to torch.tensor. |
|   \u2b91 `to_tvm_tensor` | `(torch_tensor: torch.Tensor) -> tvm.nd.array` | A helper function to transfer a torch.tensor to NDArray. |
|   \u2b91 `exec_tvm` | `(*i_args: torch.Tensor) -> list[torch.Tensor]` | - |
| `has_tvm` | `() -> bool` | - |
| `llvm_target` | `() -> str` | - |

---
#### `venv/Lib/site-packages/torch/_lazy/ts_backend.py` (8 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `init` | `()` | Initializes the lazy Torchscript backend |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/__init__.py` (31 行)

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/_common_operator_config_utils.py` (783 行)

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/_qnnpack_pt2e.py` (182 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_linear_configs` | `()` | - |
| `get_conv_configs` | `()` | - |
| `get_pooling_configs` | `()` | - |
|   \u2b91 `root_node_getter` | `(node_pattern)` | - |
| `get_relu_configs` | `()` | - |
| `get_binary_op_configs` | `()` | - |
| `get_qnnpack_pt2e_backend_config` | `()` | - |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/backend_config.py` (752 行)

**类 `ObservationType`** (继承 `Enum`) — 行 55

**类 `DTypeWithConstraints`** — 行 79

**类 `DTypeConfig`** — 行 115

**类 `BackendConfig`** — 行 291

**类 `BackendPatternConfig`** — 行 439

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `from_dict` | `(cls, dtype_config_dict: dict[str, Any]) -> DTypeConfig` | Create a ``DTypeConfig`` from a dictionary with the following items (all optiona |
|   \u2b91 `fuse_conv2d_relu` | `(is_qat, conv, relu)` | - |
|   \u2b91 `__init__` | `(self, name: str = "")` | - |
|   \u2b91 `set_name` | `(self, name: str) -> BackendConfig` | Set the name of the target backend. |
|   \u2b91 `set_backend_pattern_config` | `(self, config: BackendPatternConfig) -> BackendConfig` | Set the config for an pattern that can be run on the target backend. This overri |
|   \u2b91 `configs` | `(self) -> list[BackendPatternConfig]` | Return a copy of the list of configs set in this `BackendConfig`. |
|   \u2b91 `from_dict` | `(cls, backend_config_dict: dict[str, Any]) -> BackendConfig` | Create a ``BackendConfig`` from a dictionary with the following items:  "name":  |
|   \u2b91 `__init__` | `(self, pattern: Pattern | None = None)` | - |
|   \u2b91 `set_pattern` | `(self, pattern: Pattern) -> BackendPatternConfig` | Set the pattern to configure.  The pattern can be a float module, functional ope |
|   \u2b91 `add_dtype_config` | `(self, dtype_config: DTypeConfig) -> BackendPatternConfig` | Add a set of supported data types passed as arguments to quantize ops in the ref |
|   \u2b91 `set_qat_module` | `(self, qat_module: type[torch.nn.Module]) -> BackendPatternConfig` | Set the module that represents the QAT implementation for this pattern. |
|   \u2b91 `set_fuser_method` | `(self, fuser_method: Callable) -> BackendPatternConfig` | Set the function that specifies how to fuse this BackendPatternConfig's pattern. |
|   \u2b91 `fuse_linear_relu` | `(is_qat, linear, relu)` | - |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/executorch.py` (499 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_executorch_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for backends PyTorch lowers to through the Executorch |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/fbgemm.py` (130 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_fbgemm_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for PyTorch's native FBGEMM backend. |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/native.py` (232 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_test_only_legacy_native_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for PyTorch Native backend (fbgemm/qnnpack) with vari |
| `get_native_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for PyTorch Native backend (fbgemm/qnnpack). |
| `get_native_backend_config_dict` | `()` | Return the `BackendConfig` for PyTorch Native backend (fbgemm/qnnpack) in dictio |
| `get_test_only_legacy_native_backend_config_dict` | `()` | Return the `BackendConfig` for PyTorch Native backend (fbgemm/qnnpack) with vari |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/onednn.py` (642 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_onednn_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for PyTorch's native ONEDNN backend. |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/qnnpack.py` (172 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_qnnpack_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for PyTorch's native QNNPACK backend. |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/tensorrt.py` (99 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_tensorrt_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for the TensorRT backend. NOTE: Current api will chan |
| `get_tensorrt_backend_config_dict` | `()` | Return the `BackendConfig` for the TensorRT backend in dictionary form. |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/utils.py` (322 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `get_root_node` | `(node_pattern)` | - |
|   \u2b91 `extra_inputs_getter` | `(pattern) -> List[Any]` | - |
| `remove_boolean_dispatch_from_name` | `(p) -> Any` | Some ops have a default string representation such as '<function boolean_dispatc |
| `pattern_to_human_readable` | `(p) -> Any` | - |
| `entry_to_pretty_str` | `(entry) -> str` | Given a backend_config_dict entry, returns a string with the human readable repr |

---
#### `venv/Lib/site-packages/torch/ao/quantization/backend_config/x86.py` (127 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_x86_backend_config` | `() -> BackendConfig` | Return the `BackendConfig` for PyTorch's native x86 backend. |

---
#### `venv/Lib/site-packages/torch/ao/quantization/fx/_lower_to_native_backend.py` (1414 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_fixed_qparams_node` | `(node, modules)` | - |
| `is_default_node` | `(node, modules)` | - |
| `is_copy_node` | `(node, modules)` | - |
| `is_general_tensor_shape_node` | `(node, modules)` | - |
| `is_other_node` | `(node, modules)` | - |
| `is_special_pattern_node` | `(node, modules)` | - |
| `is_dequantize_node` | `(node)` | - |
| `is_getattr_tensor_metadata_node` | `(node)` | - |
| `is_get_tensor_info_node` | `(node)` | - |
| `should_skip_lowering` | `(op: torch.fx.node.Node, qconfig_map: dict[str, QConfigAny])` | Return True if the op is configured with a None qconfig, False otherwise. Note:  |
|   \u2b91 `load_arg` | `(a)` | - |
| `special_pattern_replacement` | `(model: GraphModule)` | - |

---
#### `venv/Lib/site-packages/torch/backends/__init__.py` (141 行)

**类 `ContextProp`** — 行 36

**类 `PropModule`** (继承 `types.ModuleType`) — 行 54

**类 `_FP32Precision`** — 行 63

**类 `GenericModule`** (继承 `PropModule`) — 行 115

| 函数 | 签名 | 说明 |
|------|------|------|
| `disable_global_flags` | `()` | - |
| `flags_frozen` | `()` | - |
|   \u2b91 `__init__` | `(self, getter, setter)` | - |
|   \u2b91 `__init__` | `(self, m, name)` | - |
|   \u2b91 `__init__` | `(self, backend, op)` | - |
| `set_flags` | `(_fp32_precision="none")` | - |
| `flags` | `(fp32_precision="none")` | - |
|   \u2b91 `inner` | `()` | - |
|   \u2b91 `inner` | `(precision)` | - |

---
#### `venv/Lib/site-packages/torch/backends/_coreml/preprocess.py` (155 行)

**类 `ScalarType`** — 行 17

**类 `CoreMLComputeUnit`** — 行 35

**类 `CoreMLQuantizationMode`** — 行 41

| 函数 | 签名 | 说明 |
|------|------|------|
| `TensorSpec` | `(shape, dtype=ScalarType.Float)` | - |
| `preprocess` | `(script_module: torch._C.ScriptObject, compile_spec: dict[str, tuple])` | - |

---
#### `venv/Lib/site-packages/torch/backends/_nnapi/prepare.py` (209 行)

**类 `NnapiModule`** (继承 `torch.nn.Module`) — 行 15

**类 `NnapiInterfaceWrapper`** (继承 `torch.nn.Module`) — 行 136

**类 `ShapeComputeModule`** (继承 `torch.nn.Module`) — 行 188

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `init` | `(self, args: list[torch.Tensor])` | - |
|   \u2b91 `forward` | `(self, args: list[torch.Tensor]) -> list[torch.Tensor]` | - |
|   \u2b91 `__init__` | `(self, mod)` | - |

---
#### `venv/Lib/site-packages/torch/backends/_nnapi/serializer.py` (2647 行)

**类 `NNAPI_OperandCode`** — 行 21

**类 `NNAPI_OperationCode`** — 行 37

**类 `NNAPI_FuseCode`** — 行 135

**类 `OperandValueSourceType`** — 行 142

**类 `TorchScalarTypes`** (继承 `enum.Enum`) — 行 152

**类 `ConvPoolArgs2d`** (继承 `NamedTuple`) — 行 180

**类 `DimOrder`** (继承 `enum.Enum`) — 行 196

**类 `Operand`** (继承 `NamedTuple`) — 行 203

**类 `_NnapiSerializer`** — 行 332

| 函数 | 签名 | 说明 |
|------|------|------|
| `approx_equal` | `(lhs, rhs, tolerance=1e-6)` | - |
| `tensor_size` | `(op_type, dims)` | - |
| `change_element` | `(tup, index, value)` | - |
|   \u2b91 `use_nchw` | `(self)` | - |
| `broadcast_shapes` | `(shape1, shape2)` | - |
| `get_conv_pool_shape` | `(image_shape, args, out_ch, transpose)` | - |
| `fix_shape` | `(shape, dim_order)` | - |
| `reverse_map_dim` | `(dim_order, d)` | - |
| `flex_name` | `(op_id, dim)` | - |
|   \u2b91 `__init__` | `(self, config, use_int16_for_qint16=False)` | - |
|   \u2b91 `get_next_operand_id` | `(self)` | - |
|   \u2b91 `add_tensor_operand` | `(self, jitval, oper)` | - |
|   \u2b91 `add_anonymous_tensor_operand` | `(self, oper)` | - |
|   \u2b91 `torch_tensor_to_operand` | `(self, tensor, dim_order)` | - |
|   \u2b91 `add_tensor_operand_for_input` | `(self, arg_idx, jitval, tensor)` | - |
|   \u2b91 `add_immediate_operand` | `(self, code, value, dims)` | - |
|   \u2b91 `add_immediate_int_scalar` | `(self, value)` | - |
|   \u2b91 `add_immediate_float_scalar` | `(self, value)` | - |
|   \u2b91 `add_immediate_bool_scalar` | `(self, value)` | - |
|   \u2b91 `add_immediate_int_vector` | `(self, value)` | - |
|   \u2b91 `has_operand_for_jitval` | `(self, jitval)` | - |
|   \u2b91 `get_tensor_operand_by_jitval` | `(self, jitval)` | - |
|   \u2b91 `get_tensor_operand_by_jitval_fixed_size` | `(self, jitval)` | - |
|   \u2b91 `get_tensor_operand_for_weight` | `(self, jitval)` | - |
|   \u2b91 `add_operation` | `(self, opcode, inputs, outputs)` | - |
|   \u2b91 `add_tensor_sequence` | `(self, jitval, values)` | - |
|   \u2b91 `add_constant_value` | `(self, jitval, ctype, value)` | - |
|   \u2b91 `get_constant_value` | `(self, jitval, typekind=None)` | - |
|   \u2b91 `operand_to_template_torchscript` | `(self, op_id, oper, shape=None)` | Return a TorchScript expression to build a template for a given operand. |
|   \u2b91 `forward_operand_shape` | `(self, out_op_id, out_dim, in_op_id, in_dim)` | - |
|   \u2b91 `compute_operand_shape` | `(self, op_id, dim, expr)` | - |
|   \u2b91 `transpose_to_nhwc` | `(self, in_id, oper)` | - |
|   \u2b91 `transpose_for_broadcast` | `(self, in0_id, in0_oper, in1_id, in1_oper)` | - |
|   \u2b91 `get_size_arg` | `(self, jitval)` | - |
|   \u2b91 `get_conv_pool_args_2d_from_pack` | `(self, kernel_size, packed_config)` | - |
|   \u2b91 `serialize_model` | `(self, model, inputs, return_shapes=None)` | - |
|   \u2b91 `serialize_values` | `(self)` | - |
|   \u2b91 `serialize_ints` | `(ints)` | - |
|   \u2b91 `add_node` | `(self, node)` | - |
|   \u2b91 `add_getattr` | `(self, node)` | - |
|   \u2b91 `add_constant_node` | `(self, node)` | - |
|   \u2b91 `add_list_construct` | `(self, node)` | - |
|   \u2b91 `add_tuple_construct` | `(self, node)` | - |
|   \u2b91 `add_unsqueeze` | `(self, node)` | - |
|   \u2b91 `add_to` | `(self, node)` | - |
|   \u2b91 `add_reshape` | `(self, node)` | - |
|   \u2b91 `add_flatten` | `(self, node)` | - |
|   \u2b91 `add_slice` | `(self, node)` | - |
|   \u2b91 `add_size` | `(self, node)` | - |
|   \u2b91 `add_cat` | `(self, node)` | - |
|   \u2b91 `add_mean` | `(self, node)` | - |
|   \u2b91 `add_quantize` | `(self, node)` | - |
|   \u2b91 `add_dequantize` | `(self, node)` | - |
|   \u2b91 `add_pointwise_simple_unary_op` | `(self, node, opcode)` | - |
|   \u2b91 `add_pointwise_simple_binary_broadcast_op` | `(self, node, opcode, fuse_code)` | - |
|   \u2b91 `add_add_sub_op` | `(self, node, opcode, fuse_code)` | - |
|   \u2b91 `add_qadd` | `(self, node, opcode, fuse_code)` | - |
|   \u2b91 `add_softmax` | `(self, node)` | - |
|   \u2b91 `add_hardtanh` | `(self, node)` | - |
|   \u2b91 `add_prelu_op` | `(self, node)` | - |
|   \u2b91 `add_pool2d_node` | `(self, node, opcode)` | - |
|   \u2b91 `add_avg_pool2d` | `(self, node)` | - |
|   \u2b91 `add_adaptive_avg_pool2d` | `(self, node)` | - |
|   \u2b91 `add_upsample_nearest2d` | `(self, node)` | - |
|   \u2b91 `add_addmm` | `(self, node)` | - |
|   \u2b91 `add_linear` | `(self, node)` | - |
|   \u2b91 `add_qlinear` | `(self, node)` | - |
|   \u2b91 `get_optional_bias` | `(self, jit_bias, weight_tensor, transpose=False)` | - |
|   \u2b91 `add_conv2d` | `(self, node)` | - |
|   \u2b91 `add_conv_underscore` | `(self, node)` | - |
|   \u2b91 `add_log_softmax` | `(self, node)` | - |
|   \u2b91 `add_qconv2d` | `(self, node, fuse_code, transpose=False)` | - |

---
#### `venv/Lib/site-packages/torch/backends/cpu/__init__.py` (22 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_cpu_capability` | `() -> str` | - |

---
#### `venv/Lib/site-packages/torch/backends/cuda/__init__.py` (606 行)

**类 `cuFFTPlanCacheAttrContextProp`** — 行 50

**类 `cuFFTPlanCache`** — 行 66

**类 `cuFFTPlanCacheManager`** — 行 91

**类 `cuBLASModule`** — 行 129

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_built` | `()` | - |
|   \u2b91 `__init__` | `(self, getter, setter)` | - |
|   \u2b91 `__init__` | `(self, device_index)` | - |
|   \u2b91 `clear` | `(self)` | - |
|   \u2b91 `__init__` | `(self)` | - |
| `is_ck_sdpa_available` | `() -> bool` | - |
| `flash_sdp_enabled` | `()` | - |
| `enable_flash_sdp` | `(enabled: bool)` | - |
| `mem_efficient_sdp_enabled` | `()` | - |
| `enable_mem_efficient_sdp` | `(enabled: bool)` | - |
| `math_sdp_enabled` | `()` | - |
| `enable_math_sdp` | `(enabled: bool)` | - |
| `allow_fp16_bf16_reduction_math_sdp` | `(enabled: bool)` | - |
| `fp16_bf16_reduction_math_sdp_allowed` | `()` | - |
| `is_flash_attention_available` | `() -> bool` | - |
| `can_use_flash_attention` | `(params: SDPAParams, debug: bool = False) -> bool` | - |
| `can_use_efficient_attention` | `(params: SDPAParams, debug: bool = False) -> bool` | - |
| `can_use_cudnn_attention` | `(params: SDPAParams, debug: bool = False) -> bool` | - |
| `cudnn_sdp_enabled` | `()` | - |
| `enable_cudnn_sdp` | `(enabled: bool)` | - |

---
#### `venv/Lib/site-packages/torch/backends/cudnn/__init__.py` (251 行)

**类 `CudnnModule`** (继承 `PropModule`) — 行 216

| 函数 | 签名 | 说明 |
|------|------|------|
| `version` | `()` | Return the version of cuDNN. |
| `is_available` | `()` | - |
| `is_acceptable` | `(tensor)` | - |

---
#### `venv/Lib/site-packages/torch/backends/cudnn/rnn.py` (129 行)

**类 `Unserializable`** — 行 41

**类 `ContextProp`** — 行 57

**类 `CudnnRNNModule`** (继承 `PropModule`) — 行 92

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_cudnn_mode` | `(mode)` | - |
|   \u2b91 `__init__` | `(self, inner)` | - |
|   \u2b91 `get` | `(self)` | - |
|   \u2b91 `__init__` | `(self, getter, setter)` | - |
| `init_dropout_state` | `(dropout, train, dropout_seed, dropout_state)` | - |
|   \u2b91 `__init__` | `(self, m, name)` | - |
|   \u2b91 `init_dropout_state` | `(dropout, train, dropout_seed, dropout_state)` | - |

---
#### `venv/Lib/site-packages/torch/backends/cusparselt/__init__.py` (58 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_available` | `() -> bool` | - |

---
#### `venv/Lib/site-packages/torch/backends/kleidiai/__init__.py` (8 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_available` | `()` | - |

---
#### `venv/Lib/site-packages/torch/backends/mha/__init__.py` (26 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_fastpath_enabled` | `() -> bool` | Returns whether fast path for TransformerEncoder and MultiHeadAttention is enabl |
| `set_fastpath_enabled` | `(value: bool) -> None` | Sets whether fast path is enabled |

---
#### `venv/Lib/site-packages/torch/backends/miopen/__init__.py` (51 行)

**类 `MiopenModule`** (继承 `PropModule`) — 行 39

---
#### `venv/Lib/site-packages/torch/backends/mkl/__init__.py` (60 行)

**类 `verbose`** — 行 14

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_available` | `()` | - |
|   \u2b91 `__init__` | `(self, enable)` | - |

---
#### `venv/Lib/site-packages/torch/backends/mkldnn/__init__.py` (140 行)

**类 `verbose`** — 行 33

**类 `MkldnnModule`** (继承 `PropModule`) — 行 113

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_available` | `()` | - |
| `is_acl_available` | `()` | - |
|   \u2b91 `__init__` | `(self, level)` | - |
| `flags` | `(enabled=False, deterministic=False, allow_tf32=True, fp32_precision="none")` | - |
|   \u2b91 `is_available` | `(self)` | - |

---
#### `venv/Lib/site-packages/torch/backends/mps/__init__.py` (79 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_built` | `() -> bool` | - |
| `is_available` | `() -> bool` | - |
| `is_macos_or_newer` | `(major: int, minor: int) -> bool` | - |
| `is_macos13_or_newer` | `(minor: int = 0) -> bool` | - |
| `get_name` | `() -> str` | - |
| `get_core_count` | `() -> int` | - |

---
#### `venv/Lib/site-packages/torch/backends/nnpack/__init__.py` (33 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_available` | `()` | - |
| `set_flags` | `(_enabled)` | - |
| `flags` | `(enabled=False)` | - |

---
#### `venv/Lib/site-packages/torch/backends/openmp/__init__.py` (8 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_available` | `()` | - |

---
#### `venv/Lib/site-packages/torch/backends/opt_einsum/__init__.py` (118 行)

**类 `OptEinsumModule`** (继承 `PropModule`) — 行 103

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_available` | `() -> bool` | - |
| `get_opt_einsum` | `() -> Any` | - |
| `set_flags` | `(_enabled=None, _strategy=None)` | - |
| `flags` | `(enabled=None, strategy=None)` | - |

---
#### `venv/Lib/site-packages/torch/backends/python_native/__init__.py` (388 行)

**类 `DSLController`** — 行 118

**类 `PythonNativeModule`** (继承 `PropModule`) — 行 186

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, dsl_name: str)` | - |
|   \u2b91 `name` | `(self) -> str` | - |
|   \u2b91 `available` | `(self) -> bool` | Check if DSL runtime is available. |
|   \u2b91 `version` | `(self)` | Get DSL version. |
|   \u2b91 `enabled` | `(self) -> bool` | Check if DSL is currently enabled. |
|   \u2b91 `enabled` | `(self, value: bool)` | Enable or disable the DSL. |
|   \u2b91 `disable` | `(self)` | Disable all operations for this DSL. |
|   \u2b91 `enable` | `(self)` | Re-enable all operations for this DSL. |
|   \u2b91 `disabled` | `(self)` | Context manager to temporarily disable DSL. |
|   \u2b91 `__init__` | `(self, original_module)` | - |
|   \u2b91 `available_dsls` | `(self) -> list[str]` | Get list of available DSLs. |
|   \u2b91 `all_dsls` | `(self) -> list[str]` | Get list of all registered DSLs. |
|   \u2b91 `get_dsl_operations` | `(self, dsl_name: str) -> list[str]` | Get list of operations registered by a specific DSL.  Args: dsl_name (str): Name |
|   \u2b91 `disable_operations` | `(self, *op_symbols: str)` | Disable specific operations across all DSLs.  Args: *op_symbols (str): Names of  |
|   \u2b91 `enable_operations` | `(self, *op_symbols: str)` | Re-enable specific operations across all DSLs.  Args: *op_symbols (str): Names o |
|   \u2b91 `disable_dispatch_keys` | `(self, *dispatch_keys: str)` | Disable operations at specific dispatch keys.  Args: *dispatch_keys (str): Dispa |
|   \u2b91 `enable_dispatch_keys` | `(self, *dispatch_keys: str)` | Re-enable operations at specific dispatch keys.  Args: *dispatch_keys (str): Dis |
|   \u2b91 `operations_disabled` | `(self, *op_symbols: str)` | Context manager to temporarily disable operations.  Args: *op_symbols (str): Nam |
|   \u2b91 `is_operation_disabled` | `(self, op_symbol: str) -> bool` | Check if an operation is currently disabled. |
|   \u2b91 `is_dsl_disabled` | `(self, dsl_name: str) -> bool` | Check if a DSL is currently disabled. |

---
#### `venv/Lib/site-packages/torch/backends/quantized/__init__.py` (66 行)

**类 `_QEngineProp`** — 行 32

**类 `_SupportedQEnginesProp`** — 行 40

**类 `QuantizedEngine`** (继承 `types.ModuleType`) — 行 49

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, m, name)` | - |

---
#### `venv/Lib/site-packages/torch/backends/xeon/run_cpu.py` (958 行)

**类 `_CPUinfo`** — 行 148

**类 `_Launcher`** — 行 262

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, test_input="")` | - |
|   \u2b91 `get_node_physical_cores` | `(self, node_id)` | - |
|   \u2b91 `get_node_logical_cores` | `(self, node_id)` | - |
|   \u2b91 `get_all_physical_cores` | `(self)` | - |
|   \u2b91 `get_all_logical_cores` | `(self)` | - |
|   \u2b91 `numa_aware_check` | `(self, core_list)` | Check whether all cores in core_list are in the same NUMA node.  Cross NUMA will |
|   \u2b91 `__init__` | `(self) -> None` | - |
|   \u2b91 `add_lib_preload` | `(self, lib_type)` | Enable TCMalloc/JeMalloc/intel OpenMP. |
|   \u2b91 `is_numactl_available` | `(self)` | - |
|   \u2b91 `log_env_var` | `(self, env_var_name="")` | - |
|   \u2b91 `set_env` | `(self, env_name, env_value)` | - |
|   \u2b91 `launch` | `(self, args)` | - |
| `create_args` | `(parser=None)` | Parse the command line options.  @retval ArgumentParser |
| `main` | `(args)` | - |

---
#### `venv/Lib/site-packages/torch/backends/xnnpack/__init__.py` (30 行)

**类 `_XNNPACKEnabled`** — 行 8

**类 `XNNPACKEngine`** (继承 `types.ModuleType`) — 行 16

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, m, name)` | - |

---
#### `venv/Lib/site-packages/torch/distributed/elastic/rendezvous/c10d_rendezvous_backend.py` (271 行)

**类 `C10dRendezvousBackend`** (继承 `RendezvousBackend`) — 行 35

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, store: Store, run_id: str) -> None` | - |
|   \u2b91 `name` | `(self) -> str` | See base class. |

---
#### `venv/Lib/site-packages/torch/distributed/elastic/rendezvous/etcd_rendezvous_backend.py` (215 行)

**类 `EtcdRendezvousBackend`** (继承 `RendezvousBackend`) — 行 28

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `name` | `(self) -> str` | See base class. |
|   \u2b91 `get_state` | `()` | - |

---
#### `venv/Lib/site-packages/torch/distributed/rpc/_testing/faulty_agent_backend_registry.py` (63 行)

---
#### `venv/Lib/site-packages/torch/distributed/rpc/backend_registry.py` (433 行)

| 函数 | 签名 | 说明 |
|------|------|------|
| `backend_registered` | `(backend_name)` | Checks if backend_name is registered as an RPC backend.  Args: backend_name (str |
| `init_backend` | `(backend, *args, **kwargs)` | - |

---
#### `venv/Lib/site-packages/torch/fx/passes/backends/cudagraphs.py` (62 行)

**类 `CudaGraphsSupport`** (继承 `OperatorSupport`) — 行 12

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `is_node_supported` | `(self, submodules, node: torch.fx.Node) -> bool` | - |
|   \u2b91 `meta_fk` | `(meta)` | - |
|   \u2b91 `find_not_cuda` | `(t)` | - |
| `partition_cudagraphs` | `(gm, inputs)` | Partition an FX graph into sub-GraphModules that can be validly run under CUDA g |

---
#### `venv/Lib/site-packages/torch/nativert/backends/_lower_utils.py` (105 行)

**类 `FlattenedModule`** (继承 `torch.nn.Module`) — 行 13

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_new_ep_with_flat_inputs_outputs` | `(ep: ExportedProgram) -> ExportedProgram` | - |
|   \u2b91 `forward` | `(self, *flat_inputs)` | - |
|   \u2b91 `patched_forward` | `(self, *args, **kwargs)` | - |

---
#### `venv/Lib/site-packages/torch/nativert/backends/_lowered_aoti_module.py` (32 行)

**类 `LoweredBackendModule`** (继承 `torch.nn.Module`) — 行 5

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `backend_id` | `(self) -> str` | - |
|   \u2b91 `original_module` | `(self) -> ExportedProgram` | - |
|   \u2b91 `forward` | `(self, *args, **kwargs)` | - |

---
#### `venv/Lib/site-packages/torch/nn/backends/thnn.py` (7 行)

---
#### `venv/Lib/site-packages/torch/utils/backend_registration.py` (521 行)

**类 `DummyfooModule`** — 行 416

**类 `_DummyBackendModule`** — 行 448

**类 `_DummyPrivateUse1Hook`** (继承 `torch._C._acc.PrivateUse1Hooks`) — 行 468

**类 `_DummyDeviceGuard`** (继承 `torch._C._acc.DeviceGuard`) — 行 479

| 函数 | 签名 | 说明 |
|------|------|------|
| `rename_privateuse1_backend` | `(backend_name: str) -> None` | - |
|   \u2b91 `wrap_tensor_backend` | `(self: torch.Tensor) -> bool` | - |
|   \u2b91 `wrap_tensor_backend` | `(self: torch.nn.utils.rnn.PackedSequence) -> bool` | - |
|   \u2b91 `wrap_storage_backend` | `(self: torch.storage._StorageBase) -> bool` | - |
|   \u2b91 `wrap_storage_to` | `(self, device=None, non_blocking=False)` | - |
|   \u2b91 `wrap_typed_storage_backend` | `(self: torch.storage.TypedStorage) -> bool` | - |
|   \u2b91 `is_available` | `()` | - |
|   \u2b91 `func_name` | `(*args, **kwargs)` | - |
|   \u2b91 `is_initialized` | `(self) -> bool` | - |
|   \u2b91 `is_available` | `(self) -> bool` | - |
|   \u2b91 `current_device` | `(self) -> int` | - |
|   \u2b91 `manual_seed_all` | `(self, seed: int) -> None` | - |
|   \u2b91 `device_count` | `(self) -> int` | - |
|   \u2b91 `is_available` | `(self) -> bool` | - |
|   \u2b91 `has_primary_context` | `(self, dev_id) -> bool` | - |
|   \u2b91 `is_built` | `(self) -> bool` | - |
|   \u2b91 `type_` | `(self)` | - |

---
#### `venv/Lib/site-packages/torchgen/gen_backend_stubs.py` (636 行)

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `create_decl` | `(f: NativeFunction) -> str` | - |
| `main` | `() -> None` | - |
|   \u2b91 `make_file_manager` | `(install_dir: str) -> FileManager` | - |

---
#### `venv/Lib/site-packages/transformers/image_processing_backends.py` (690 行)

**类 `TorchvisionBackend`** (继承 `BaseImageProcessor`) — 行 86

**类 `PilBackend`** (继承 `BaseImageProcessor`) — 行 428

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, **kwargs: Unpack[ImagesKwargs])` | - |
|   \u2b91 `is_fast` | `(self) -> bool` | `bool`: Whether or not this image processor is using the fast (Torchvision) back |
|   \u2b91 `backend` | `(self) -> str` | `str`: The backend used by this image processor. |
|   \u2b91 `fetch_images` | `(self, image_url_or_urls: str | list[str] | list[list[str]])` | Convert a single or a list of URLs / paths into `torch.Tensor` objects.  Already |
|   \u2b91 `convert_to_rgb` | `(self, image: ImageInput) -> ImageInput` | Convert an image to RGB format. |
|   \u2b91 `__init__` | `(self, **kwargs: Unpack[ImagesKwargs])` | - |
|   \u2b91 `is_fast` | `(self) -> bool` | `bool`: Whether or not this image processor is using the fast (Torchvision) back |
|   \u2b91 `backend` | `(self) -> str` | `str`: The backend used by this image processor. |
|   \u2b91 `convert_to_rgb` | `(self, image: ImageInput) -> ImageInput` | Convert an image to RGB format. |

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
|   \u2b91 `decorator` | `(fn)` | - |
| `can_handle` | `(ext: str) -> bool` | - |
| `process_bytes` | `(data: bytes, ext: str) -> str` | 二进制入口（PDF 等），按扩展名分发 |
| `sha256` | `(text: str) -> str` | - |
| `is_duplicate` | `(content_hash: str) -> bool` | 检查内容哈希是否已存在于数据库 |

**关键依赖：**
- `from database import get_db`

---
#### `backend/processing/vector_store.py` (303 行)

**类 `VectorStore`** — 行 23

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self)` | - |
|   \u2b91 `embed_fn` | `(self)` | - |
|   \u2b91 `add_document` | `(self, doc_id: int, title: str, chunks: list[str], category: str = "", tags: str = "")` | - |
|   \u2b91 `query` | `(self, question: str, top_k: int = 5, category: str = "") -> list[dict]` | - |
|   \u2b91 `count` | `(self) -> int` | - |
|   \u2b91 `index_wiki_page` | `(self, page_id: int, title: str, content: str, category: str = "", tags: str = "")` | 将 Wiki 页面全文嵌入后存入向量库 |
|   \u2b91 `remove_wiki_page` | `(self, page_id: int)` | 从向量库中删除指定 Wiki 页面 |
|   \u2b91 `search_wiki` | `(self, query: str, top_k: int = 10) -> list[dict]` | 语义搜索 Wiki 页面 |
|   \u2b91 `unified_search` | `(self, query: str, top_k: int = 5) -> list[dict]` | 统一搜索：同时查 memories + documents + wiki_pages，RRF 融合排序 |
|   \u2b91 `get_embedding_status` | `(self) -> dict` | 返回各 collection 的 embedding 状态 |
| `get_vector_store` | `() -> VectorStore` | - |

**关键依赖：**
- `import chromadb`
- `from chromadb.config import Settings`
- `from sentence_transformers import SentenceTransformer`
- `from sentence_transformers import SentenceTransformer`
- `from ai_client import ai_client`
- `from ai_client import ai_client`

---
## 后端端点层 (endpoints/)

#### `backend/endpoints/admin.py` (217 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/stats` | `admin_stats()` |  |
| GET | `/logs` | `admin_logs()` | lines |
| GET | `/documents/recent` | `recent_documents()` | limit |
| GET | `/system/info` | `system_info()` |  |
| GET | `/monitored-urls` | `list_monitored_urls()` |  |
| POST | `/monitored-urls` | `add_monitored_url()` | payload |
| DELETE | `/monitored-urls/{url_id}` | `delete_monitored_url()` | url_id |
| POST | `/monitored-urls/check` | `check_monitored_urls()` |  |
| GET | `/monitored-urls/changes` | `get_url_changes()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `admin_stats` | `()` | 返回系统核心统计数字 |
| `admin_logs` | `(lines: int = 100)` | 返回后端日志最后 N 行 |
| `recent_documents` | `(limit: int = 20)` | 返回最近上传的文档列表（带预览） |
| `system_info` | `()` | 返回运行环境信息 |
| `list_monitored_urls` | `()` | 列出所有监控的 URL |
| `add_monitored_url` | `(payload: dict)` | 添加监控 URL |
| `delete_monitored_url` | `(url_id: int)` | 删除监控 URL |
| `check_monitored_urls` | `()` | 手动触发所有 URL 的变更检查。 生产环境应在 main.py lifespan 中设置定时任务每 6 小时调用一次。 |
| `get_url_changes` | `()` | 获取有变更的 URL 列表 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from fastapi.responses import JSONResponse`
- `from database import get_db`

---
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
#### `backend/endpoints/automation.py` (1884 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/automation/modules` | `list_modules()` |  |
| POST | `/automation/run` | `run_automation()` | payload |
| POST | `/automation/queue` | `queue_tasks()` | payload |
| GET | `/automation/queue/status` | `queue_status()` |  |
| GET | `/automation/queue/{task_id}` | `task_status()` | task_id |
| POST | `/automation/queue/retry/{task_id}` | `retry_task()` | task_id |
| DELETE | `/automation/queue/clear` | `clear_completed()` |  |
| POST | `/automation/reparse/{doc_id}` | `reparse_document()` | doc_id |
| GET | `/automation/reparseable` | `list_reparseable()` |  |
| POST | `/documents/cleanup` | `cleanup_documents()` | payload |
| POST | `/automation/extract-webpage` | `extract_webpage()` | payload |

**类 `TextExtractor`** (继承 `HTMLParser`) — 行 1827

| 函数 | 签名 | 说明 |
|------|------|------|
| `verify_external_deps` | `() -> dict` | 启动时校验外部依赖（ffmpeg / claude 等），返回状态报告。  调用方（如 main.py lifespan）应在启动时调用此函数并将结果打印到日志 |
| `recover_orphan_summaries` | `() -> dict` | 启动时扫描摘要目录，把有 .md 文件但未入库的自动导入。  扫描 douyin-summaries/, bilibili-summaries/, xiaoho |
| `recover_tasks_on_startup` | `()` | 启动时恢复未完成的任务 + 孤儿 .md 文件。  在 main.py 的 lifespan 中调用。 |
| `list_modules` | `()` | - |
| `run_automation` | `(payload: dict)` | 同步执行（保持向后兼容）—— 单任务阻塞等待。 |
| `queue_tasks` | `(payload: dict)` | 批量提交任务，立即返回任务 ID 列表。支持多个链接（\\n 分隔或数组）。 |
| `queue_status` | `()` | 获取所有任务状态（最近 50 个）。 |
| `task_status` | `(task_id: str)` | 查询单个任务状态。 |
| `retry_task` | `(task_id: str)` | 重新执行失败的任务（主要用于 API Key 更新后重试）。 如果任务是 API Key 错误导致的失败，会先检查 Key 是否已更新。 |
| `clear_completed` | `()` | 清除已完成和失败的任务（内存 + DB）。 |
| `reparse_document` | `(doc_id: int)` | 重新解析失败的摘要文档（支持抖音/B站/小红书）。 提取原始链接 → 删除旧文档 → 重新提交自动化任务。 |
| `list_reparseable` | `()` | 列出可以重新解析的文档（ASR 失败或内容不完整）。 |
| `cleanup_documents` | `(payload: dict = None)` | 批量清理测试文档、重复文档、无意义短文档。 支持模式： - test: 标题含 test/测试 的文档 - short: 少于 50 字的文档 - duplic |
| `extract_webpage` | `(payload: dict)` | 通用网页正文提取 — 使用 Jina Reader API 作为首选，fallback 到简单抓取。 输入: {"url": "https://example. |
|   \u2b91 `__init__` | `(self)` | - |
|   \u2b91 `handle_starttag` | `(self, tag, attrs)` | - |
|   \u2b91 `handle_endtag` | `(self, tag)` | - |
|   \u2b91 `handle_data` | `(self, data)` | - |

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
|   \u2b91 `clean_opt` | `(s)` | - |
| `brainstorm_step2` | `(payload: dict)` | Iterative question phase. Returns next question + options. |
| `brainstorm_step3` | `(payload: dict)` | Final output generation phase. |

**关键依赖：**
- `from fastapi import APIRouter`
- `from ai_client import ai_client`

---
#### `backend/endpoints/categories.py` (247 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/categories` | `list_categories()` |  |
| POST | `/categories` | `create_category()` | payload |
| PUT | `/categories/{cat_id}` | `update_category()` | cat_id, payload |
| DELETE | `/categories/{cat_id}` | `delete_category()` | cat_id |
| PUT | `/documents/{doc_id}/move` | `move_document()` | doc_id, payload |
| PUT | `/documents/batch-move` | `batch_move_documents()` | payload |
| PUT | `/documents/{doc_id}/tags` | `update_document_tags()` | doc_id, payload |
| POST | `/documents/{doc_id}/auto-tags` | `auto_tag_document()` | doc_id |

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_categories` | `()` | - |
| `create_category` | `(payload: dict)` | - |
| `update_category` | `(cat_id: int, payload: dict)` | - |
| `delete_category` | `(cat_id: int)` | - |
| `move_document` | `(doc_id: int, payload: dict)` | 移动文档到指定分类，同时更新向量库 metadata |
| `batch_move_documents` | `(payload: dict)` | 批量移动文档到指定分类 |
| `update_document_tags` | `(doc_id: int, payload: dict)` | 更新文档标签 |
| `auto_tag_document` | `(doc_id: int)` | AI 自动识别文档标签 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`
- `from ai_client import ai_client`

---
#### `backend/endpoints/creator.py` (117 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/services` | `list_services()` |  |
| GET | `/services/{service_id}` | `get_service_status()` | service_id |

**类 `ServiceStatus`** (继承 `BaseModel`) — 行 31

**类 `ServiceListResponse`** (继承 `BaseModel`) — 行 41

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_services` | `() -> ServiceListResponse` | 获取所有自托管服务的状态列表  通过 TCP 端口检测判断服务是否在线， 并发检测所有服务以提高响应速度。 |
| `get_service_status` | `(service_id: str) -> ServiceStatus` | 获取单个服务的详细状态 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from fastapi import HTTPException`

---
#### `backend/endpoints/ddl.py` (199 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/ddl/tasks` | `list_tasks()` | status, task_type, project_id, plan_date, plan_type |
| POST | `/ddl/tasks` | `create_task()` | payload |
| PUT | `/ddl/tasks/{task_id}` | `update_task()` | task_id, payload |
| DELETE | `/ddl/tasks/{task_id}` | `delete_task()` | task_id |
| PUT | `/ddl/tasks/reorder` | `reorder_tasks()` | payload |
| GET | `/ddl/stats` | `ddl_stats()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_tasks` | `(status: str = "", task_type: str = "", project_id: int = 0, plan_date: str = "", plan_type: str = "")` | 列出 DDL 任务，支持按状态、类型、项目、计划日期筛选 |
| `create_task` | `(payload: dict)` | 创建 DDL 任务 |
| `update_task` | `(task_id: int, payload: dict)` | 更新 DDL 任务 |
| `delete_task` | `(task_id: int)` | 删除 DDL 任务 |
| `reorder_tasks` | `(payload: dict)` | 批量更新排序 (拖拽后的顺序) |
| `ddl_stats` | `()` | DDL 统计信息 |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`

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
#### `backend/endpoints/images.py` (110 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/images/generate-cover` | `generate_cover()` | req |

**类 `GenerateCoverRequest`** (继承 `BaseModel`) — 行 18

| 函数 | 签名 | 说明 |
|------|------|------|
| `generate_cover` | `(req: GenerateCoverRequest)` | - |

**关键依赖：**
- `from fastapi import APIRouter`
- `import httpx`
- `from database import get_db`

---
#### `backend/endpoints/journal.py` (210 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/journal/entries` | `list_entries()` | year, month, tag, mood |
| GET | `/journal/entries/{entry_id}` | `get_entry()` | entry_id |
| GET | `/journal/today` | `get_today()` |  |
| POST | `/journal/entries` | `create_entry()` | payload |
| PUT | `/journal/entries/{entry_id}` | `update_entry()` | entry_id, payload |
| DELETE | `/journal/entries/{entry_id}` | `delete_entry()` | entry_id |
| GET | `/journal/stats` | `get_stats()` |  |
| GET | `/journal/tags` | `list_tags()` |  |

**类 `JournalEntryCreate`** (继承 `BaseModel`) — 行 15

**类 `JournalEntryUpdate`** (继承 `BaseModel`) — 行 25

**类 `JournalEntryOut`** (继承 `BaseModel`) — 行 34

**类 `Config`** — 行 46

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_entries` | `(year: int = 0, month: int = 0, tag: str = "", mood: str = "")` | - |
| `get_entry` | `(entry_id: int)` | - |
| `get_today` | `()` | - |
| `create_entry` | `(payload: JournalEntryCreate)` | - |
| `update_entry` | `(entry_id: int, payload: JournalEntryUpdate)` | - |
| `delete_entry` | `(entry_id: int)` | - |
| `get_stats` | `()` | - |
| `list_tags` | `()` | - |

**关键依赖：**
- `from fastapi import APIRouter`
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
#### `backend/endpoints/operations.py` (1387 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/topics` | `create_topic()` | req |
| GET | `/topics` | `list_topics()` | limit, unused_only |
| POST | `/topics/ai-discover` | `ai_discover_topics()` | keyword, count |
| POST | `/accounts` | `add_account()` | req |
| GET | `/accounts` | `list_accounts()` | platform |
| POST | `/projects` | `create_project()` | req |
| GET | `/projects` | `list_projects()` | status, platform, limit |
| GET | `/projects/{project_id}` | `get_project()` | project_id |
| POST | `/projects/{project_id}/status` | `update_project_status()` | project_id, status |
| POST | `/projects/{project_id}/script/generate` | `generate_script()` | project_id, req |
| POST | `/projects/{project_id}/script/update` | `update_script()` | project_id, req |
| POST | `/projects/{project_id}/script/polish` | `polish_script()` | project_id, style |
| POST | `/projects/{project_id}/video/editing-plan` | `generate_editing_plan()` | project_id |
| POST | `/projects/{project_id}/video/upload` | `upload_video_path()` | project_id, video_path |
| POST | `/projects/{project_id}/cover/generate` | `generate_cover_for_project()` | project_id, req |
| GET | `/images/{filename}` | `serve_cover_image()` | filename |
| POST | `/projects/{project_id}/publish` | `publish_project()` | project_id, req |
| POST | `/projects/{project_id}/publish/confirm` | `confirm_published()` | project_id, platform, url |
| POST | `/projects/{project_id}/auto-edit` | `auto_edit_video()` | project_id, req |
| GET | `/video/{filename}` | `serve_video()` | filename |
| POST | `/projects/{project_id}/video/capcut-export` | `capcut_export_guide()` | project_id |
| POST | `/projects/{project_id}/auto-publish` | `auto_publish()` | project_id, req |
| GET | `/publish/config` | `get_publish_config()` |  |
| POST | `/projects/{project_id}/tts/generate` | `generate_tts()` | project_id, req |
| GET | `/audio/{filename}` | `serve_audio()` | filename |
| GET | `/tts/voices` | `list_tts_voices()` |  |
| GET | `/dashboard` | `operations_dashboard()` |  |

**类 `TopicIdeaCreate`** (继承 `BaseModel`) — 行 27

**类 `TopicIdeaOut`** (继承 `BaseModel`) — 行 33

**类 `ProjectCreate`** (继承 `BaseModel`) — 行 42

**类 `ProjectOut`** (继承 `BaseModel`) — 行 48

**类 `ScriptGenerateRequest`** (继承 `BaseModel`) — 行 59

**类 `ScriptUpdateRequest`** (继承 `BaseModel`) — 行 66

**类 `CoverGenerateRequest`** (继承 `BaseModel`) — 行 71

**类 `PublishRequest`** (继承 `BaseModel`) — 行 78

**类 `PlatformAccountCreate`** (继承 `BaseModel`) — 行 84

**类 `AutoEditRequest`** (继承 `BaseModel`) — 行 758

**类 `AutoPublishRequest`** (继承 `BaseModel`) — 行 987

**类 `TTSRequest`** (继承 `BaseModel`) — 行 1205

| 函数 | 签名 | 说明 |
|------|------|------|
| `create_topic` | `(req: TopicIdeaCreate)` | 手动添加选题 |
| `list_topics` | `(limit: int = 50, unused_only: bool = False)` | 列出选题库 |
| `ai_discover_topics` | `(keyword: str = "", count: int = 5)` | AI 自动发现选题 |
| `add_account` | `(req: PlatformAccountCreate)` | 添加平台账号 |
| `list_accounts` | `(platform: str = "")` | 列出所有账号 |
| `create_project` | `(req: ProjectCreate)` | 创建内容项目 |
| `list_projects` | `(status: str = "", platform: str = "", limit: int = 50)` | 列出内容项目 |
| `get_project` | `(project_id: int)` | 获取项目详情 |
| `update_project_status` | `(project_id: int, status: str)` | 更新项目状态 |
| `generate_script` | `(project_id: int, req: ScriptGenerateRequest = None)` | AI 生成口播稿 |
| `update_script` | `(project_id: int, req: ScriptUpdateRequest)` | 更新口播稿（人工编辑后保存） |
| `polish_script` | `(project_id: int, style: str = "更口语化")` | AI 润色口播稿 |
| `generate_editing_plan` | `(project_id: int)` | 生成视频剪辑方案 |
| `upload_video_path` | `(project_id: int, video_path: str)` | 记录视频文件路径（实际文件由用户上传到指定目录） |
| `generate_cover_for_project` | `(project_id: int, req: CoverGenerateRequest = None)` | 为项目生成封面图 |
| `serve_cover_image` | `(filename: str)` | 提供封面图文件 |
| `publish_project` | `(project_id: int, req: PublishRequest = None)` | 发布到多平台（当前为模拟/记录，实际发布需对接各平台 API） |
| `confirm_published` | `(project_id: int, platform: str, url: str = "")` | 确认已发布（用户手动发布后回填链接） |
| `auto_edit_video` | `(project_id: int, req: AutoEditRequest = None)` | 自动剪辑视频（基于 FFmpeg + 口播稿时间轴） |
| `serve_video` | `(filename: str)` | 提供视频文件 |
| `capcut_export_guide` | `(project_id: int)` | 生成剪映导入指南（剪映目前没有开放 API，提供自动化脚本） |
| `auto_publish` | `(project_id: int, req: AutoPublishRequest = None)` | 一键发布到多平台（通过 Postiz 或 n8n） |
| `get_publish_config` | `()` | 获取发布配置状态 |
| `generate_tts` | `(project_id: int, req: TTSRequest = None)` | 将口播稿转为语音（火山引擎 TTS） |
| `serve_audio` | `(filename: str)` | 提供音频文件 |
| `list_tts_voices` | `()` | 列出可用音色 |
| `operations_dashboard` | `()` | 运营仪表盘 |

**关键依赖：**
- `from fastapi import APIRouter, HTTPException`
- `import httpx`
- `from database import get_db`
- `from ai_client import ai_client`
- `from fastapi.responses import FileResponse`
- `from fastapi.responses import FileResponse`
- `from fastapi.responses import FileResponse`

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
#### `backend/endpoints/second_self.py` (624 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/api/files` | `list_files()` |  |
| GET | `/api/file` | `read_file()` | path, description="相对路径" |
| POST | `/api/file` | `write_file()` | path, description="相对路径" |
| GET | `/api/self` | `get_self_layer()` |  |
| POST | `/api/decide` | `decide()` | body |
| POST | `/api/chat` | `chat()` | body |
| POST | `/api/chat/stream` | `chat_stream()` | body |
| GET | `/api/memory/stats` | `memory_stats()` |  |
| GET | `/api/memory` | `search_memory_api()` | q, description="搜索关键词" |
| POST | `/api/lint` | `run_lint()` |  |
| POST | `/api/ingest` | `ingest_api()` | body |
| POST | `/api/ingest/enhanced` | `ingest_enhanced_api()` | body |
| POST | `/api/self/scan-changes` | `scan_self_changes_api()` |  |
| GET | `/api/pending-captures` | `get_pending_captures_api()` |  |
| POST | `/api/pending-captures/confirm` | `confirm_pending_api()` | body |
| POST | `/api/project/scan` | `scan_project_api()` |  |
| POST | `/api/social/ingest` | `social_ingest_api()` | body |
| POST | `/api/chat/distill` | `chat_distill_api()` | body |
| POST | `/api/batch-import` | `batch_import_api()` | body |
| POST | `/api/chat/batch-distill` | `()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_files` | `()` | - |
| `get_self_layer` | `()` | 返回当前 Self 层快照（ME.md + DASHBOARD.md 解析结果） |
|   \u2b91 `generate` | `()` | - |
| `memory_stats` | `()` | 返回记忆存储统计信息 |
| `run_lint` | `()` | - |
| `scan_self_changes_api` | `()` | 扫描 Self 核心文件变更，自动生成 update 记忆。 |
| `get_pending_captures_api` | `()` | 获取待确认队列中的低置信度记忆候选。 |
| `scan_project_api` | `()` | 扫描 DASHBOARD 项目的骨架变更，生成 milestone 记忆。 |

**关键依赖：**
- `from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File, Form`
- `from fastapi.responses import StreamingResponse`

---
#### `backend/endpoints/skills.py` (250 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/community` | `()` |  |
| GET | `/community/categories` | `list_categories()` |  |
| POST | `/community/sync` | `sync_community()` |  |
| GET | `/community/stats` | `community_stats()` |  |
| GET | `/local` | `list_local_skills()` |  |
| POST | `/local/scan` | `scan_local()` |  |
| POST | `/local/{skill_id}/toggle` | `toggle_local_skill()` | skill_id, req |
| DELETE | `/local/{skill_id}` | `delete_local_skill()` | skill_id |
| POST | `/local/install` | `install_skill()` | req |

**类 `CommunitySkillOut`** (继承 `BaseModel`) — 行 34

**类 `LocalSkillOut`** (继承 `BaseModel`) — 行 47

**类 `SyncResult`** (继承 `BaseModel`) — 行 58

**类 `ToggleRequest`** (继承 `BaseModel`) — 行 66

**类 `ToggleResult`** (继承 `BaseModel`) — 行 70

**类 `DeleteResult`** (继承 `BaseModel`) — 行 77

**类 `InstallRequest`** (继承 `BaseModel`) — 行 83

**类 `InstallResult`** (继承 `BaseModel`) — 行 88

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_categories` | `()` | 获取所有 Skill 分类 |
| `sync_community` | `()` | 手动触发从 GitHub 同步社区 Skill 目录 |
| `community_stats` | `()` | 获取同步统计信息 |
| `list_local_skills` | `()` | 获取已安装的本地 Skill 列表 |
| `scan_local` | `()` | 重新扫描本地 Skill 文件 |
| `toggle_local_skill` | `(skill_id: str, req: ToggleRequest)` | 启用/禁用本地 Skill |
| `delete_local_skill` | `(skill_id: str)` | 卸载本地 Skill |
| `install_skill` | `(req: InstallRequest)` | 安装社区 Skill 到本地  当前实现：标记为已安装（实际文件操作需要 git clone，后续扩展） |

**关键依赖：**
- `from fastapi import APIRouter, Query`
- `from database import get_db, DB_PATH`

---
#### `backend/endpoints/sop.py` (531 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| GET | `/sop/blocks` | `list_blocks()` | search, tag |
| GET | `/sop/blocks/{block_id}` | `get_block()` | block_id |
| POST | `/sop/blocks` | `create_block()` | payload |
| PUT | `/sop/blocks/{block_id}` | `update_block()` | block_id, payload |
| DELETE | `/sop/blocks/{block_id}` | `delete_block()` | block_id |
| GET | `/sop/chains` | `list_chains()` |  |
| GET | `/sop/chains/{chain_id}` | `get_chain()` | chain_id |
| POST | `/sop/chains` | `create_chain()` | payload |
| PUT | `/sop/chains/{chain_id}` | `update_chain()` | chain_id, payload |
| DELETE | `/sop/chains/{chain_id}` | `delete_chain()` | chain_id |
| POST | `/sop/chains/{chain_id}/blocks` | `add_block_to_chain()` | chain_id, payload |
| PUT | `/sop/chains/{chain_id}/blocks/{cb_id}` | `update_chain_block()` | chain_id, cb_id, payload |
| DELETE | `/sop/chains/{chain_id}/blocks/{cb_id}` | `remove_block_from_chain()` | chain_id, cb_id |
| PUT | `/sop/chains/{chain_id}/reorder` | `reorder_chain_blocks()` | chain_id, payload |
| GET | `/sop/suggestions` | `list_suggestions()` | status, suggestion_type, limit |
| GET | `/sop/suggestions/{sug_id}` | `get_suggestion()` | sug_id |
| POST | `/sop/suggestions/{sug_id}/confirm` | `confirm_suggestion()` | sug_id |
| POST | `/sop/suggestions/{sug_id}/reject` | `reject_suggestion()` | sug_id, payload |
| POST | `/sop/evolution/analyze` | `trigger_analysis()` | payload |
| GET | `/sop/wiki-unmatched` | `list_unmatched_wiki()` |  |

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_blocks` | `(search: str = None, tag: str = None)` | - |
| `get_block` | `(block_id: int)` | - |
| `create_block` | `(payload: dict)` | - |
| `update_block` | `(block_id: int, payload: dict)` | - |
| `delete_block` | `(block_id: int)` | - |
| `list_chains` | `()` | - |
| `get_chain` | `(chain_id: int)` | - |
| `create_chain` | `(payload: dict)` | - |
| `update_chain` | `(chain_id: int, payload: dict)` | - |
| `delete_chain` | `(chain_id: int)` | - |
| `add_block_to_chain` | `(chain_id: int, payload: dict)` | - |
| `update_chain_block` | `(chain_id: int, cb_id: int, payload: dict)` | - |
| `remove_block_from_chain` | `(chain_id: int, cb_id: int)` | - |
| `reorder_chain_blocks` | `(chain_id: int, payload: dict)` | Batch reorder: {order: [{cb_id, sort_order}, ...]} |
| `list_suggestions` | `(status: str = "pending", suggestion_type: str = None, limit: int = 50)` | - |
| `get_suggestion` | `(sug_id: int)` | - |
| `confirm_suggestion` | `(sug_id: int)` | Apply the suggestion: create block, merge content, or insert into chain. |
| `reject_suggestion` | `(sug_id: int, payload: dict = None)` | - |
| `trigger_analysis` | `(payload: dict = None)` | Trigger AI analysis: match wiki pages to SOP blocks/chains. |
| `list_unmatched_wiki` | `()` | Wiki pages not yet linked to any SOP block or pending suggestion. |

**关键依赖：**
- `from fastapi import APIRouter`
- `from database import get_db`

---
#### `backend/endpoints/upload.py` (360 行)

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
- `import httpx`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`
- `from processing.vector_store import get_vector_store`
- `from processing.chunker import chunk_text`
- `from processing.vector_store import get_vector_store`

---
#### `backend/endpoints/wiki.py` (1009 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/wiki/compile` | `compile_wiki()` | payload |
| GET | `/wiki/pages` | `list_wiki_pages()` | category, search |
| GET | `/wiki/pages/{page_id}` | `get_wiki_page()` | page_id |
| GET | `/wiki/graph` | `get_wiki_graph()` |  |
| GET | `/wiki/categories` | `get_wiki_categories()` |  |
| DELETE | `/wiki/pages/{page_id}` | `delete_wiki_page()` | page_id |
| POST | `/wiki/pages` | `create_wiki_page()` | request |
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
| `create_wiki_page` | `(request: Request)` | 手动创建 Wiki 页面 |
| `update_wiki_page` | `(page_id: int, payload: dict)` | 手动编辑 Wiki 页面 |
| `delete_all_wiki_pages` | `()` | - |
| `regenerate_wiki` | `()` | 清空 Wiki 并重新编译所有文档 |
| `search_wiki` | `(payload: dict)` | 语义搜索 Wiki 页面 |
| `reindex_wiki` | `()` | 重建所有 Wiki 页面的向量索引 |
| `generate_learning_paths` | `()` | 分析所有 Wiki 页面，自动生成学习路径 |
| `generate_category_overviews` | `()` | 为每个分类生成综述 hub 页面 |

**关键依赖：**
- `from fastapi import APIRouter, Request`
- `from database import get_db`
- `from ai_client import ai_client`
- `from processing.vector_store import get_vector_store`

---
#### `backend/endpoints/workflow.py` (437 行)

| 方法 | 路径 | 处理函数 | 参数 |
|------|------|----------|------|
| POST | `/workflow/run` | `workflow_run()` | req |
| GET | `/workflow/status/{task_id}` | `workflow_status()` | task_id |
| POST | `/workflow/pause/{task_id}` | `workflow_pause()` | task_id |
| POST | `/workflow/resume/{task_id}` | `workflow_resume()` | task_id, req |
| GET | `/workflow/templates` | `workflow_templates()` |  |
| GET | `/workflow/templates/{filename}` | `workflow_template_get()` | filename |
| PUT | `/workflow/templates/{filename}` | `workflow_template_save()` | filename, req |
| DELETE | `/workflow/templates/{filename}` | `workflow_template_delete()` | filename |
| POST | `/workflow/templates/{filename}/copy` | `workflow_template_copy()` | filename |
| POST | `/workflow/create-from-text` | `workflow_create_from_text()` | req |
| GET | `/workflow/queue/status` | `workflow_queue_status()` | show_archived |
| POST | `/workflow/archive/{task_id}` | `workflow_archive()` | task_id |
| GET | `/workflow/tools` | `workflow_tools()` |  |
| GET | `/workflow/output/{task_id}/{filename}` | `workflow_download()` | task_id, filename |

**类 `RunRequest`** (继承 `BaseModel`) — 行 28

**类 `ResumeRequest`** (继承 `BaseModel`) — 行 33

**类 `CreateFromTextRequest`** (继承 `BaseModel`) — 行 37

**类 `TemplateSaveRequest`** (继承 `BaseModel`) — 行 42

| 函数 | 签名 | 说明 |
|------|------|------|
| `workflow_run` | `(req: RunRequest)` | 启动一个 workflow。 |
| `workflow_status` | `(task_id: str)` | 查询单个任务状态。 |
| `workflow_pause` | `(task_id: str)` | 暂停一个运行中的 workflow。 |
| `workflow_resume` | `(task_id: str, req: ResumeRequest = None)` | 恢复一个暂停的 workflow。 |
| `workflow_templates` | `()` | 列出所有可用的 YAML 模板。 |
| `workflow_template_get` | `(filename: str)` | 获取单个模板的 YAML 原始内容（用于编辑）。 |
| `workflow_template_save` | `(filename: str, req: TemplateSaveRequest)` | 保存/更新 YAML 模板。 |
| `workflow_template_delete` | `(filename: str)` | 删除一个 YAML 模板。 |
| `workflow_template_copy` | `(filename: str)` | 复制一个模板。 |
| `workflow_create_from_text` | `(req: CreateFromTextRequest)` | 用大白话描述创建 workflow 模板——AI 自动转译为 YAML。  示例输入： "打开百度搜猫的图片，截图保存，然后AI分析图片里什么品种"  系统会用 |
| `workflow_queue_status` | `(show_archived: bool = False)` | 获取所有 workflow 任务状态（最近 20 个）。 |
| `workflow_archive` | `(task_id: str)` | 切换任务的归档状态。 |
| `workflow_tools` | `()` | 列出所有已注册的工具。 |
| `workflow_download` | `(task_id: str, filename: str)` | 下载 workflow 输出文件（截图、报告等）。 |

**关键依赖：**
- `from fastapi import APIRouter, HTTPException`
- `from fastapi.responses import FileResponse`

---
## MCP Server

## 前端页面

#### `electron/node_modules/electron/dist/LICENSES.chromium.html` (164588 行)

- 0 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `print-link`

---
#### `electron/node_modules/plist/examples/browser/index.html` (15 行)

- 2 个 `<script>` 块, 0 个 `<style>` 块

---
#### `extension/popup.html` (52 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `apiBase`, `saveBtn`, `captureBtn`, `clipPageBtn`, `douyinSection`, `douyinFavBtn`, `douyinStatus`, `douyinLinkList`, `status`

---
#### `frontend/dist/admin/admin.html` (308 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `statsGrid`, `healthDot`, `systemStatus`, `logBox`, `recentDocs`
- **JS 函数：**
  - `fmt(n)` -> 行 154
  - `get(obj, path, fallback)` -> 行 161
  - `loadStats()` -> 行 173
  - `checkHealth()` -> 行 205
  - `loadLogs()` -> 行 224
  - `loadRecentDocs()` -> 行 249
  - `openInbox()` -> 行 276
  - `exportAll()` -> 行 286
  - `escapeHtml(str)` -> 行 291

---
#### `frontend/dist/index.html` (18 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `app`

---
#### `frontend/dist/second-self/index.html` (826 行)

- 3 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `statMemory`, `statProjects`, `statStatus`, `heroArea`, `hero-canvas`, `modeLabel`, `hintLabel`, `responseBubble`, `sidePanel`, `projectsList`, `maintList`, `memoryInfo`, `btnPanel`, `btnUpload`, `fileInput`, `btnVoice`, `btnDecide`, `btnReset`, `btnImport`, `decisionOverlay`
- **JS 函数：**
  - `loadDashboard()` -> 行 400
  - `initSpeech()` -> 行 449
  - `bindEvents()` -> 行 491
  - `handleImportFiles(files)` -> 行 541
  - `renderImportFileList()` -> 行 545
  - `toggleVoice()` -> 行 629
  - `analyzeText()` -> 行 636
  - `processMessage(text)` -> 行 647
  - `flushDisplay()` -> 行 664
  - `scheduleFlush()` -> 行 673
  - `speakText(text)` -> 行 728
  - `setMode(mode, label)` -> 行 740
  - `showResponse(quote, result, streaming)` -> 行 744
  - `showResponseStreaming(quoteText, resultText)` -> 行 752
  - `showResponseFinal(quoteText, resultText)` -> 行 772
  - `simpleMarkdown(text)` -> 行 779
  - `showDecision(data)` -> 行 788
  - `togglePanel()` -> 行 804
  - `toast(msg)` -> 行 808
  - `calcDaysAgo(dateStr)` -> 行 813

---
#### `frontend/index.html` (17 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `app`

---
#### `frontend/node_modules/katex/contrib/auto-render/index.html` (58 行)

- 3 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `test`

---
#### `frontend/node_modules/katex/contrib/copy-tex/index.html` (39 行)

- 4 个 `<script>` 块, 1 个 `<style>` 块

---
#### `frontend/node_modules/mhchemparser/test/test-dist.html` (212 行)

- 3 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `output`
- **JS 函数：**
  - `test(type, input, expected)` -> 行 19
  - `output(html)` -> 行 26

---
#### `frontend/node_modules/mhchemparser/test/test-esm.html` (209 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `output`
- **JS 函数：**
  - `test(type, input, expected)` -> 行 16
  - `output(html)` -> 行 23

---
#### `frontend/node_modules/tslib/tslib.es6.html` (1 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块

---
#### `frontend/node_modules/tslib/tslib.html` (1 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块

---
#### `frontend/node_modules/xss/dist/test.html` (15 行)

- 3 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `result`

---
#### `frontend/public/admin/admin.html` (308 行)

- 1 个 `<script>` 块, 0 个 `<style>` 块
- **关键 DOM ID：** `statsGrid`, `healthDot`, `systemStatus`, `logBox`, `recentDocs`
- **JS 函数：**
  - `fmt(n)` -> 行 154
  - `get(obj, path, fallback)` -> 行 161
  - `loadStats()` -> 行 173
  - `checkHealth()` -> 行 205
  - `loadLogs()` -> 行 224
  - `loadRecentDocs()` -> 行 249
  - `openInbox()` -> 行 276
  - `exportAll()` -> 行 286
  - `escapeHtml(str)` -> 行 291

---
#### `frontend/public/second-self/index.html` (826 行)

- 3 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `statMemory`, `statProjects`, `statStatus`, `heroArea`, `hero-canvas`, `modeLabel`, `hintLabel`, `responseBubble`, `sidePanel`, `projectsList`, `maintList`, `memoryInfo`, `btnPanel`, `btnUpload`, `fileInput`, `btnVoice`, `btnDecide`, `btnReset`, `btnImport`, `decisionOverlay`
- **JS 函数：**
  - `loadDashboard()` -> 行 400
  - `initSpeech()` -> 行 449
  - `bindEvents()` -> 行 491
  - `handleImportFiles(files)` -> 行 541
  - `renderImportFileList()` -> 行 545
  - `toggleVoice()` -> 行 629
  - `analyzeText()` -> 行 636
  - `processMessage(text)` -> 行 647
  - `flushDisplay()` -> 行 664
  - `scheduleFlush()` -> 行 673
  - `speakText(text)` -> 行 728
  - `setMode(mode, label)` -> 行 740
  - `showResponse(quote, result, streaming)` -> 行 744
  - `showResponseStreaming(quoteText, resultText)` -> 行 752
  - `showResponseFinal(quoteText, resultText)` -> 行 772
  - `simpleMarkdown(text)` -> 行 779
  - `showDecision(data)` -> 行 788
  - `togglePanel()` -> 行 804
  - `toast(msg)` -> 行 808
  - `calcDaysAgo(dateStr)` -> 行 813

---
#### `frontend/test-markdown.html` (78 行)

- 0 个 `<script>` 块, 1 个 `<style>` 块
- **JS 函数：**
  - `hello()` -> 行 41

---
#### `project-memory/ui/study-hub-dashboard-style-refresh.html` (4370 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `home`, `dashboard-grid`, `grid-bg`, `focus-content`, `wiki`, `kb`, `auto`, `ddl`, `journal`, `flow`, `creator`, `search`, `notifications`, `profile`, `settings`, `settings-panel`, `secondself`, `skillmarket`, `modal-overlay`, `modal-title`
- **JS 函数：**
  - `showPage(id)` -> 行 3157
  - `switchFocusView(view)` -> 行 3162
  - `swapNodes(a, b)` -> 行 3261
  - `setupCard(card)` -> 行 3268
  - `switchSettingsTab(el, tab)` -> 行 3310
  - `openModal(title, body)` -> 行 3557
  - `closeModal()` -> 行 3562
  - `initToggleSwitches()` -> 行 3567

---
#### `project-memory/ui/test-write.html` (1 行)

- 0 个 `<script>` 块, 0 个 `<style>` 块

---
#### `project-memory/ui/横屏工作台Dashboard-低保真线框图-完整版.html` (3535 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `home`, `dashboard-grid`, `grid-bg`, `focus-content`, `wiki`, `kb`, `auto`, `ddl`, `journal`, `flow`, `creator`, `search`, `notifications`, `profile`, `settings`, `settings-panel`, `secondself`, `skillmarket`, `modal-overlay`, `modal-title`
- **JS 函数：**
  - `showPage(id)` -> 行 2352
  - `switchFocusView(view)` -> 行 2357
  - `swapNodes(a, b)` -> 行 2456
  - `setupCard(card)` -> 行 2463
  - `switchSettingsTab(el, tab)` -> 行 2505
  - `openModal(title, body)` -> 行 2752
  - `closeModal()` -> 行 2757
  - `initToggleSwitches()` -> 行 2762

---
#### `project-memory/ui/横屏工作台Dashboard-低保真线框图.html` (2750 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `home`, `dashboard-grid`, `grid-bg`, `focus-content`, `wiki`, `kb`, `auto`, `ddl`, `journal`, `flow`, `creator`, `brainstorm`, `learning`, `learning-checklist-view`, `learning-plan-view`, `learning-overview-view`, `sop`, `skills`, `skills-discover`, `skills-installed`
- **JS 函数：**
  - `showPage(id)` -> 行 2459
  - `switchFocusView(view)` -> 行 2464
  - `swapNodes(a, b)` -> 行 2563
  - `setupCard(card)` -> 行 2570

---
#### `project-memory/ui/横屏工作台Dashboard-高保真框架图-完整版.html` (252 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `pg-home`, `pg-wiki`, `pg-kb`, `pg-brainstorm`, `pg-learning`, `pg-auto`, `pg-ddl`, `pg-journal`, `pg-flow`, `pg-sop`, `pg-creator`, `pg-skills`, `pg-ss`, `pg-design`, `pg-states`, `pg-settings`
- **JS 函数：**
  - `sp(id)` -> 行 241
  - `tt()` -> 行 249

---
#### `second-self/app/index.html` (870 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `statMemory`, `statProjects`, `statStatus`, `heroArea`, `hero-canvas`, `modeLabel`, `hintLabel`, `responseBubble`, `sidePanel`, `memoryFieldPanel`, `fieldBadge`, `emotionLabel`, `emotionTuning`, `fieldLayers`, `coreLayerItems`, `activeLayerItems`, `suppressLayerItems`, `projectsList`, `maintList`, `memoryInfo`
- **JS 函数：**
  - `loadDashboard()` -> 行 486
  - `showMemoryField(field)` -> 行 527
  - `processMessage(text)` -> 行 593
  - `flushDisplay()` -> 行 611
  - `scheduleFlush()` -> 行 619
  - `showResponse(quote, result, streaming)` -> 行 666
  - `showResponseStreaming(quoteText, resultText)` -> 行 672
  - `showResponseFinal(quoteText, resultText)` -> 行 681
  - `simpleMarkdown(text)` -> 行 687
  - `showDecision(data)` -> 行 691
  - `togglePanel()` -> 行 707
  - `toast(msg)` -> 行 711
  - `calcDaysAgo(dateStr)` -> 行 716
  - `esc(s)` -> 行 721
  - `handleFiles(files)` -> 行 765
  - `renderFileList()` -> 行 769
  - `sendChat()` -> 行 856

---
#### `second-self.bak/app/index.html` (80 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块
- **关键 DOM ID：** `stats`, `total`, `active`, `dormant`, `search`
- **JS 函数：**
  - `loadStats()` -> 行 63
  - `doSearch()` -> 行 72

---
#### `venv/Lib/site-packages/setuptools/tests/indexes/test_links_priority/external.html` (4 行)

- 0 个 `<script>` 块, 0 个 `<style>` 块

---
#### `venv/Lib/site-packages/setuptools/tests/indexes/test_links_priority/simple/foobar/index.html` (5 行)

- 0 个 `<script>` 块, 0 个 `<style>` 块

---
#### `venv/Lib/site-packages/torch/utils/model_dump/skeleton.html` (22 行)

- 1 个 `<script>` 块, 1 个 `<style>` 块

---
## Chrome 扩展

### 扩展配置
- **名称**: 学习中枢 - 对话采集
- **版本**: 2.1
- **权限**: `storage`, `tabs`, `scripting`, `activeTab`, `alarms`, `contextMenus`
- **Host 权限**: `https://*/*`, `http://localhost:8741/*`

#### `extension/background.js` (176 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `keepAlive()` |  | 15 |
| `getApiBase()` |  | 21 |
| `handleApiRequest()` | request, sendResponse | 50 |

---
#### `extension/bing-assistant.js` (974 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `main()` |  | 34 |
| `loadSceneRules()` |  | 69 |
| `loadState()` |  | 79 |
| `saveState()` |  | 92 |
| `loadPrefs()` |  | 108 |
| `savePrefs()` |  | 130 |
| `restoreFilterState()` | isFilterRefresh, urlScene | 147 |
| `matchScene()` | query | 185 |
| `showPanel()` |  | 198 |
| `cleanupPanel()` |  | 237 |
| `showDot()` |  | 246 |
| `cleanupDot()` |  | 260 |
| `closePanel()` |  | 267 |
| `restorePosition()` |  | 283 |
| `bindPanelEvents()` |  | 298 |
| `handlePanelClick()` | e | 311 |
| `startDrag()` | e | 374 |
| `onDragMove()` | e | 389 |
| `onDragEnd()` |  | 410 |
| `toggleCollapse()` |  | 421 |
| `togglePin()` |  | 437 |
| `updatePinUI()` |  | 443 |
| `switchScene()` | sceneId | 456 |
| `toggleSource()` | item | 486 |
| `resetSources()` |  | 503 |
| `updateAIHint()` |  | 513 |
| `applyFilter()` |  | 529 |
| `adjustBing()` | panelVisible | 562 |
| `watchUrl()` |  | 581 |
| `check()` |  | 584 |
| `bindGlobalEvents()` |  | 633 |
| `cleanupAll()` |  | 643 |
| `renderPanel()` |  | 651 |
| `renderTabs()` |  | 669 |
| `renderBody()` |  | 677 |
| `showGuide()` |  | 744 |
| `getCSS()` |  | 759 |
| `isBingSearch()` |  | 871 |
| `isDark()` |  | 875 |
| `escape()` | text | 880 |
| `getBuiltinRules()` |  | 886 |

---
#### `extension/popup.js` (172 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `getApiBase()` |  | 156 |
| `checkDouyinPage()` |  | 161 |

---
#### `frontend/node_modules/binary-extensions/index.js` (2 行)

---
#### `frontend/node_modules/echarts/dist/extension/bmap.js` (369 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `BMapCoordSys()` | bmap, api | 27 |
| `dataToCoordSize()` | dataSize, dataItem | 102 |
| `createOverlayCtor()` |  | 118 |
| `Overlay()` | root | 119 |
| `v2Equal()` | a, b | 216 |
| `isEmptyObject()` | obj | 246 |
| `zoomEndHandler()` |  | 286 |

---
#### `frontend/node_modules/echarts/dist/extension/bmap.min.js` (22 行)

---
#### `frontend/node_modules/echarts/dist/extension/dataTool.js` (403 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `map()` | arr, cb, context | 59 |
| `reduce()` | arr, cb, memo, context | 77 |
| `bindPolyfill()` | func, context | 86 |
| `isFunction()` | value | 98 |
| `slice()` | arr | 101 |
| `parse()` | xml | 109 |
| `parseAttributes()` | parent | 135 |
| `parseNodes()` | parent, attributesMap | 144 |
| `parseEdges()` | parent | 203 |
| `getAttr()` | el, attrName | 234 |
| `getChildByTagName()` | parent, tagName | 237 |
| `getChildrenByTagName()` | parent, tagName | 248 |
| `asc()` | arr | 307 |
| `quantile()` | ascArr, p | 313 |
| `prepareBoxplotData()` | rawData, opt | 346 |

---
#### `frontend/node_modules/echarts/dist/extension/dataTool.min.js` (22 行)

---
#### `frontend/node_modules/echarts/extension/bmap/BMapCoordSys.js` (235 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `BMapCoordSys()` | bmap, api | 47 |
| `dataToCoordSize()` | dataSize, dataItem | 122 |
| `createOverlayCtor()` |  | 138 |
| `Overlay()` | root | 139 |

---
#### `frontend/node_modules/echarts/extension/bmap/BMapModel.js` (74 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `v2Equal()` | a, b | 46 |

---
#### `frontend/node_modules/echarts/extension/bmap/BMapView.js` (146 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `isEmptyObject()` | obj | 46 |
| `zoomEndHandler()` |  | 86 |

---
#### `frontend/node_modules/echarts/extension/bmap/bmap.js` (65 行)

---
#### `frontend/node_modules/echarts/extension/dataTool/gexf.js` (202 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `parseAttributes()` | parent | 78 |
| `parseNodes()` | parent, attributesMap | 87 |
| `parseEdges()` | parent | 147 |
| `getAttr()` | el, attrName | 178 |
| `getChildByTagName()` | parent, tagName | 181 |
| `getChildrenByTagName()` | parent, tagName | 192 |

---
#### `frontend/node_modules/echarts/extension/dataTool/index.js` (62 行)

---
#### `frontend/node_modules/echarts/extension/dataTool/prepareBoxplotData.js` (116 行)

| 函数 | 参数 | 行号 |
|------|------|------|
| `asc()` | arr | 44 |
| `quantile()` | ascArr, p | 50 |

---
#### `frontend/node_modules/echarts/lib/extension.js` (110 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/lib/input/mathml/mml3/mml3-node.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/lib/input/mathml/mml3/mml3.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/lib/mml3.js` (21 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/mml3.js` (8 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/action.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/lib/action.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/lib/input/tex/action/ActionConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/all-packages.js` (13 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/all-packages.js` (25 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/input/tex/AllPackages.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/input/tex/autoload/AutoloadConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/input/tex/require/RequireConfiguration.js` (7 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/webpack.config.js` (13 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/ams.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/ams.js` (23 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/input/tex/ams/AmsConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/input/tex/ams/AmsItems.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/input/tex/ams/AmsMethods.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/amscd.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/lib/amscd.js` (21 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/lib/input/tex/amscd/AmsCdConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/lib/input/tex/amscd/AmsCdMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/autoload.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/lib/autoload.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/lib/input/tex/autoload/AutoloadConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/webpack.config.js` (14 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/bbox.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/lib/bbox.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/lib/input/tex/bbox/BboxConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/boldsymbol.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/lib/boldsymbol.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/lib/input/tex/boldsymbol/BoldsymbolConfiguration.js` (7 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/braket.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/braket.js` (23 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/input/tex/braket/BraketConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/input/tex/braket/BraketItems.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/input/tex/braket/BraketMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/bussproofs.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/bussproofs.js` (25 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsItems.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsUtil.js` (10 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/cancel.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/lib/cancel.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/lib/input/tex/cancel/CancelConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/webpack.config.js` (13 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/cases.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/lib/cases.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/lib/input/tex/cases/CasesConfiguration.js` (7 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/webpack.config.js` (15 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/centernot.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/lib/centernot.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/lib/input/tex/centernot/CenternotConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/color.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/color.js` (25 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorConstants.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorUtil.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/colortbl.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/lib/colortbl.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/lib/input/tex/colortbl/ColortblConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/colorv2.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/lib/colorv2.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/lib/input/tex/colorv2/ColorV2Configuration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/configmacros.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/lib/configmacros.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/lib/input/tex/configmacros/ConfigMacrosConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/webpack.config.js` (14 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/empheq.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/lib/empheq.js` (21 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/lib/input/tex/empheq/EmpheqConfiguration.js` (6 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/lib/input/tex/empheq/EmpheqUtil.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/webpack.config.js` (13 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/enclose.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/lib/enclose.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/lib/input/tex/enclose/EncloseConfiguration.js` (6 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/extpfeil.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/lib/extpfeil.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/lib/input/tex/extpfeil/ExtpfeilConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/webpack.config.js` (14 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/gensymb.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/lib/gensymb.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/lib/input/tex/gensymb/GensymbConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/html.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/lib/html.js` (21 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/lib/input/tex/html/HtmlConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/lib/input/tex/html/HtmlMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsConfiguration.js` (6 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsItems.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsTags.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsUtil.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/mathtools.js` (27 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/mathtools.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/webpack.config.js` (14 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/lib/input/tex/mhchem/MhchemConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/lib/mhchem.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/mhchem.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/webpack.config.js` (13 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandItems.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandUtil.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/newcommand.js` (25 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/newcommand.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/lib/input/tex/noerrors/NoErrorsConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/lib/noerrors.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/noerrors.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/lib/input/tex/noundefined/NoUndefinedConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/lib/noundefined.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/noundefined.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/input/tex/physics/PhysicsConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/input/tex/physics/PhysicsItems.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/input/tex/physics/PhysicsMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/physics.js` (23 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/physics.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/lib/input/tex/require/RequireConfiguration.js` (7 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/lib/require.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/require.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/webpack.config.js` (13 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/lib/input/tex/setoptions/SetOptionsConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/lib/setoptions.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/setoptions.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/lib/input/tex/tagformat/TagFormatConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/lib/tagformat.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/tagformat.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/lib/input/tex/textcomp/TextcompConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/lib/textcomp.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/textcomp.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/webpack.config.js` (13 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/input/tex/textmacros/TextMacrosConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/input/tex/textmacros/TextMacrosMethods.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/input/tex/textmacros/TextParser.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/textmacros.js` (23 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/textmacros.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/lib/input/tex/unicode/UnicodeConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/lib/unicode.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/unicode.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/lib/input/tex/upgreek/UpgreekConfiguration.js` (4 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/lib/upgreek.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/upgreek.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/lib/input/tex/verb/VerbConfiguration.js` (5 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/lib/verb.js` (19 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/verb.js` (2 行)

---
#### `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/webpack.config.js` (12 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/mml/extensions/mml3.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/action.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/all-packages.js` (34 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/ams.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/amscd.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/autoload.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/bbox.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/boldsymbol.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/braket.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/bussproofs.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/cancel.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/cases.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/centernot.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/color.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/colortbl.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/colorv2.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/configmacros.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/empheq.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/enclose.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/extpfeil.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/gensymb.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/html.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/mathtools.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/mhchem.js` (34 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/newcommand.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/noerrors.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/noundefined.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/physics.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/require.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/setoptions.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/tagformat.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/textcomp.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/textmacros.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/unicode.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/upgreek.js` (1 行)

---
#### `frontend/node_modules/mathjax-full/es5/input/tex/extensions/verb.js` (1 行)

---
## 配置文件

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

### `backend/requirements.txt` (26 行, hash: `9193b97c`)

```
# ===== 核心依赖 =====
python-dotenv>=1.0.0
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
httpx>=0.25.0

# ===== 数据层 =====
chromadb>=0.4.0
watchdog>=4.0.0

# ===== AI / Embedding =====
sentence-transformers>=2.2.0
dashscope>=1.20.0

# ===== 文档处理 =====
PyMuPDF>=1.23.0
jieba>=0.42.0

# ===== 流程编排 =====
pyyaml>=6.0

# ===== 社交解析 =====
douyin-mcp-server>=1.2.0
ffmpeg-python>=0.2.0

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

### `requirements-mcp.txt` (5 行, hash: `e5b54302`)

```
mcp>=1.0.0
httpx>=0.25.0
requests>=2.28.0
dashscope

```

### `second-self/requirements.txt` (4 行, hash: `72e0c00d`)

```
# Second Self — 零依赖运行（Python 3 内置库即可）
# 可选：安装 openai 以启用 LLM 对话功能
# pip install openai

```

### `second-self.bak/requirements.txt` (6 行, hash: `59162edb`)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
requests>=2.31.0
python-multipart>=0.0.6

```

## 工具百宝箱 (mods/)

### brainstorm

| 文件 | 行数 |
|------|------|
| `.gitignore` | 22 |
| `README.md` | 105 |
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
| `start.bat` | 40 |
| `test_app.py` | 305 |
| `test_gui.py` | 296 |
| `护眼仪小助手.spec` | 39 |

### learning

| 文件 | 行数 |
|------|------|
| `vibe-coding-learning-plan.md` | 397 |
| `学习清单生成器.html` | 351 |
| `小白上线一个真实网站.md` | 424 |
| `超级学习管家-全栈VibeCoding路线.md` | 730 |

### suit

| 文件 | 行数 |
|------|------|
| `.gitignore` | 25 |
| `README.md` | 74 |
| `REQUIREMENTS.md` | 230 |
| `build-err.txt` | 1 |
| `build-out.txt` | 1 |
| `eslint.config.js` | 23 |
| `index.html` | 19 |
| `package-lock.json` | 6820 |
| `package.json` | 46 |
| `postcss.config.js` | 7 |
| `public/favicon.svg` | 1 |
| `public/icon-192.png` | 22 |
| `public/icon-192.svg` | 7 |
| `public/icon-512.png` | 95 |
| `public/icons.svg` | 25 |
| `public/manifest.json` | 23 |
| `public/sw.js` | 37 |
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

## B站 MCP Server (bilibili-mcp-server/)

### `bilibili-mcp-server/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bilibili-mcp-server"
version = "1.0.0"
description = "MCP server for parsing Bilibili videos and extracting text"
authors = [{name = "study-web"}]
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = [
    "dashscope",
    "ffmpeg-python",
    "mcp>=1.0.0",
    "requests",
    "tqdm",
]

[project.scripts]
bilibili-mcp-server = "bilibili_mcp_server.server:main"

[tool.setuptools.packages.find]
include = ["bilibili_mcp_server*"]

```

#### `/sessions/inspiring-kind-cerf/mnt/study web/bilibili-mcp-server/bilibili_mcp_server/__init__.py` (9 行)

---
#### `/sessions/inspiring-kind-cerf/mnt/study web/bilibili-mcp-server/bilibili_mcp_server/__main__.py` (8 行)

---
#### `/sessions/inspiring-kind-cerf/mnt/study web/bilibili-mcp-server/bilibili_mcp_server/asr_module.py` (152 行)

**类 `QwenASR`** — 行 18

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, api_key: Optional[str] = None, model: str = "qwen3-asr-flash")` | - |
| `create_asr_instance` | `(api_key: Optional[str] = None, model: str = "qwen3-asr-flash") -> QwenASR` | - |

---
#### `/sessions/inspiring-kind-cerf/mnt/study web/bilibili-mcp-server/bilibili_mcp_server/server.py` (595 行)

**类 `BilibiliProcessor`** — 行 40

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, api_key: str = "", model: Optional[str] = None)` | - |
|   \u2b91 `parse_share_url` | `(self, share_text: str) -> dict` | 从分享链接/文本中解析视频信息 |
|   \u2b91 `get_video_url` | `(self, bvid: str, cid: int, quality: int = 80) -> dict` | 获取视频播放URL |
|   \u2b91 `extract_text_from_audio_url` | `(self, audio_url: str, context: Optional[str] = None) -> str` | 从音频URL中提取文字（ASR） |
|   \u2b91 `extract_text_from_audio_file` | `(self, file_path: Path, context: Optional[str] = None) -> str` | 从本地音频文件中提取文字 |
|   \u2b91 `extract_text_from_video_url` | `(self, video_url: str, context: Optional[str] = None) -> str` | 从视频URL中提取文字（使用阿里云百炼ASR） |
| `parse_bilibili_video_info` | `(share_link: str) -> str` | 解析B站分享链接，获取视频基本信息（标题、封面、UP主、播放量、分P列表等）  参数: - share_link: B站分享链接（b23.tv短链接或bilib |
| `get_bilibili_download_link` | `(share_link: str, cid: Optional[int] = None, quality: Optional[int] = 80) -> str` | 获取B站视频/音频的下载链接  参数: - share_link: B站分享链接或BV号 - cid: 分P的cid（可选，默认使用第一个分P） - quali |
| `get_video_resource` | `(bvid: str) -> str` | 通过BV号获取视频详细信息 |
| `bilibili_usage_guide` | `() -> str` | B站视频解析使用指南 |
| `main` | `()` | 启动MCP服务器 |

**关键依赖：**
- `from mcp.server.fastmcp import FastMCP`
- `from mcp.server.fastmcp import Context`

---
## 小红书 MCP Server (xiaohongshu-mcp-server/)

### `xiaohongshu-mcp-server/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "xiaohongshu-mcp-server"
version = "1.0.0"
description = "MCP server for parsing Xiaohongshu (RedNote) notes and extracting text"
authors = [{name = "study-web"}]
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = [
    "dashscope",
    "ffmpeg-python",
    "mcp>=1.0.0",
    "requests",
    "tqdm",
]

[project.scripts]
xiaohongshu-mcp-server = "xiaohongshu_mcp_server.server:main"

[tool.setuptools.packages.find]
include = ["xiaohongshu_mcp_server*"]

```

#### `/sessions/inspiring-kind-cerf/mnt/study web/xiaohongshu-mcp-server/xiaohongshu_mcp_server/__init__.py` (9 行)

---
#### `/sessions/inspiring-kind-cerf/mnt/study web/xiaohongshu-mcp-server/xiaohongshu_mcp_server/__main__.py` (8 行)

---
#### `/sessions/inspiring-kind-cerf/mnt/study web/xiaohongshu-mcp-server/xiaohongshu_mcp_server/server.py` (608 行)

**类 `QwenASR`** — 行 38

**类 `XiaohongshuProcessor`** — 行 116

| 函数 | 签名 | 说明 |
|------|------|------|
|   \u2b91 `__init__` | `(self, api_key: Optional[str] = None, model: str = "qwen3-asr-flash")` | - |
|   \u2b91 `__init__` | `(self, api_key: str = "", model: Optional[str] = None)` | - |
|   \u2b91 `parse_note_info` | `(self, share_text: str) -> dict` | 解析小红书分享链接获取笔记信息 |
|   \u2b91 `extract_text_from_video` | `(self, video_url: str, context: Optional[str] = None) -> str` | 从小红书视频中提取文字 |
| `parse_xiaohongshu_note_info` | `(share_link: str) -> str` | 解析小红书分享链接，获取笔记基本信息（标题、正文、图片、视频、作者、互动数据等）  参数: - share_link: 小红书分享链接（xhslink.com短 |
| `extract_xiaohongshu_text` | `(share_link: str) -> str` | 提取小红书笔记中的文字内容（标题 + 正文 + 标签）  参数: - share_link: 小红书分享链接  返回: - 笔记的文字内容（Markdown格式 |
| `get_xiaohongshu_media` | `(share_link: str) -> str` | 获取小红书笔记中的图片和视频链接  参数: - share_link: 小红书分享链接  返回: - 包含图片URL列表和视频URL的JSON |
| `get_note_resource` | `(note_id: str) -> str` | 通过笔记ID获取笔记信息 |
| `xiaohongshu_usage_guide` | `() -> str` | 小红书笔记解析使用指南 |
| `main` | `()` | 启动MCP服务器 |

**关键依赖：**
- `from mcp.server.fastmcp import FastMCP`
- `from mcp.server.fastmcp import Context`

---
## 文件完整性指纹

| 文件 | MD5 (前8位) | 行数 |
|------|-------------|------|
| `bilibili-mcp-server/bilibili_mcp_server/__init__.py` | `409ef19c` | 9 |
| `bilibili-mcp-server/bilibili_mcp_server/__main__.py` | `4d3b095c` | 8 |
| `bilibili-mcp-server/bilibili_mcp_server/asr_module.py` | `fa875c58` | 152 |
| `bilibili-mcp-server/bilibili_mcp_server/server.py` | `6e7ae432` | 595 |
| `backend/__init__.py` | `9e67a2e6` | 2 |
| `backend/ai_client.py` | `9a2f8ea0` | 49 |
| `backend/core/skills_scanner.py` | `c4a8a573` | 212 |
| `backend/core/skills_sync.py` | `b7349010` | 244 |
| `backend/database.py` | `12b5a077` | 421 |
| `backend/endpoints/__init__.py` | `d41d8cd9` | 1 |
| `backend/endpoints/admin.py` | `f9217f12` | 217 |
| `backend/endpoints/ai_search.py` | `b903d460` | 157 |
| `backend/endpoints/automation.py` | `a530af05` | 1884 |
| `backend/endpoints/brainstorm.py` | `b5bb66fc` | 279 |
| `backend/endpoints/categories.py` | `9e6cc598` | 247 |
| `backend/endpoints/creator.py` | `d5558a07` | 117 |
| `backend/endpoints/ddl.py` | `5729b4e2` | 199 |
| `backend/endpoints/evolution.py` | `922a09da` | 212 |
| `backend/endpoints/export.py` | `3b9000b4` | 123 |
| `backend/endpoints/images.py` | `1ff3211a` | 110 |
| `backend/endpoints/journal.py` | `a01bfd16` | 210 |
| `backend/endpoints/links.py` | `72532e04` | 92 |
| `backend/endpoints/operations.py` | `6770080d` | 1387 |
| `backend/endpoints/rag.py` | `8c1a86d4` | 106 |
| `backend/endpoints/review.py` | `66f4eda8` | 205 |
| `backend/endpoints/second_self.py` | `f7beec98` | 624 |
| `backend/endpoints/skills.py` | `f5407e6e` | 250 |
| `backend/endpoints/sop.py` | `628eb7e9` | 531 |
| `backend/endpoints/upload.py` | `d239c3d5` | 360 |
| `backend/endpoints/wiki.py` | `d57722e7` | 1009 |
| `backend/endpoints/workflow.py` | `cad7ab14` | 437 |
| `backend/evolution_files.py` | `f28b1274` | 169 |
| `backend/evolution_pipeline.py` | `8fcc61e2` | 289 |
| `backend/main.py` | `f6105628` | 458 |
| `backend/mcp_server.py` | `f3c3695a` | 823 |
| `backend/processing/__init__.py` | `d41d8cd9` | 1 |
| `backend/processing/chunker.py` | `3cebfd14` | 37 |
| `backend/processing/processors.py` | `733919b8` | 71 |
| `backend/processing/vector_store.py` | `e3d27081` | 303 |
| `backend/social_parsers.py` | `613f8fb5` | 352 |
| `backend/sop_evolution.py` | `b3786b26` | 297 |
| `backend/tests/__init__.py` | `d41d8cd9` | 1 |
| `backend/tests/test_main.py` | `9d0d1b32` | 82 |
| `backend/watcher.py` | `8cf30998` | 118 |
| `backend/workflow/__init__.py` | `30930bd7` | 3 |
| `backend/workflow/engine.py` | `f0ab682e` | 343 |
| `backend/workflow/executors.py` | `86abc681` | 362 |
| `backend/workflow/loader.py` | `aae7dd91` | 226 |
| `backend/workflow/registry.py` | `8c25df18` | 75 |
| `electron/node_modules/electron/dist/LICENSES.chromium.html` | `2692689c` | 164588 |
| `electron/node_modules/plist/examples/browser/index.html` | `c7c600b2` | 15 |
| `extension/background.js` | `fbd0bfb1` | 176 |
| `extension/bing-assistant.js` | `e92470f5` | 974 |
| `extension/popup.html` | `da951c56` | 52 |
| `extension/popup.js` | `3c3d1623` | 172 |
| `frontend/dist/admin/admin.html` | `24d52e08` | 308 |
| `frontend/dist/index.html` | `82a2d8ef` | 18 |
| `frontend/dist/second-self/index.html` | `41bf7996` | 826 |
| `frontend/index.html` | `9a3b25b4` | 17 |
| `frontend/node_modules/binary-extensions/index.js` | `1ccd550e` | 2 |
| `frontend/node_modules/echarts/dist/extension/bmap.js` | `ae72dd31` | 369 |
| `frontend/node_modules/echarts/dist/extension/bmap.min.js` | `3430781d` | 22 |
| `frontend/node_modules/echarts/dist/extension/dataTool.js` | `7f582189` | 403 |
| `frontend/node_modules/echarts/dist/extension/dataTool.min.js` | `c7c7d3f8` | 22 |
| `frontend/node_modules/echarts/extension/bmap/BMapCoordSys.js` | `af04766b` | 235 |
| `frontend/node_modules/echarts/extension/bmap/BMapModel.js` | `4562534b` | 74 |
| `frontend/node_modules/echarts/extension/bmap/BMapView.js` | `32192b9b` | 146 |
| `frontend/node_modules/echarts/extension/bmap/bmap.js` | `c12fd2de` | 65 |
| `frontend/node_modules/echarts/extension/dataTool/gexf.js` | `a5c11e59` | 202 |
| `frontend/node_modules/echarts/extension/dataTool/index.js` | `91cd9172` | 62 |
| `frontend/node_modules/echarts/extension/dataTool/prepareBoxplotData.js` | `e8da1db3` | 116 |
| `frontend/node_modules/echarts/lib/extension.js` | `0f5a7753` | 110 |
| `frontend/node_modules/katex/contrib/auto-render/index.html` | `95856723` | 58 |
| `frontend/node_modules/katex/contrib/copy-tex/index.html` | `7f11b779` | 39 |
| `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/lib/input/mathml/mml3/mml3-node.js` | `0653a301` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/lib/input/mathml/mml3/mml3.js` | `f641c3e9` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/lib/mml3.js` | `959eee47` | 21 |
| `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/mml3.js` | `6180d004` | 8 |
| `frontend/node_modules/mathjax-full/components/src/input/mml/extensions/mml3/webpack.config.js` | `4ef7c211` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/action.js` | `22a89589` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/lib/action.js` | `16f56749` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/lib/input/tex/action/ActionConfiguration.js` | `e9499f91` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/action/webpack.config.js` | `9c723d25` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/all-packages.js` | `92a54730` | 13 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/all-packages.js` | `45a10b25` | 25 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/input/tex/AllPackages.js` | `3117ec87` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/input/tex/autoload/AutoloadConfiguration.js` | `d60517c4` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/lib/input/tex/require/RequireConfiguration.js` | `a9df68e1` | 7 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/all-packages/webpack.config.js` | `1bd94c7a` | 13 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/ams.js` | `90545a50` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/ams.js` | `f7b95218` | 23 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/input/tex/ams/AmsConfiguration.js` | `29abe8b7` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/input/tex/ams/AmsItems.js` | `9c0f5f86` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/lib/input/tex/ams/AmsMethods.js` | `fd5d0b86` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/ams/webpack.config.js` | `66fa33ec` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/amscd.js` | `c9991664` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/lib/amscd.js` | `9ffb9048` | 21 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/lib/input/tex/amscd/AmsCdConfiguration.js` | `9a695477` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/lib/input/tex/amscd/AmsCdMethods.js` | `0877f377` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/amscd/webpack.config.js` | `536880f6` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/autoload.js` | `845c6cba` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/lib/autoload.js` | `cb38faaf` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/lib/input/tex/autoload/AutoloadConfiguration.js` | `d60517c4` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/autoload/webpack.config.js` | `b0f31cb7` | 14 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/bbox.js` | `9a3f6b42` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/lib/bbox.js` | `5ff155fb` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/lib/input/tex/bbox/BboxConfiguration.js` | `036e08f8` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bbox/webpack.config.js` | `d301c965` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/boldsymbol.js` | `a1aa8aef` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/lib/boldsymbol.js` | `c811741a` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/lib/input/tex/boldsymbol/BoldsymbolConfiguration.js` | `2b638b0e` | 7 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/boldsymbol/webpack.config.js` | `d1e58d3e` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/braket.js` | `07a70e10` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/braket.js` | `21852f13` | 23 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/input/tex/braket/BraketConfiguration.js` | `33e36bc9` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/input/tex/braket/BraketItems.js` | `f5c3fe98` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/lib/input/tex/braket/BraketMethods.js` | `b2705868` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/braket/webpack.config.js` | `dbadfbed` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/bussproofs.js` | `d0b36b6e` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/bussproofs.js` | `4e9ba83f` | 25 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsConfiguration.js` | `2d86b3cd` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsItems.js` | `dfd8c472` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsMethods.js` | `eec85356` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/lib/input/tex/bussproofs/BussproofsUtil.js` | `35eef457` | 10 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/bussproofs/webpack.config.js` | `8b9cd550` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/cancel.js` | `fd443419` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/lib/cancel.js` | `e41afa32` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/lib/input/tex/cancel/CancelConfiguration.js` | `3a11fa71` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cancel/webpack.config.js` | `48bd2fa0` | 13 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/cases.js` | `c5bbc493` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/lib/cases.js` | `8e4e5b0b` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/lib/input/tex/cases/CasesConfiguration.js` | `cfbf6eea` | 7 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/cases/webpack.config.js` | `3343d3e5` | 15 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/centernot.js` | `76d04500` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/lib/centernot.js` | `795614e8` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/lib/input/tex/centernot/CenternotConfiguration.js` | `be9e021c` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/centernot/webpack.config.js` | `51615849` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/color.js` | `d43dd76c` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/color.js` | `08e97111` | 25 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorConfiguration.js` | `1ce2be18` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorConstants.js` | `a1f83fa7` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorMethods.js` | `7562beaf` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/lib/input/tex/color/ColorUtil.js` | `570de40e` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/color/webpack.config.js` | `92711266` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/colortbl.js` | `baffcaaa` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/lib/colortbl.js` | `91486dd2` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/lib/input/tex/colortbl/ColortblConfiguration.js` | `feecae46` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colortbl/webpack.config.js` | `e082e917` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/colorv2.js` | `09ead5d3` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/lib/colorv2.js` | `68a63e4c` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/lib/input/tex/colorv2/ColorV2Configuration.js` | `9c202c58` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/colorv2/webpack.config.js` | `005ba8f4` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/configmacros.js` | `67daaa38` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/lib/configmacros.js` | `85523145` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/lib/input/tex/configmacros/ConfigMacrosConfiguration.js` | `22fd5f03` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/configmacros/webpack.config.js` | `37b04c05` | 14 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/empheq.js` | `810e4cf7` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/lib/empheq.js` | `f584a9ec` | 21 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/lib/input/tex/empheq/EmpheqConfiguration.js` | `9e538a6b` | 6 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/lib/input/tex/empheq/EmpheqUtil.js` | `5dc83402` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/empheq/webpack.config.js` | `15bdcee1` | 13 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/enclose.js` | `86fa100f` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/lib/enclose.js` | `21b862fd` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/lib/input/tex/enclose/EncloseConfiguration.js` | `3c23c4f1` | 6 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/enclose/webpack.config.js` | `cfed1548` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/extpfeil.js` | `71caae3a` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/lib/extpfeil.js` | `afe754c6` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/lib/input/tex/extpfeil/ExtpfeilConfiguration.js` | `4532d5c5` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/extpfeil/webpack.config.js` | `d934528e` | 14 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/gensymb.js` | `c26bb8b3` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/lib/gensymb.js` | `f60d8274` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/lib/input/tex/gensymb/GensymbConfiguration.js` | `6b9784b2` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/gensymb/webpack.config.js` | `2d2df676` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/html.js` | `18794b72` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/lib/html.js` | `332b4005` | 21 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/lib/input/tex/html/HtmlConfiguration.js` | `52083647` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/lib/input/tex/html/HtmlMethods.js` | `46faf973` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/html/webpack.config.js` | `10c9ef6a` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsConfiguration.js` | `f1608e36` | 6 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsItems.js` | `635275a5` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsMethods.js` | `fbf8c110` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsTags.js` | `b90c49f0` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/input/tex/mathtools/MathtoolsUtil.js` | `84a6317e` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/lib/mathtools.js` | `54b5d8de` | 27 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/mathtools.js` | `f9b9ef9b` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mathtools/webpack.config.js` | `a63738a9` | 14 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/lib/input/tex/mhchem/MhchemConfiguration.js` | `c545ae45` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/lib/mhchem.js` | `e9218efe` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/mhchem.js` | `001b29f7` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/mhchem/webpack.config.js` | `1229f41e` | 13 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandConfiguration.js` | `604229c0` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandItems.js` | `c7851ae4` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandMethods.js` | `3e5e61c1` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/input/tex/newcommand/NewcommandUtil.js` | `ce409b91` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/lib/newcommand.js` | `903ef7bf` | 25 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/newcommand.js` | `d05e61f2` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/newcommand/webpack.config.js` | `db1dbed3` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/lib/input/tex/noerrors/NoErrorsConfiguration.js` | `59da9a6b` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/lib/noerrors.js` | `b65ad9e2` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/noerrors.js` | `a05d1375` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noerrors/webpack.config.js` | `00ccc77f` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/lib/input/tex/noundefined/NoUndefinedConfiguration.js` | `e821d99f` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/lib/noundefined.js` | `d88a290a` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/noundefined.js` | `814e4c21` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/noundefined/webpack.config.js` | `590d3693` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/input/tex/physics/PhysicsConfiguration.js` | `4873135b` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/input/tex/physics/PhysicsItems.js` | `11a9b070` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/input/tex/physics/PhysicsMethods.js` | `9aeb2d03` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/lib/physics.js` | `872b69a5` | 23 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/physics.js` | `fb8232bf` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/physics/webpack.config.js` | `3f216997` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/lib/input/tex/require/RequireConfiguration.js` | `a9df68e1` | 7 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/lib/require.js` | `38d2025a` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/require.js` | `81d8fbf5` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/require/webpack.config.js` | `ceb55afc` | 13 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/lib/input/tex/setoptions/SetOptionsConfiguration.js` | `8aa2252a` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/lib/setoptions.js` | `eb142bad` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/setoptions.js` | `9e726df4` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/setoptions/webpack.config.js` | `b5f4b551` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/lib/input/tex/tagformat/TagFormatConfiguration.js` | `a7071acf` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/lib/tagformat.js` | `13576a86` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/tagformat.js` | `9f2cf7d5` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/tagformat/webpack.config.js` | `74132ece` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/lib/input/tex/textcomp/TextcompConfiguration.js` | `ef558e80` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/lib/textcomp.js` | `aa2e75f4` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/textcomp.js` | `b4ae2b73` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textcomp/webpack.config.js` | `43cf9ebc` | 13 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/input/tex/textmacros/TextMacrosConfiguration.js` | `c176700e` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/input/tex/textmacros/TextMacrosMethods.js` | `a56cf33d` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/input/tex/textmacros/TextParser.js` | `92929842` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/lib/textmacros.js` | `e65b6efa` | 23 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/textmacros.js` | `d72ab0cf` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/textmacros/webpack.config.js` | `be809911` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/lib/input/tex/unicode/UnicodeConfiguration.js` | `7b31d0c3` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/lib/unicode.js` | `f24bb86d` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/unicode.js` | `2be66cff` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/unicode/webpack.config.js` | `8cf0fc77` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/lib/input/tex/upgreek/UpgreekConfiguration.js` | `c83c9151` | 4 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/lib/upgreek.js` | `ebeda031` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/upgreek.js` | `f3e29bd0` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/upgreek/webpack.config.js` | `71244a81` | 12 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/lib/input/tex/verb/VerbConfiguration.js` | `39bd80a8` | 5 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/lib/verb.js` | `408ed06a` | 19 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/verb.js` | `f6473a31` | 2 |
| `frontend/node_modules/mathjax-full/components/src/input/tex/extensions/verb/webpack.config.js` | `574ae1e7` | 12 |
| `frontend/node_modules/mathjax-full/es5/input/mml/extensions/mml3.js` | `bd10514b` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/action.js` | `82f38dc5` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/all-packages.js` | `441050e5` | 34 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/ams.js` | `1bc2af18` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/amscd.js` | `255cca7d` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/autoload.js` | `9e5e62bc` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/bbox.js` | `f459b9ce` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/boldsymbol.js` | `d760e63e` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/braket.js` | `ec3ac028` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/bussproofs.js` | `f3adca1c` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/cancel.js` | `f58274c9` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/cases.js` | `f3e7ea5c` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/centernot.js` | `c355de00` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/color.js` | `01fa7bdb` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/colortbl.js` | `73321697` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/colorv2.js` | `e57003d4` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/configmacros.js` | `2293a193` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/empheq.js` | `646f560f` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/enclose.js` | `cdc7b8ab` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/extpfeil.js` | `1c400bd6` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/gensymb.js` | `753faef0` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/html.js` | `55035b2d` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/mathtools.js` | `6a8c3c09` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/mhchem.js` | `a9146aa6` | 34 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/newcommand.js` | `831e3679` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/noerrors.js` | `306ed70d` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/noundefined.js` | `60305544` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/physics.js` | `34ffa3cc` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/require.js` | `ddffe3c9` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/setoptions.js` | `422038bb` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/tagformat.js` | `d4442e62` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/textcomp.js` | `28742f11` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/textmacros.js` | `25e1a713` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/unicode.js` | `c95abb61` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/upgreek.js` | `05380fb5` | 1 |
| `frontend/node_modules/mathjax-full/es5/input/tex/extensions/verb.js` | `51168d18` | 1 |
| `frontend/node_modules/mhchemparser/test/test-dist.html` | `6f919f15` | 212 |
| `frontend/node_modules/mhchemparser/test/test-esm.html` | `e8603004` | 209 |
| `frontend/node_modules/tslib/tslib.es6.html` | `5b9030be` | 1 |
| `frontend/node_modules/tslib/tslib.html` | `442aa09e` | 1 |
| `frontend/node_modules/xss/dist/test.html` | `5cdff124` | 15 |
| `frontend/public/admin/admin.html` | `24d52e08` | 308 |
| `frontend/public/second-self/index.html` | `41bf7996` | 826 |
| `frontend/test-markdown.html` | `a9a78eef` | 78 |
| `project-memory/ui/study-hub-dashboard-style-refresh.html` | `11886b9a` | 4370 |
| `project-memory/ui/test-write.html` | `906f0f48` | 1 |
| `project-memory/ui/横屏工作台Dashboard-低保真线框图-完整版.html` | `27a0d077` | 3535 |
| `project-memory/ui/横屏工作台Dashboard-低保真线框图.html` | `724cad11` | 2750 |
| `project-memory/ui/横屏工作台Dashboard-高保真框架图-完整版.html` | `378440ad` | 252 |
| `second-self.bak/app/index.html` | `46e14569` | 80 |
| `second-self/app/index.html` | `afa2b0c6` | 870 |
| `venv/Lib/site-packages/anyio/_backends/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/anyio/_backends/_asyncio.py` | `3e6d66d1` | 2997 |
| `venv/Lib/site-packages/anyio/_backends/_trio.py` | `b0f88f54` | 1344 |
| `venv/Lib/site-packages/cffi/backend_ctypes.py` | `cd7c9df7` | 1122 |
| `venv/Lib/site-packages/cryptography/hazmat/backends/__init__.py` | `39f4fc71` | 14 |
| `venv/Lib/site-packages/cryptography/hazmat/backends/openssl/__init__.py` | `a603d3fa` | 10 |
| `venv/Lib/site-packages/cryptography/hazmat/backends/openssl/backend.py` | `dbbff65f` | 313 |
| `venv/Lib/site-packages/google/api/backend_pb2.py` | `bdeac803` | 61 |
| `venv/Lib/site-packages/httpcore/_backends/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/httpcore/_backends/anyio.py` | `72a339f3` | 147 |
| `venv/Lib/site-packages/httpcore/_backends/auto.py` | `b05af13f` | 53 |
| `venv/Lib/site-packages/httpcore/_backends/base.py` | `52468c26` | 102 |
| `venv/Lib/site-packages/httpcore/_backends/mock.py` | `a391c8c5` | 144 |
| `venv/Lib/site-packages/httpcore/_backends/sync.py` | `e9c9e471` | 242 |
| `venv/Lib/site-packages/httpcore/_backends/trio.py` | `61ca6be4` | 160 |
| `venv/Lib/site-packages/joblib/_parallel_backends.py` | `e366130d` | 754 |
| `venv/Lib/site-packages/joblib/_store_backends.py` | `cb397720` | 501 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/__init__.py` | `ba53d800` | 15 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/_posix_reduction.py` | `f5c09720` | 68 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/_win_reduction.py` | `3cf710bd` | 19 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/context.py` | `3a12bca1` | 406 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/fork_exec.py` | `a34f0c14` | 74 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/popen_loky_posix.py` | `70497e68` | 194 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/popen_loky_win32.py` | `95f022ce` | 174 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/process.py` | `eb9858b9` | 86 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/queues.py` | `2a76957d` | 237 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/reduction.py` | `ddc0e653` | 224 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/resource_tracker.py` | `091a7e66` | 412 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/spawn.py` | `bf72b471` | 245 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/synchronize.py` | `a59cb6d9` | 410 |
| `venv/Lib/site-packages/joblib/externals/loky/backend/utils.py` | `2c81fdc6` | 182 |
| `venv/Lib/site-packages/joblib/test/test_store_backends.py` | `5280f57f` | 95 |
| `venv/Lib/site-packages/kubernetes/client/models/v1_ingress_backend.py` | `9b0c295d` | 147 |
| `venv/Lib/site-packages/kubernetes/client/models/v1_ingress_service_backend.py` | `c3f4dd2e` | 150 |
| `venv/Lib/site-packages/kubernetes/client/models/v1_service_backend_port.py` | `ec840995` | 151 |
| `venv/Lib/site-packages/mpmath/libmp/backend.py` | `0bd76a93` | 116 |
| `venv/Lib/site-packages/networkx/utils/backends.py` | `e4dbab09` | 2172 |
| `venv/Lib/site-packages/networkx/utils/tests/test_backends.py` | `13189970` | 226 |
| `venv/Lib/site-packages/numpy/f2py/_backends/__init__.py` | `f997c7e4` | 10 |
| `venv/Lib/site-packages/numpy/f2py/_backends/_backend.py` | `2265fe07` | 45 |
| `venv/Lib/site-packages/numpy/f2py/_backends/_distutils.py` | `5fcd0704` | 77 |
| `venv/Lib/site-packages/numpy/f2py/_backends/_meson.py` | `20609d60` | 245 |
| `venv/Lib/site-packages/oauthlib/oauth2/rfc6749/clients/backend_application.py` | `27a16902` | 75 |
| `venv/Lib/site-packages/onnxruntime/backend/__init__.py` | `e9e32b4c` | 7 |
| `venv/Lib/site-packages/onnxruntime/backend/backend.py` | `97f21598` | 215 |
| `venv/Lib/site-packages/onnxruntime/backend/backend_rep.py` | `71f16c36` | 77 |
| `venv/Lib/site-packages/scipy/_lib/_uarray/_backend.py` | `97b5270b` | 708 |
| `venv/Lib/site-packages/scipy/_lib/array_api_extra/_lib/_backends.py` | `5efb4c85` | 73 |
| `venv/Lib/site-packages/scipy/fft/_backend.py` | `fcb13503` | 202 |
| `venv/Lib/site-packages/scipy/fft/_basic_backend.py` | `24e664a1` | 198 |
| `venv/Lib/site-packages/scipy/fft/_debug_backends.py` | `81fc088f` | 23 |
| `venv/Lib/site-packages/scipy/fft/_fftlog_backend.py` | `cc6855c3` | 202 |
| `venv/Lib/site-packages/scipy/fft/_realtransforms_backend.py` | `08f8e534` | 64 |
| `venv/Lib/site-packages/scipy/fft/tests/mock_backend.py` | `e6fe63c9` | 97 |
| `venv/Lib/site-packages/scipy/fft/tests/test_backend.py` | `ad94be5c` | 99 |
| `venv/Lib/site-packages/scipy/ndimage/_support_alternative_backends.py` | `d4506fc4` | 121 |
| `venv/Lib/site-packages/scipy/signal/_support_alternative_backends.py` | `20333810` | 389 |
| `venv/Lib/site-packages/scipy/special/_support_alternative_backends.py` | `6198f69c` | 877 |
| `venv/Lib/site-packages/scipy/special/tests/test_support_alternative_backends.py` | `04d512dc` | 403 |
| `venv/Lib/site-packages/sentence_transformers/backend/__init__.py` | `83afc80e` | 19 |
| `venv/Lib/site-packages/sentence_transformers/backend/load.py` | `33012634` | 176 |
| `venv/Lib/site-packages/sentence_transformers/backend/optimize.py` | `d22074e3` | 104 |
| `venv/Lib/site-packages/sentence_transformers/backend/quantize.py` | `0e4a20d6` | 219 |
| `venv/Lib/site-packages/sentence_transformers/backend/utils.py` | `60b66e82` | 336 |
| `venv/Lib/site-packages/setuptools/tests/indexes/test_links_priority/external.html` | `efaf4d8f` | 4 |
| `venv/Lib/site-packages/setuptools/tests/indexes/test_links_priority/simple/foobar/index.html` | `8f6c3844` | 5 |
| `venv/Lib/site-packages/sklearn/externals/array_api_extra/_lib/_backends.py` | `5efb4c85` | 73 |
| `venv/Lib/site-packages/sympy/core/backend.py` | `ccd87e51` | 121 |
| `venv/Lib/site-packages/sympy/plotting/backends/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/sympy/plotting/backends/base_backend.py` | `689c1972` | 420 |
| `venv/Lib/site-packages/sympy/plotting/backends/matplotlibbackend/__init__.py` | `4b9c7bc6` | 6 |
| `venv/Lib/site-packages/sympy/plotting/backends/matplotlibbackend/matplotlib.py` | `dc4ad936` | 319 |
| `venv/Lib/site-packages/sympy/plotting/backends/textbackend/__init__.py` | `79851d3a` | 4 |
| `venv/Lib/site-packages/sympy/plotting/backends/textbackend/text.py` | `f890440a` | 25 |
| `venv/Lib/site-packages/torch/_dynamo/backends/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/torch/_dynamo/backends/common.py` | `6e33c082` | 185 |
| `venv/Lib/site-packages/torch/_dynamo/backends/cudagraphs.py` | `7b41b098` | 300 |
| `venv/Lib/site-packages/torch/_dynamo/backends/debugging.py` | `cf7c9272` | 731 |
| `venv/Lib/site-packages/torch/_dynamo/backends/distributed.py` | `a7db701f` | 623 |
| `venv/Lib/site-packages/torch/_dynamo/backends/inductor.py` | `f3471f67` | 32 |
| `venv/Lib/site-packages/torch/_dynamo/backends/onnxrt.py` | `79844394` | 40 |
| `venv/Lib/site-packages/torch/_dynamo/backends/registry.py` | `a7b98da7` | 207 |
| `venv/Lib/site-packages/torch/_dynamo/backends/tensorrt.py` | `5398a0cb` | 13 |
| `venv/Lib/site-packages/torch/_dynamo/backends/torchxla.py` | `2ce3fef6` | 56 |
| `venv/Lib/site-packages/torch/_dynamo/backends/tvm.py` | `0862ad4b` | 198 |
| `venv/Lib/site-packages/torch/_lazy/ts_backend.py` | `da403d10` | 8 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/__init__.py` | `397fb614` | 31 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/_common_operator_config_utils.py` | `52f0771b` | 783 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/_qnnpack_pt2e.py` | `44547492` | 182 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/backend_config.py` | `ee90b4b8` | 752 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/executorch.py` | `2d900bc4` | 499 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/fbgemm.py` | `5e90f10f` | 130 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/native.py` | `a26e397a` | 232 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/onednn.py` | `53d0b5ac` | 642 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/qnnpack.py` | `d7087e8d` | 172 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/tensorrt.py` | `1d5d1504` | 99 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/utils.py` | `5a8d90b0` | 322 |
| `venv/Lib/site-packages/torch/ao/quantization/backend_config/x86.py` | `0acf0407` | 127 |
| `venv/Lib/site-packages/torch/ao/quantization/fx/_lower_to_native_backend.py` | `caabba3d` | 1414 |
| `venv/Lib/site-packages/torch/backends/__init__.py` | `d277e543` | 141 |
| `venv/Lib/site-packages/torch/backends/_coreml/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/torch/backends/_coreml/preprocess.py` | `92f337ef` | 155 |
| `venv/Lib/site-packages/torch/backends/_nnapi/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/torch/backends/_nnapi/prepare.py` | `8f72aaac` | 209 |
| `venv/Lib/site-packages/torch/backends/_nnapi/serializer.py` | `01a254d3` | 2647 |
| `venv/Lib/site-packages/torch/backends/cpu/__init__.py` | `c062e03a` | 22 |
| `venv/Lib/site-packages/torch/backends/cuda/__init__.py` | `9547fcac` | 606 |
| `venv/Lib/site-packages/torch/backends/cudnn/__init__.py` | `d5b682d0` | 251 |
| `venv/Lib/site-packages/torch/backends/cudnn/rnn.py` | `0c7bb38f` | 129 |
| `venv/Lib/site-packages/torch/backends/cusparselt/__init__.py` | `be14807f` | 58 |
| `venv/Lib/site-packages/torch/backends/kleidiai/__init__.py` | `35fbe706` | 8 |
| `venv/Lib/site-packages/torch/backends/mha/__init__.py` | `7e186e04` | 26 |
| `venv/Lib/site-packages/torch/backends/miopen/__init__.py` | `0dff595d` | 51 |
| `venv/Lib/site-packages/torch/backends/mkl/__init__.py` | `60fa97e1` | 60 |
| `venv/Lib/site-packages/torch/backends/mkldnn/__init__.py` | `67e84968` | 140 |
| `venv/Lib/site-packages/torch/backends/mps/__init__.py` | `d5ed5c55` | 79 |
| `venv/Lib/site-packages/torch/backends/nnpack/__init__.py` | `d1347450` | 33 |
| `venv/Lib/site-packages/torch/backends/openmp/__init__.py` | `dfbbc200` | 8 |
| `venv/Lib/site-packages/torch/backends/opt_einsum/__init__.py` | `8f6c243b` | 118 |
| `venv/Lib/site-packages/torch/backends/python_native/__init__.py` | `4f96323c` | 388 |
| `venv/Lib/site-packages/torch/backends/quantized/__init__.py` | `128469e0` | 66 |
| `venv/Lib/site-packages/torch/backends/xeon/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/torch/backends/xeon/run_cpu.py` | `c081a159` | 958 |
| `venv/Lib/site-packages/torch/backends/xnnpack/__init__.py` | `5e560078` | 30 |
| `venv/Lib/site-packages/torch/distributed/elastic/rendezvous/c10d_rendezvous_backend.py` | `2dfbbf65` | 271 |
| `venv/Lib/site-packages/torch/distributed/elastic/rendezvous/etcd_rendezvous_backend.py` | `853bf480` | 215 |
| `venv/Lib/site-packages/torch/distributed/rpc/_testing/faulty_agent_backend_registry.py` | `3f947e6a` | 63 |
| `venv/Lib/site-packages/torch/distributed/rpc/backend_registry.py` | `910fe563` | 433 |
| `venv/Lib/site-packages/torch/fx/passes/backends/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/torch/fx/passes/backends/cudagraphs.py` | `7fa5a017` | 62 |
| `venv/Lib/site-packages/torch/nativert/backends/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/torch/nativert/backends/_lower_utils.py` | `063de6f5` | 105 |
| `venv/Lib/site-packages/torch/nativert/backends/_lowered_aoti_module.py` | `e7360965` | 32 |
| `venv/Lib/site-packages/torch/nn/backends/__init__.py` | `d41d8cd9` | 1 |
| `venv/Lib/site-packages/torch/nn/backends/thnn.py` | `232f0f26` | 7 |
| `venv/Lib/site-packages/torch/utils/backend_registration.py` | `6717942e` | 521 |
| `venv/Lib/site-packages/torch/utils/model_dump/skeleton.html` | `3c3e9f41` | 22 |
| `venv/Lib/site-packages/torchgen/gen_backend_stubs.py` | `1a523de5` | 636 |
| `venv/Lib/site-packages/transformers/image_processing_backends.py` | `86545b99` | 690 |
| `xiaohongshu-mcp-server/xiaohongshu_mcp_server/__init__.py` | `f2838c63` | 9 |
| `xiaohongshu-mcp-server/xiaohongshu_mcp_server/__main__.py` | `561aa71b` | 8 |
| `xiaohongshu-mcp-server/xiaohongshu_mcp_server/server.py` | `a5459c88` | 608 |

<!-- 文件总数: 438, 生成时间: 2026-06-07 01:10 UTC -->
<!-- AUTO-GENERATED-END -->
