# Second Self — 第二个我

> 本地优先的个人 AI 分身系统。基于 Markdown 文件 + SQLite 记忆 + LLM 决策管道。

---

## 快速启动

```bash
# 1. 安装依赖（仅 LLM 对话需要）
pip install openai

# 2. 配置 API Key（三选一）
export OPENAI_API_KEY="sk-..."
# 或 export DASHSCOPE_API_KEY="..."
# 或 export GRSAI_API_KEY="..."

# 3. 启动服务
python server.py
# → http://localhost:8420
```

---

## 核心架构

```
second-self/
├── app/                    # 前端界面 (index.html)
├── os_layer/               # OS 操作扩展（对标 OpenClaw）
│   ├── safety_guard.py     # 安全守卫 (SAFE/RISKY/DANGEROUS)
│   ├── shell_executor.py   # Shell 命令执行
│   ├── fs_operator.py      # 文件系统操作
│   ├── browser_controller.py # 浏览器控制
│   ├── skill_registry.py   # 技能注册系统
│   └── gateway.py          # 统一执行入口
├── skills/                 # 可扩展技能目录
│   ├── shell-helper/
│   └── file-helper/
├── .memory/                # SQLite 记忆数据库
├── ME.md                   # 个人上下文
├── DASHBOARD.md            # 活跃仪表盘
├── PRINCIPLES.md           # 决策原则
├── AUTONOMY.md             # 五级授权边界
└── server.py               # HTTP API 服务
```

---

## 决策管道 (Self Engine)

每条消息经过 4 个阶段：

1. **加载 Self 层** — 读取 ME.md + DASHBOARD.md
2. **检索记忆** — 构建记忆场 (Memory Field)
3. **决策引擎** — 优先级 / 反模式 / 原则匹配 / 权限判断 / OS 意图检测
4. **生成回复** — 调用 LLM（OpenAI / DashScope / GRSAI 自动回退）

---

## OS Layer 能力

| 能力 | API Action | 权限 |
|------|-----------|------|
| 执行 Shell | `shell.execute` | SAFE 自动 / RISKY 需确认 |
| 读文件 | `fs.read` | L2 自动 |
| 写文件 | `fs.write` | L1 需确认 |
| 列目录 | `fs.list` | L2 自动 |
| 搜索内容 | `fs.search` | L2 自动 |
| 删除文件 | `fs.delete` | L1 需确认 |
| 网页导航 | `browser.navigate` | L1 需确认 |
| 提取内容 | `browser.extract` | L2 自动 |
| 网页截图 | `browser.screenshot` | L1 需确认 |
| 执行技能 | `skill.execute` | 按技能声明 |
| 列出技能 | `skill.list` | L2 自动 |

**安全模型**：对标 OpenClaw Hardstop — 命令分级、路径黑名单、审计日志。

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/self` | Self 层快照 |
| GET  | `/api/files` | 核心文件列表 |
| GET  | `/api/memory/stats` | 记忆统计 |
| POST | `/api/decide` | 决策分析 |
| POST | `/api/chat` | 完整对话 |
| POST | `/api/chat/stream` | 流式对话 |
| POST | `/api/file?path=...` | 读写文件 |
| POST | `/api/lint` | 运行 Lint |
| POST | `/api/ingest` | 内容导入 |
| POST | `/api/os/execute` | **OS 操作执行** |
| GET  | `/api/os/skills` | **列出 OS 技能** |

---

## 开发 Skill

在 `skills/<skill-name>/` 下创建：

```yaml
---
name: my-skill
description: 一句话描述触发条件
triggers: ["关键词1", "关键词2"]
risk_level: safe          # safe | risky | dangerous
requires_confirmation: false
---
```

可选创建 `run.py`：

```python
def run(args: dict):
    return {"result": "hello"}
```

系统自动发现并注册。

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API |
| `OPENAI_API_BASE` | 自定义 base_url |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope |
| `GRSAI_API_KEY` | GRSAI Nano Banana |
| `SECOND_SELF_PORT` | 服务端口号（默认 8420）|

---

## 技术栈

- **后端**：Python 3.12 + 标准库 HTTP Server（零框架依赖）
- **数据库**：SQLite（记忆存储）
- **LLM**：OpenAI 兼容 API（多 Provider 自动回退）
- **前端**：原生 HTML/JS（无构建步骤）
- **OS 扩展**：Playwright（可选，用于浏览器截图）
