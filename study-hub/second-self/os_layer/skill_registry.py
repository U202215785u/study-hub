"""技能注册系统 — 对标 OpenClaw Skill 系统

技能是扩展 OS 能力的插件。每个技能是一个目录，包含：
  SKILL.md      — 描述文件（YAML frontmatter + Markdown）
  run.py        — Python 执行入口（可选）
  scripts/      — 辅助脚本（可选）

加载来源（按优先级）：
  1. second-self/skills/         — 用户自定义技能
  2. ~/.second-self/skills/      — 全局用户技能
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from gateway_paths import ROOT


@dataclass
class Skill:
    name: str
    description: str
    version: str
    author: str
    triggers: list[str] = field(default_factory=list)
    risk_level: str = "safe"  # safe / risky / dangerous
    requires_confirmation: bool = False
    path: Path = field(default_factory=Path)
    run_func: Callable | None = None


def _parse_skill_md(path: Path) -> dict[str, Any]:
    """解析 SKILL.md 的 YAML frontmatter + Markdown body。"""
    import json
    text = path.read_text(encoding="utf-8", errors="replace")

    # 提取 YAML frontmatter
    frontmatter = {}
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 3:
            fm_text = text[3:end].strip()
            current_key = None
            for line in fm_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("-"):
                    # 列表项（block 列表）
                    if current_key:
                        if current_key not in frontmatter:
                            frontmatter[current_key] = []
                        val = stripped[1:].strip().strip('"').strip("'")
                        frontmatter[current_key].append(val)
                elif ":" in stripped:
                    k, v = stripped.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    current_key = k
                    # 尝试解析内联 JSON 数组
                    if v.startswith("[") and v.endswith("]"):
                        try:
                            v = json.loads(v.replace("'", '"'))
                        except json.JSONDecodeError:
                            pass
                    elif isinstance(v, str):
                        v = v.strip('"').strip("'")
                    frontmatter[k] = v

    return frontmatter


def discover_skills() -> list[Skill]:
    """发现所有可用技能。"""
    skills = []
    search_paths = [
        ROOT / "skills",
        Path.home() / ".second-self" / "skills",
    ]

    for base in search_paths:
        if not base.exists():
            continue
        for skill_dir in base.iterdir():
            if not skill_dir.is_dir():
                continue
            md_file = skill_dir / "SKILL.md"
            if not md_file.exists():
                continue

            fm = _parse_skill_md(md_file)
            name = fm.get("name", skill_dir.name)
            description = fm.get("description", "")
            version = fm.get("version", "0.1.0")
            author = fm.get("author", "unknown")
            triggers = fm.get("triggers", []) or fm.get("trigger", [])
            if isinstance(triggers, str):
                triggers = [t.strip() for t in triggers.split(",")]
            risk = fm.get("risk_level", "safe")
            requires = str(fm.get("requires_confirmation", "false")).lower() == "true"

            # 尝试加载 run.py
            run_py = skill_dir / "run.py"
            run_func = None
            if run_py.exists():
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(f"skill_{skill_dir.name}", run_py)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "run"):
                        run_func = mod.run
                except Exception:
                    pass

            skills.append(Skill(
                name=name,
                description=description,
                version=version,
                author=author,
                triggers=triggers,
                risk_level=risk,
                requires_confirmation=requires,
                path=skill_dir,
                run_func=run_func,
            ))

    return skills


def find_skill_by_trigger(text: str, skills: list[Skill] | None = None) -> Skill | None:
    """根据用户输入文本匹配技能。"""
    if skills is None:
        skills = discover_skills()
    text_lower = text.lower()
    for skill in skills:
        for trigger in skill.triggers:
            if trigger.lower() in text_lower:
                return skill
    return None


def list_skills() -> list[dict]:
    """列出所有技能的元信息。"""
    return [
        {
            "name": s.name,
            "description": s.description,
            "version": s.version,
            "author": s.author,
            "triggers": s.triggers,
            "risk_level": s.risk_level,
            "requires_confirmation": s.requires_confirmation,
        }
        for s in discover_skills()
    ]


def execute_skill(skill: Skill, args: dict[str, Any], *, user_confirmed: bool = False) -> dict[str, Any]:
    """执行技能。"""
    if skill.requires_confirmation and not user_confirmed:
        return {
            "success": False,
            "error": f"[NEEDS_CONFIRMATION] 技能 '{skill.name}' 需要用户确认。",
            "skill": skill.name,
        }

    if skill.run_func is None:
        return {
            "success": False,
            "error": f"技能 '{skill.name}' 没有可执行入口 (run.py::run)",
            "skill": skill.name,
        }

    try:
        result = skill.run_func(args)
        return {
            "success": True,
            "result": result,
            "skill": skill.name,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"技能执行失败: {str(e)}",
            "skill": skill.name,
        }
