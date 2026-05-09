# CLAUDE.md — 学习中枢 Study Hub

> 参照 Karpathy 编码哲学，为 LLM 编程建立约束边界。

---

## 四条核心原则

### 1. 编码前先思考

- **说出假设**：不确定就问，不要默默猜测。歧义存在时列出所有选项，不要悄悄选一个。
- **主动简化**：如果用户的方案过度复杂，直接说"有更简单的做法"，给出更少代码的方案。
- **遇到困惑就停**：说出哪里不清楚，而不是硬着头皮写可能错误的东西。

### 2. 简洁优先

- 不加没被要求的功能、抽象、配置项、"灵活性"
- 不为不可能发生的场景写错误处理
- 如果可以 200 行缩成 50 行，就重写
- 自检：**一个资深工程师会不会说这太复杂了？** 如果是，简化。

### 3. 外科手术式修改

- 只改必须改的，不要顺手改进相邻代码
- 匹配现有风格，即使你不喜欢
- 发现死代码提一句，但别删（除非被明确要求）
- 移除你的改动造成的孤儿代码（无用 import / 变量 / 函数）

### 4. 目标驱动执行

- 模糊任务转化为可验证目标："修 bug" → "用测试复现，然后修复"
- 多步任务先列计划，每步带验证点
- 改完就跑测试 / 服务验证，确认通过再报告完成

---

## 项目架构不可变约束

### AI 服务 — DeepSeek 唯一，不可切换

```python
# backend/ai_client.py — 不可变
API_KEY = "sk-d703daaf15d343b88dce53a1dd4d32e4"
API_BASE = "https://api.deepseek.com/v1"
MODEL = "deepseek-v4-pro"
```

- **唯一 Provider：DeepSeek**，禁止引入其他 AI 服务（Kimi/Claude/豆包等）
- API Key **硬编码死值**，禁止改为环境变量、配置文件、或任何可配置形式
- `api_base` 和 `model` 可通过环境变量覆盖，但 Key 不行
- 禁止新增 `provider` 参数或任何 Provider 选择逻辑

### 数据库 — 不可变

- **SQLite 路径**: `backend/data/study_hub.db`
- **ChromaDB 路径**: `backend/data/chroma_db/`
- 禁止更换数据库引擎（不引入 PostgreSQL / MySQL / MongoDB 等）
- 表结构变更必须向后兼容（添加列允许，删除列 / 重命名列禁止）
- 所有迁移通过 `database.py` 中的 `CREATE TABLE IF NOT EXISTS` 自动完成

---

## 架构边界（减少耦合）

### 三层分离

```
endpoints/   ← HTTP 层：只做参数校验、调用 processing、返回响应
processing/  ← 业务层：纯函数，不 import FastAPI，不访问 HTTP 上下文
backend/     ← 核心层：ai_client / database / watcher，不依赖 endpoints
```

### 硬规定

- **endpoints 禁止直接操作 SQLite**：所有数据库操作通过 `database.py` 导出的函数
- **endpoints 禁止直接操作 ChromaDB**：所有向量操作通过 `processing/vector_store.py` 的 `VectorStore` 类
- **processing 禁止 import FastAPI**：`from fastapi import ...` 不得出现在 processing 目录下
- **前端与后端仅通过 HTTP API 通信**：不得在前端 JS 中直接读写文件系统或数据库
- **MCP Server 仅做代理**：`mcp_server.py` 只转发请求到后端 HTTP API，不包含业务逻辑

### 依赖方向

```
frontend → HTTP → endpoints → processing → ai_client / database / vector_store
                                                    ↑
mcp_server ─── HTTP ────────────────────────────────┘
extension  ─── HTTP ────────────────────────────────┘
```

**禁止反向依赖**：`database.py` 不能 import `endpoints`，`processing` 不能 import `mcp_server`。

---

## 技术栈约束

| 层 | 技术 | 不可变 |
|------|------|------|
| 后端框架 | FastAPI + Uvicorn | 否 |
| 数据库 | SQLite + ChromaDB | 是 |
| 向量模型 | BAAI/bge-small-zh-v1.5 (本地) | 是 |
| AI 服务 | DeepSeek（唯一，不可切换）| 是 |
| API Key | `sk-d703daaf15d343b88dce53a1dd4d32e4` | 是 |
| 前端 | 原生 HTML/JS (无框架) | 否 |
| Chrome 扩展 | Manifest V3 | 否 |
| MCP 协议 | MCP Python SDK | 否 |
| 部署 | Docker Compose | 否 |
| 端口 | 8741 | 否 |

---

## mods/ — 工具百宝箱

`mods/` 是项目级独立工具模块目录，与 study-hub 平级但为独立项目：

```
mods/
├── brainstorm/    # 护眼仪小助手 (Python/PyInstaller)
├── learning/      # Vibe Coding 学习计划 + 清单生成器
└── suit/          # React + TypeScript + Vite 前端套件
```

### 不可变规则

- `mods/` 目录名和位置不可更改
- 三个模块目录结构各自独立，互不依赖
- **`mods/` 已纳入 Git 追踪**，任何 worktree 中都能看到

---

## 项目结构

```
├── study-hub/                     # 主项目
│   ├── backend/
│   │   ├── main.py                # FastAPI 入口 + lifespan
│   │   ├── ai_client.py           # DeepSeek AI 客户端（单例）
│   │   ├── database.py            # SQLite 初始化 + 操作函数
│   │   ├── watcher.py             # Inbox 文件夹监控
│   │   ├── evolution_pipeline.py  # 技能进化分析引擎
│   │   ├── evolution_files.py     # 进化数据 I/O
│   │   ├── endpoints/             # HTTP 路由层
│   │   │   ├── upload.py          #   文档上传 / CRUD
│   │   │   ├── rag.py             #   RAG 知识库查询
│   │   │   ├── review.py          #   每日复盘 / 周报
│   │   │   ├── categories.py      #   分类管理
│   │   │   ├── wiki.py            #   LLM Wiki 编译
│   │   │   ├── evolution.py       #   进化系统 API
│   │   │   ├── automation.py      #   社交媒体自动化
│   │   │   └── ai_search.py       #   AI 网络搜索
│   │   └── processing/            # 业务逻辑层
│   │       ├── processors.py      #   文件类型处理器
│   │       ├── chunker.py         #   文本分块
│   │       └── vector_store.py    #   ChromaDB 向量存储
│   ├── frontend/
│   │   ├── index.html             # 主仪表盘
│   │   ├── kb.html                # 知识库管理
│   │   └── wiki.html              # Wiki 知识图谱
│   ├── extension/                 # Chrome 扩展 (Manifest V3)
│   ├── mcp_server.py              # MCP Server (Claude Desktop)
│   ├── social_parsers.py          # B站/小红书/ASR 解析器
│   └── .env.example
├── mods/                          # 工具百宝箱（独立模块）
│   ├── brainstorm/                 #   护眼仪小助手
│   ├── learning/                   #   学习清单生成器
│   └── suit/                       #   前端套件 (React+Vite)
├── bilibili-mcp-server/           # B站 MCP 独立包
├── xiaohongshu-mcp-server/        # 小红书 MCP 独立包
└── .claude/
    ├── scripts/generate_readme.py  # README 自动生成
    ├── settings.json               # Hooks 配置
    └── skills/                     # Agent Skills
```

---

## 数据流

```
用户上传文档 ─→ upload.py ─→ database.py(SQLite) + vector_store.py(ChromaDB)
                                                              ↓
用户提问 RAG ─→ rag.py ─→ vector_store.query() ─→ ai_client.chat() ─→ 返回
                                                              ↓
Chrome 采对话 ─→ extension/content.js ─→ POST /upload/text ─→ 存储
                                                              ↓
写每日复盘 ─→ review.py ─→ ai_client.chat() ─→ 存储 reviews 表
                                                              ↓
编译 Wiki ─→ wiki.py ─→ 读 documents 表 ─→ ai_client.chat() ─→ wiki_pages 表
                                                              ↓
进化分析 ─→ evolution.py ─→ 对比 wiki + skills ─→ 生成 skill_patches
```

---

## 编码约定

### Python

- 类型注解：函数签名使用，但不过度标注（简单参数可省略）
- 异步：FastAPI 路由用 `async def`，数据库操作用同步（SQLite 不支持异步）
- 全局单例：`ai_client`、`vector_store` 在 `main.py` lifespan 中初始化
- 错误处理：API 路由返回 `{"error": str(e)}`，不抛出未捕获异常

### 前端

- 无框架：原生 JS + 内联 CSS，不引入 React/Vue
- 状态：`localStorage` 存用户配置，API 拉取数据
- Markdown 渲染：CDN 加载 `marked.js`，手动 fallback

### 配置

- 所有配置通过环境变量，默认值硬编码在代码中（`os.getenv("KEY", "default")`）
- `.env.example` 仅列出可配置项，不含真实 Key

---

## 测试与验证

```bash
# 启动服务（注意：必须在 backend/ 目录下运行）
cd study-hub/backend && python main.py

# 运行测试
pytest backend/tests/ -v

# 检查 README 新鲜度
python .claude/scripts/generate_readme.py --check

# 健康检查
curl http://localhost:8741/health

# 验证 DeepSeek 模型可用性
curl -s https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer sk-d703daaf15d343b88dce53a1dd4d32e4" \
  | python -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

---

## 已知坑与预防

### 坑1：Worktree 里 mods/ 消失

**现象**：工具百宝箱的三个模块在 worktree 里看不到。

**原因**：Git worktree 只包含 Git 追踪的文件。`mods/` 必须在 Git 中才能出现在 worktree。

**预防**：`mods/` 已纳入 Git 追踪。新增模块目录后立即 `git add` 并提交。

### 坑2：服务器跑了旧代码

**现象**：改了代码但 401/报错依旧。

**原因**：服务器可能在原始仓库启动的（`study web/study-hub/backend/`），而改动在 worktree 里（`.claude/worktrees/xxx/study-hub/backend/`）。两条路径是不同文件。

**预防**：
- 改代码前先确认服务器是从哪个路径跑的：`netstat -ano | findstr :8741`
- 改完代码后必须重启服务器
- 如果服务器在原始仓库跑，改动也要同步到原始仓库

### 坑3：DeepSeek Model 名过期

**现象**：API Key 正确但返回 401。

**原因**：DeepSeek 升级到 V4 后，旧 model 名 `deepseek-chat` 已废弃。当前有效模型只有 `deepseek-v4-pro` 和 `deepseek-v4-flash`。

**预防**：
- 模型名硬编码在 `ai_client.py`，修改前先用上方验证命令确认模型存在
- 不要在环境变量中随意覆盖 `DEEPSEEK_MODEL`
- DeepSeek 公告模型变更时同步更新硬编码值

### 坑4：AI Key 被环境变量覆盖

**现象**：API Key 不对。

**原因**：旧版代码从 `os.getenv("DEEPSEEK_API_KEY")` 读取 Key，如果 `.env` 文件或系统环境变量有旧 Key 会覆盖。

**预防**：`ai_client.py` 已将 Key 硬编码，不从环境变量读取。禁止恢复 `os.getenv` 方式。

### 坑5：Python 输出中文乱码

**现象**：Windows 终端输出 `\uXXXX` 或乱码。

**预防**：脚本开头加 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`

### 坑6：Worktree 累积过多

**现象**：`.claude/worktrees/` 下有大量旧 worktree（当前 10 个），占磁盘。

**预防**：已完成的工作通过 `/exit-worktree` 退出并清理。定期检查 `ls .claude/worktrees/`。

---

## 注意事项

- **系统编码**：Windows 上输出中文用 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`
- **路径分隔符**：代码中统一用 `/`，不硬编码 `\`
- **ChromaDB 本地模型**：首次启动自动下载 `bge-small-zh-v1.5`，需等待
- **AI 搜索**：使用 DuckDuckGo 免费搜索，不依赖付费 Search API
- **自动化引擎**：抖音用 Claude Code CLI；B站/小红书用原生 API + Qwen ASR
