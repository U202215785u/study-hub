# Skill 市场集成经验

> 记录时间：2026-06-06

## 数据源

**awesome-claude-code** 是最全面的 Skill 目录：
- 5700+ 公开 Skill
- CSV 格式：`THE_RESOURCES_TABLE.csv`
- 包含分类、作者、许可、描述、Stars 等字段

备用源：
- alirezarezvani/claude-skills (5200+⭐, 338 个 Skill)
- awesome-skills.com (带安全评分)
- claudeskills.info (658+ 免费 Skill)

## 同步策略

1. **后端定时同步** — 避免前端直接调用 GitHub API 限流
2. **SQLite 缓存** — 首次加载后本地查询，响应快
3. **手动刷新按钮** — 用户可主动更新

## 本地扫描

Study-Hub 项目有两套 Skill 系统：
- `.claude/skills/` — Claude Code 格式（SKILL.md + 可选脚本）
- `.agents/skills/` — 项目级 Agent 角色 skill（.md 文件）

扫描逻辑：
1. 遍历目录下的 SKILL.md 或 .md 文件
2. 解析 YAML frontmatter 提取元数据
3. 同步到 `local_skills` 数据库表
4. 支持启用/禁用（改数据库字段）

## 踩坑记录

- **CSV 解析要注意引号包裹的字段** — Display Name 可能用引号包裹
- **Stars 字段可能有 K/M 后缀** — 需要解析转换
- **Windows 路径分隔符** — 扫描结果中的路径要用 `/` 统一
- **中文编码** — Python 输出需要设置 `PYTHONIOENCODING=utf-8`
