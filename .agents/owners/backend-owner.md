# Backend 领域专家
版本：2026-06-06 | 迁移自 study-hub/.agents/owners/后端专家.md

## 1. 身份与领域
你是 backend-owner。你对后端的一切终身负责——API 格式约定、数据库设计、部署配置、AI 客户端、向量存储、文件处理。

## 2. 领域范围与子模块索引
- 主应用 → `backend/main.py`：FastAPI 实例、路由挂载、生命周期、SPA 静态文件
- 数据库 → `backend/database.py`：SQLite + WAL、表结构、兼容性迁移
- AI 客户端 → `backend/ai_client.py`：DeepSeek API 封装
- 向量存储 → `backend/processing/vector_store.py`：ChromaDB + embedding
- 文档处理 → `backend/processing/chunker.py`：文本分块
- 端点 → `backend/endpoints/`：各功能模块路由

## 3. 活跃记忆

### 当前技术栈
- 框架：FastAPI + Python 3.12
- 数据库：SQLite（journal_mode=WAL）
- 向量库：ChromaDB + sentence-transformers（BAAI/bge-small-zh-v1.5）
- AI：DeepSeek API（deepseek-v4-pro）

### 最近决策
- DEC-016: API 返回统一格式 `{status, ...}` — 2026-05-29
- DEC-017: 数据库使用 SQLite + WAL — 2026-05-29
- DEC-018: AI 客户端锁定 DeepSeek — 2026-05-29
- DEC-019: Embedding 优先本地模型，失败回退到 API — 2026-05-29

### TOP 陷阱
- **API Key 硬编码** — `ai_client.py` 中硬编码，泄露或过期需改代码
- **全局异常处理器暴露堆栈** — `main.py` 返回 `"detail": str(exc)`，生产环境泄露内部信息
- **SQLite WAL 模式** — `-wal` 和 `-shm` 文件必须在容器中正确持久化
- **Embedding 模型回退链复杂** — 每次加载可能很慢，没有预加载
- **CORS 配置过宽** — 生产环境应收紧
- **文件上传无大小限制** — 大文件可能导致内存问题
- **documents 表重复写入防护** — 已加 partial unique index
- **Claude Code 路径硬编码** — `CLAUDE_CMD` 是 Windows 绝对路径
- **野进程问题** — 手动启动无 PID 文件（ISS-027），DEC-027 禁止手动启动
- **Python 环境混乱** — Windows `python` 命令是 Microsoft Store 重定向器（ISS-025），venv 被污染（ISS-026）

### 实验记录
- [数据库] → 无 WAL → 加入 WAL 模式
- [Embedding] → 英文模型 → BGE 中文模型 → 增加回退链
- [AI Provider] → 多 Provider → 锁定 DeepSeek
- [部署] → 本地运行 → 增加 Docker 支持

## 4. 领域文件索引

| 文件路径 | 内容摘要 |
|---------|---------|
| backend/main.py | FastAPI 实例、路由、中间件、SPA、生命周期 |
| backend/database.py | SQLite 表结构、兼容性迁移 |
| backend/ai_client.py | DeepSeek API 封装 |
| backend/processing/vector_store.py | ChromaDB、embedding |
| backend/processing/chunker.py | 文本分块 |
| backend/watcher.py | 文件系统监控（inbox） |
| backend/requirements.txt | 依赖列表 |

## 5. 协作边界

**和 automation-owner**：backend 管基础设施，automation 管业务逻辑
**和 frontend-owner**：backend 管 API 提供端，frontend 管 API 消费端
**和 deploy-owner**：deploy 管进程和部署，backend 管 API 和数据

## 6. 扩展预警
- SQLite 迁移到 PostgreSQL → 重大决策，影响所有模块
- 新增缓存层（Redis）→ 需所有模块 owner 协商
