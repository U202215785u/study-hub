# PRD：Study-Hub ↔ Obsidian 双向通信

> 创建于 2026-06-06 | 状态：待实现

## 功能目标

Study-Hub 和 Obsidian 之间双向 HTTP 通信。Study-Hub 文档一键发送到 Obsidian vault，Obsidian 笔记拉回 Study-Hub 做 AI 处理（分块 + 向量化 + 语义搜索）。纯本地通信，不经过云端。

## 核心流程

1. **Study-Hub → Obsidian**：用户在文档详情页/Wiki 页点「发送到 Obsidian」→ 内容写入 Obsidian vault 指定文件夹 → 自动转换 `[[wikilinks]]` 和 `#tag`
2. **Obsidian → Study-Hub**：用户在 Obsidian 里通过命令/按钮 → 当前笔记 POST 到 Study-Hub → 自动入库、分块、向量化
3. **连接状态**：前端实时显示 Obsidian 是否在线

## 关键决策（已确认）

1. **通信方向**：双向（推 + 拉）
2. **Obsidian 依赖**：依赖 Local REST API 插件（`localhost:27124`）
3. **格式转换**：智能转换 —— 发送到 Obsidian 时自动将关键词转为 `[[wikilinks]]`，标签转为 `#tag`
4. **拉回路径**：手动触发 + 自动监听 vault 文件夹，两种方式并存

## 涉及区域

| 区域 | 改动内容 |
|------|----------|
| 后端 | 新增 4 个接口（send/search/notes/status）+ ObsidianClient HTTP 客户端 |
| 前端 | 文档页和 Wiki 页新增「发送到 Obsidian」按钮 + 连接状态指示器 |
| 配置 | .env 新增 `OBSIDIAN_VAULT_PATH`、`OBSIDIAN_REST_API_URL`、`OBSIDIAN_DEFAULT_FOLDER` |
| 文档 | 用户配置指南 |

## 新增接口

### Study-Hub → Obsidian

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/obsidian/send` | 将文档/Wiki 写入 Obsidian vault |
| POST | `/obsidian/search` | 搜索 Obsidian 中的笔记 |
| GET | `/obsidian/notes` | 列出 vault 中的笔记 |
| GET | `/obsidian/status` | 检测 Obsidian REST API 是否可达 |

### Obsidian → Study-Hub

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/obsidian/import` | 导入一篇 Obsidian 笔记到知识库 |
| POST | `/obsidian/import-batch` | 批量导入 |

## 发送内容格式

推送到 Obsidian 时：
- 标题 → 文件名（`.md`）
- 内容 → Markdown 正文
- 关键词 → 自动转为 `[[wikilinks]]`
- Study-Hub 标签 → Obsidian `#tag`
- 存入 vault 的 `study-hub/` 子目录（可配置）

## 边界情况

- **Obsidian 未安装 REST API 插件**：前端显示"未检测到 Obsidian"，引导安装
- **Obsidian 未运行**：请求超时后提示"请先打开 Obsidian"
- **Vault 路径错误**：发送前校验路径，不存在则提示用户
- **大文档（>5000 字）**：不截断，完整发送
- **冲突（两边同时编辑）**：以最后写入为准，标记潜在冲突

## 验收标准

- [ ] Study-Hub 文档成功写入 Obsidian vault（含 wikilinks 转换）
- [ ] Obsidian 笔记成功导入 Study-Hub 知识库（含分块 + 向量化）
- [ ] 连接失败时有明确的用户提示
- [ ] 纯本地通信，不依赖云端服务
- [ ] 用户配置文档完整可用
