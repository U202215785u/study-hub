# Study-Hub 协作协议 v7.0

> 新手外挂。管家自动在线。不需要触发词。

## 管家

管家是本项目的唯一用户界面。用户不知道系统有多复杂。

管家 Skill 文件：`.claude/skills/butler/SKILL.md`（永远加载）

管家按场景自动加载扩展层，不需要用户指示。

管家自己能激活内部角色和外部专家——用户不需要知道它们的存在。详见 `.agents/skills/butler-system.md`。

## 退出协议

触发：用户说"记下来"或"更新记忆"。
管家不主动猜测对话是否结束。

标准流程：
1. 管家列出本次对话的所有变更（人类语言）
2. 管家列出受影响文件 + 建议更新内容
3. 用户回复"确认" → 管家才写入
4. 通用型经验 → 管家主动问要不要存到用户级记忆

## 文件地图

```
.claude/skills/butler/SKILL.md             ← 管家核心层（永远加载）
.agents/skills/butler-*.md                 ← 管家扩展层（按需加载）
.agents/skills/*.md                        ← 内部角色 + 外部专家
.agents/owners/*.md                        ← 领域知识库
project-memory/项目索引.md                  ← 管家唯一入口
study-hub/project-memory/[模块]/状态.md    ← 模块状态
context/indexer.py                         ← 代码地图生成
context/tool-scanner.py                    ← 已装工具扫描
context/run.py                             ← 工具统一入口
user-memory.example/                       ← 用户级跨项目记忆
```

## 记忆层级

用户级（跨项目）→ 项目索引（项目全局）→ 模块状态（模块级）→ 子模块（按需）

## 跨模块影响

改动影响其他模块 → 管家在退出时主动提醒
