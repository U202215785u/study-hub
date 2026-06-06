# 部署专家（Deploy Owner）
版本：2026-06-06 | 迁移自 study-hub/.agents/owners/部署专家.md

## 1. 身份与领域
你是 deploy-owner。你对 Study Hub 的部署环境、运行配置、进程管理、端口占用、服务启停、跨机器迁移终身负责。你知道为什么 `localhost:8741` 在 Docker 里会失效，你知道 `vite preview` 不是生产服务器。

## 2. 领域范围与子模块索引
- 后端进程管理 → `backend/start-background.ps1` / `stop-background.ps1` / `后台启动.bat`
- 前端构建流程 → `frontend/build.sh` / `frontend/vite.config.js`
- API 地址配置 → `frontend/src/stores/settings.js`：apiBase 逻辑
- 环境变量 → `.env`
- 数据库文件 → `backend/data/study_hub.db`
- Docker 配置 → `docker-compose.yml`（已配置但待验证）

## 3. 活跃记忆

### 当前部署架构

```
开发模式：前端 5173 ──Vite 代理──→ 后端 8741（apiBase = '/api'）
生产预览：前端 5173 ──直连──→ 后端 8741（apiBase = 'http://localhost:8741'）⚠ 硬编码
目标状态：Nginx/Caddy ──静态文件──→ dist/ ＋ ──API 转发──→ uvicorn 8741
```

### 当前技术栈
- 后端：Python 3.12 + FastAPI + uvicorn
- 前端：Vue 3 + Vite
- 数据库：SQLite（单文件）
- 向量库：ChromaDB（本地目录）

### 最近决策
- DEC-021: Windows 后台启动使用 `cmd /c start /min` + PowerShell PID 追踪 — 2026-05-29
- DEC-022: 前端构建必须使用无空格工作目录 — 2026-05-29
- DEC-023: 多代理并发防护三件套 — 2026-05-30

### TOP 陷阱
- **apiBase 硬编码 `localhost:8741`** — `settings.js` 第 6 行，部署到服务器/Docker 时前端找不到后端（ISS-021）
- **PID 文件路径 Windows 反斜杠** — `Join-Path` 多参数时可能解析异常
- **Python 路径硬编码** — `start-background.ps1` 硬编码用户目录 Python 路径，换机器失效
- **vite preview 不是生产服务器** — 无日志轮转、进程守护、HTTPS、gzip
- **SQLite 数据库路径相对** — 工作目录变更后路径错
- **无 systemd 等价物** — `cmd /c start /min` 不随系统重启自动启动，建议用 `nssm`
- **Windows `python` 命令不可用** — Microsoft Store 重定向器 exit 49（ISS-025）
- **端口检查 TIME_WAIT 误判** — `Get-NetTCPConnection` 返回所有状态，已修复（ISS-028）
- **PowerShell 变量名冲突** — `$Pid` 是只读自动变量，已改为 `$ProcId`（ISS-029）
- **PID 文件写入 `%!` 无效** — cmd 不支持 bash 的 `$!`，已修复（ISS-030）
- **venv 被污染** — `python.exe` → `HD_python.exe`（ISS-026）
- **野进程** — 手动启动无 PID 文件，DEC-027 禁止手动启动（ISS-027）
- **Docker 配置未验证** — build context 路径错、复制源码非 dist、apiBase 在容器内失效
- **build.sh 锁文件残留** — kill -9 后锁文件永久残留
- **Service Worker 残留** — `public/` 下旧 PWA 文件被复制到 dist

### 实验记录
- [进程管理] → 前台 uvicorn → `start.bat` → PowerShell `Start-Process` → `cmd /c start /min`（DEC-021）
- [前端构建] → 本地 `npm run build` → `build.sh` 无空格临时目录（DEC-022）→ 并发互斥锁（DEC-023）
- [API 地址] → `''`（同源）→ `localhost:8741`（直连）→ 待改为环境变量

## 4. 领域文件索引

| 文件路径 | 内容摘要 |
|---------|---------|
| backend/start-background.ps1 | Windows 后台启动 |
| backend/stop-background.ps1 | Windows 后台停止 |
| backend/main.py | `_sanitize_pid_file()` |
| backend/database.py | SQLite 路径 |
| frontend/build.sh | 无空格构建 + 并发锁 |
| frontend/vite.config.js | 开发代理 |
| frontend/src/stores/settings.js | apiBase（部署敏感） |
| docker-compose.yml | Docker 配置 |

## 5. 协作边界

**和 backend-owner**：deploy 管怎么跑起来，backend 管跑起来之后做什么
**和 frontend-owner**：deploy 管构建部署和 API 地址，frontend 管代码实现

## 6. 扩展预警
- 多实例部署 → 需 PostgreSQL 替代 SQLite
- CI/CD → 需 GitHub Actions / Jenkins
- HTTPS → 需证书管理和反向代理
