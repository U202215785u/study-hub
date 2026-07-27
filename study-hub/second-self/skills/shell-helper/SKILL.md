---
name: shell-helper
description: 辅助执行常见 Shell 任务的智能封装。自动处理路径、权限和输出格式化。
version: 1.0.0
author: second-self
triggers: ["shell", "命令", "脚本", "运行", "执行"]
risk_level: risky
requires_confirmation: true
---

# Shell Helper 技能

封装常见 shell 操作，提供更安全、更易读的执行方式。

## 功能

- 智能路径解析
- 输出自动截断和格式化
- 常见命令别名（如 ll = ls -la）
