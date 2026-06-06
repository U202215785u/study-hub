# 学习中枢 Study Hub

> 浏览器新标签页变身学习操作系统 —— 从"我该学什么"到"我学到了什么"形成闭环。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

---

## 这是什么

一个页面聚合你所有的学习工具：AI 搜索、知识库管理、对话采集、每日复盘。AI 对话不再"聊完就丢"，而是自动回流到你的知识库。

**核心功能：**

- 🔍 **智能搜索** — AI 回答 / 知识库语义搜索 / 全网搜索，一个搜索框搞定
- 📚 **RAG 知识库** — 上传文档（txt/md/pdf），AI 基于你的资料回答问题
- 📖 **Wiki 编译** — 原始文档自动编译成结构化 Wiki + 知识图谱 + 学习路径
- 🚀 **AI 启动器** — 一键打开 Claude / ChatGPT / DeepSeek / Kimi / 豆包
- 📝 **每日复盘** — 写笔记 → AI 润色 → 关联知识库 → 自动生成周报
- 🔌 **Chrome 扩展** — AI 网站对话自动采集，回流知识库
- 🧠 **MCP Server** — Claude Desktop 深度集成，对话中直接操作知识库
- ⚡ **自动化引擎** — 粘贴抖音/B站/小红书链接，自动提取文本存入知识库
- 🧬 **技能进化** — 分析知识库内容，自动生成技能改进补丁
- 🛠️ **工具百宝箱 (mods/)** — 护眼仪桌面助手 / 学习计划生成器 / React 前端套件

---

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/U202215785u/study-hub.git
cd study-hub/study-hub

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入任一 AI API Key（DeepSeek / Kimi / Claude / 豆包）

# 3. 一键启动
docker compose up -d

# 4. 打开浏览器
# http://localhost:8741
```

首次 Docker build 约 5-10 分钟（下载依赖和中文 embedding 模型），后续启动秒开。

> 详细文档：[study-hub/README.md](study-hub/README.md)

---

## 浏览器扩展安装

1. 打开 `chrome://extensions`，开启右上角 **开发者模式**
2. 点击 **加载已解压的扩展程序**
3. 选择 `study-hub/extension/` 文件夹
4. 搞定 — 之后在 Claude/ChatGPT/DeepSeek/Kimi/豆包的对话会自动采集

---

## 怎么跑起来的

```
┌─────────────────────────────────────────────────────────┐
│                     浏览器新标签页                        │
│  搜索框 ←→ 常用网站 ←→ AI启动器 ←→ 知识库 ←→ 每日复盘    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                Python 后端 (FastAPI :8741)                │
│  /upload  /rag  /review  /categories  /wiki  /inbox      │
│                                                          │
│  AI Client (Claude / Kimi / DeepSeek / 豆包)             │
│  SQLite (文档/复盘)  +  ChromaDB (向量搜索)               │
└──────┬───────────────────────────────────┬──────────────┘
       │ MCP (Claude Desktop 集成)         │ HTTP
┌──────▼──────────┐              ┌─────────▼──────────────┐
│  MCP Server     │              │  Chrome 扩展             │
│  (Claude 对话中  │              │  (AI网站对话自动采集)    │
│   操作知识库)    │              │                          │
└─────────────────┘              └────────────────────────┘
```

---

## 仓库结构

| 目录 | 说明 |
|------|------|
| `study-hub/` | 主项目：前端 + 后端 + 扩展 + MCP Server |
| `mods/` | 工具百宝箱：护眼仪助手 / 学习计划生成器 / React 前端套件 |
| `bilibili-mcp-server/` | B站 MCP Server（视频信息解析 + 语音识别） |
| `xiaohongshu-mcp-server/` | 小红书 MCP Server（笔记内容提取） |

<!-- AUTO-STATS-START -->

<!-- 自动生成于 2026-05-15 19:29 UTC，请勿手动编辑此区块 -->

## 项目实时概况

| 指标 | 数值 |
|:---|:---|
| 后端 API 端点 | `13` 个 |
| MCP Server 工具 | `27` 个 |
| 前端页面 | `13` 个 |
| 工具百宝箱模块 | `3` 个 |
| Python 代码总行数 | `42,773` 行 |
| 自动文档更新 | `2026-05-15 19:29 UTC` |

📖 [查看完整 API 文档 →](study-hub/README.md)
<!-- AUTO-STATS-END -->

---

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `CLAUDE_API_KEY` | Claude API Key | 至少填一个 |
| `KIMI_API_KEY` | Kimi API Key | 至少填一个 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 至少填一个 |
| `DOUBAO_API_KEY` | 豆包 API Key | 至少填一个 |
| `AI_DEFAULT_PROVIDER` | 默认使用的 AI | 可选（默认 claude） |
| `PORT` | 服务端口 | 可选（默认 8741） |
| `EMBEDDING_MODEL` | 本地 embedding 模型 | 可选（默认 bge-small-zh-v1.5） |

---

## License

MIT
