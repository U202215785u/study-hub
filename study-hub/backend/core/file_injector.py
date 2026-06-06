"""
文件注入器 — 将记忆系统内容生成到 AI 工具可读取的文件

生成文件：
- CLAUDE.md          → 项目根目录（Claude Code 自动读取）
- .cursor/rules/memory-context.mdc  → Cursor 规则（alwaysApply）
- .claude/skills/memory-context/SKILL.md  → Kimi Code CLI skill（需手动加载）

触发方式：定时任务每5分钟检查并更新
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

# 项目根目录（backend 的父目录）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# 输出路径
CLAUDE_MD_PATH = os.path.join(PROJECT_ROOT, "CLAUDE.md")
CURSOR_RULE_PATH = os.path.join(PROJECT_ROOT, ".cursor", "rules", "memory-context.mdc")
KIMI_SKILL_DIR = os.path.join(PROJECT_ROOT, ".claude", "skills", "memory-context")
KIMI_SKILL_PATH = os.path.join(KIMI_SKILL_DIR, "SKILL.md")

# 记忆数据库
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_db
from core.memory_ranker import rank_memories


def _ensure_dirs():
    """确保输出目录存在"""
    os.makedirs(os.path.dirname(CURSOR_RULE_PATH), exist_ok=True)
    os.makedirs(KIMI_SKILL_DIR, exist_ok=True)


def _fetch_role_memories(conn, top_k: int = 3) -> List[Dict]:
    """获取角色记忆（混合加权排序）"""
    rows = conn.execute(
        """SELECT * FROM memories
           WHERE memory_layer = 'role' AND status = 'active'
           ORDER BY updated_at DESC"""
    ).fetchall()
    ranked = rank_memories(rows, top_k=top_k)
    return [dict(r) for r in ranked]


def _fetch_project_memories(conn, top_k: int = 3) -> List[Dict]:
    """获取活跃项目记忆"""
    rows = conn.execute(
        """SELECT p.*, COUNT(m.id) as mem_count
           FROM projects p
           LEFT JOIN memories m ON m.project_name = p.name AND m.status = 'active'
           WHERE p.status = 'active' AND p.last_active > datetime('now', '-30 days')
           GROUP BY p.id
           ORDER BY p.last_active DESC LIMIT ?""",
        (top_k,),
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_workflow_memories(conn, top_k: int = 3) -> List[Dict]:
    """获取工作流记忆"""
    rows = conn.execute(
        """SELECT * FROM workflows
           ORDER BY updated_at DESC LIMIT ?""",
        (top_k,),
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_world_memories(conn, top_k: int = 2) -> List[Dict]:
    """获取世界记忆（documents + wiki_pages）"""
    docs = conn.execute(
        """SELECT id, title, content, tags, created_at, 'document' as source
           FROM documents
           ORDER BY created_at DESC LIMIT ?""",
        (top_k,),
    ).fetchall()

    wikis = conn.execute(
        """SELECT id, title, content, summary, created_at, 'wiki' as source
           FROM wiki_pages
           ORDER BY updated_at DESC LIMIT ?""",
        (top_k,),
    ).fetchall()

    return [dict(r) for r in list(docs) + list(wikis)]


def _build_behavior_instructions(
    role_memories: List[Dict],
    project_memories: List[Dict],
    workflow_memories: List[Dict],
    world_memories: List[Dict],
) -> str:
    """构建行为指令式内容"""
    parts = []

    # 角色记忆 → 行为指令
    if role_memories:
        lines = []
        for i, m in enumerate(role_memories, 1):
            content = m.get("content", "")
            mem_type = m.get("memory_type", "preference")
            # 将信息描述转换为行为指令
            if mem_type == "habit":
                lines.append(f"{i}. 用户习惯：{content}。请在协助时尊重这一习惯。")
            elif mem_type == "preference":
                lines.append(f"{i}. 用户偏好：{content}。请在相关场景中默认采用此偏好。")
            elif mem_type == "skill":
                lines.append(f"{i}. 用户能力：{content}。请基于此能力水平调整解释深度。")
            else:
                lines.append(f"{i}. {content}")
        parts.append("## 角色行为指令\n" + "\n".join(lines))

    # 项目记忆 → 行为指令
    if project_memories:
        lines = []
        for i, p in enumerate(project_memories, 1):
            name = p.get("name", "")
            tech = json.loads(p.get("tech_stack") or "[]")
            progress = p.get("progress_note", "")
            tech_str = f"（技术栈：{', '.join(tech)}）" if tech else ""
            progress_str = f" 当前进度：{progress}" if progress else ""
            lines.append(
                f"{i}. 用户正在做项目「{name}」{tech_str}。{progress_str} "
                f"请在涉及此项目时基于现有技术栈和进度给出建议。"
            )
        parts.append("## 项目行为指令\n" + "\n".join(lines))

    # 工作流记忆 → 行为指令
    if workflow_memories:
        lines = []
        for i, w in enumerate(workflow_memories, 1):
            name = w.get("name", "")
            prefs = json.loads(w.get("preferences") or "{}")
            pref_str = "；".join(f"{k}={v}" for k, v in prefs.items()) if prefs else ""
            lines.append(
                f"{i}. 用户的工作流「{name}」偏好：{pref_str}。 "
                f"请在协作时遵循此工作流习惯。"
            )
        parts.append("## 工作流行为指令\n" + "\n".join(lines))

    # 世界记忆 → 参考上下文（仅在需要时注入）
    if world_memories:
        lines = []
        for m in world_memories:
            source = m.get("source", "")
            title = m.get("title", "")
            content = m.get("content", "") or m.get("summary", "")
            # 截断内容避免过长
            if len(content) > 200:
                content = content[:200] + "..."
            source_label = "文档" if source == "document" else "Wiki"
            lines.append(f"- 【{source_label}】{title}：{content}")
        parts.append("## 参考上下文（按需使用）\n" + "\n".join(lines))

    return "\n\n".join(parts)


def _generate_claude_md(content: str) -> str:
    """生成 CLAUDE.md 格式"""
    return f"""# Study-Hub 记忆上下文

> 本文件由 Study-Hub 五层记忆系统自动生成，请勿手动编辑。
> 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}

{content}
"""


def _generate_cursor_mdc(content: str) -> str:
    """生成 .cursor/rules/memory-context.mdc 格式"""
    return f"""---
description: Study-Hub 记忆上下文 — 自动注入用户偏好、项目背景、工作流习惯
alwaysApply: true
---

# Study-Hub 记忆上下文

> 本文件由 Study-Hub 五层记忆系统自动生成，请勿手动编辑。
> 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}

{content}
"""


def _generate_kimi_skill(content: str) -> str:
    """生成 Kimi Code CLI SKILL.md 格式"""
    return f"""---
description: 加载 Study-Hub 记忆上下文 — 用户偏好、项目背景、工作流习惯。当用户说"加载记忆"或当前任务涉及用户已知项目时使用。
---

# Study-Hub 记忆上下文

> 本文件由 Study-Hub 五层记忆系统自动生成。
> 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}
> ⚠️ 使用方式：在 Kimi Code CLI 对话中说"加载 memory-context skill"

{content}
"""


def generate_memory_files() -> Dict[str, Any]:
    """生成所有记忆文件，返回生成结果统计"""
    _ensure_dirs()

    conn = get_db()
    try:
        role_memories = _fetch_role_memories(conn, top_k=3)
        project_memories = _fetch_project_memories(conn, top_k=3)
        workflow_memories = _fetch_workflow_memories(conn, top_k=3)
        world_memories = _fetch_world_memories(conn, top_k=2)
    finally:
        conn.close()

    # 构建行为指令式内容
    behavior_content = _build_behavior_instructions(
        role_memories, project_memories, workflow_memories, world_memories
    )

    # 如果没有记忆，生成空模板
    if not behavior_content:
        behavior_content = "## 暂无记忆\n\n用户尚未保存任何记忆。当用户使用 Study-Hub 浏览器插件或手动添加记忆后，此文件将自动更新。"

    # 生成三种格式
    claude_md = _generate_claude_md(behavior_content)
    cursor_mdc = _generate_cursor_mdc(behavior_content)
    kimi_skill = _generate_kimi_skill(behavior_content)

    # 写入文件
    files_written = []
    errors = []

    try:
        with open(CLAUDE_MD_PATH, "w", encoding="utf-8") as f:
            f.write(claude_md)
        files_written.append(CLAUDE_MD_PATH)
    except Exception as e:
        errors.append(f"CLAUDE.md: {e}")

    try:
        with open(CURSOR_RULE_PATH, "w", encoding="utf-8") as f:
            f.write(cursor_mdc)
        files_written.append(CURSOR_RULE_PATH)
    except Exception as e:
        errors.append(f".cursor/rules/memory-context.mdc: {e}")

    try:
        with open(KIMI_SKILL_PATH, "w", encoding="utf-8") as f:
            f.write(kimi_skill)
        files_written.append(KIMI_SKILL_PATH)
    except Exception as e:
        errors.append(f"memory-context/SKILL.md: {e}")

    return {
        "files_written": files_written,
        "errors": errors,
        "stats": {
            "role_memories": len(role_memories),
            "project_memories": len(project_memories),
            "workflow_memories": len(workflow_memories),
            "world_memories": len(world_memories),
        },
        "timestamp": datetime.now().isoformat(),
    }
