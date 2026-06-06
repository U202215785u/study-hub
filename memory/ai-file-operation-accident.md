# AI 文件操作事故 — 2026-06-06

## 事故

整理项目文件时，执行 `mv study-hub/second-self/* study-hub/second-self/.* second-self/ 2>/dev/null; rm -rf study-hub/second-self/`，导致 second-self 全部核心代码被删除。

## 因果链

1. **根因**：`mv` 命令中 `.*` 展开包含 `.` 和 `..`，导致 `mv` 未能正常完成
2. **催化**：`2>/dev/null` 掩盖了错误信息，误判为成功
3. **致命**：使用 `;` 而非 `&&`，`mv` 失败后 `rm -rf` 仍执行
4. **结果**：16 个 Python 模块 + 12 个配置文档 + 数据目录全部丢失

## 保全的数据

- `second-self/.memory/entries.db`（112 条记忆，最核心的资产）
- `second-second/docs/screenshots/`（5 张截图）
- 从数据库恢复的 5 个核心配置文件：ME.md、DASHBOARD.md、PRINCIPLES.md、PREFERENCES.md、AUTONOMY.md

## 恢复尝试

- VS Code 本地历史：无备份（从未在 VS Code 中打开编辑 second-self 文件）
- Cursor 本地历史：无备份
- Git：second-self 从未被追踪
- 结论：代码无法恢复，需重建骨架

## 教训

1. `rm -rf` 的敬畏程度应等同于 `DROP DATABASE`
2. 文件迁移的安全流程：复制 → 验证 → 重命名源为 .bak → 确认后删除
3. 绝不在同一条命令中同时使用 `2>/dev/null` 和 `rm -rf`
4. 移动文件时只用 `&&`，绝不用 `;`
