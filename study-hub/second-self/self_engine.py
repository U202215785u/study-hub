"""Self Engine — 决策管道

在每条消息到达 LLM 之前完成判断。不是提示词，是管道。
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from gateway_paths import ROOT
from memory_store import search_memory, insert_entry, get_stats as memory_stats
from memory_field import build_field, format_field_for_prompt, detect_field, detect_emotional_state


def load_self_layer() -> dict:
    """读取 ME.md + DASHBOARD.md。"""
    me = _parse_me()
    dashboard = _parse_dashboard()
    return {
        "me": me,
        "dashboard": dashboard,
        "snapshot_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _parse_me() -> dict:
    """解析 ME.md。"""
    me_path = ROOT / "ME.md"
    if not me_path.exists():
        return {}
    
    text = me_path.read_text(encoding="utf-8")
    result = {
        "identity": {},
        "career": {},
        "assets": {},
        "skills": [],
        "traits": {},
        "constraints": {},
        "top_priorities": [],
    }
    
    sections = {
        "基础事实": ("identity", _parse_kv_pairs),
        "职业": ("career", _parse_kv_pairs),
        "资产": ("assets", _parse_kv_pairs),
        "技能栈": ("skills", _parse_list),
        "性格特征": ("traits", _parse_kv_pairs),
        "当前约束": ("constraints", _parse_kv_pairs),
        "当前最高优先级": ("top_priorities", _parse_priorities),
    }
    
    for section_name, (key, parser) in sections.items():
        section_text = _extract_section(text, section_name)
        if section_text:
            result[key] = parser(section_text)
    
    return result


def _parse_dashboard() -> dict:
    """解析 DASHBOARD.md。"""
    dash_path = ROOT / "DASHBOARD.md"
    if not dash_path.exists():
        return {"strategic_projects": [], "maintenance_items": []}
    
    text = dash_path.read_text(encoding="utf-8")
    
    projects = []
    project_pattern = r'### 项目\s*\d*\s*[:：]\s*(.+?)\n(.*?)(?=### 项目|\n## |\Z)'
    for match in re.finditer(project_pattern, text, re.DOTALL):
        name = match.group(1).strip()
        body = match.group(2)
        proj = {"name": name}
        fields = {
            "目标": "goal",
            "当前进度": "progress",
            "下一个里程碑": "next_milestone",
            "阻断因素": "blocker",
        }
        for cn, en in fields.items():
            m = re.search(rf'{cn}[:：]\s*(.+)', body)
            if m:
                proj[en] = m.group(1).strip()
        projects.append(proj)
    
    return {"strategic_projects": projects}


def _extract_section(text: str, section_name: str) -> str | None:
    """提取 markdown 章节内容。支持章节标题后有附加内容（如日期）。"""
    pattern = rf'## {re.escape(section_name)}.*?\n(.*?)(?=\n## |\Z)'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None


def _parse_kv_pairs(text: str) -> dict:
    """解析键值对。"""
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("-") and ":" in line:
            key, value = line[1:].split(":", 1)
            result[key.strip()] = value.strip()
    return result


def _parse_list(text: str) -> list:
    """解析列表。"""
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def _parse_priorities(text: str) -> list:
    """解析优先级列表。"""
    priorities = []
    for match in re.finditer(r'(\d+)\.\s*\*\*(.+?)\*\*[:：]\s*(.+)', text):
        rank = int(match.group(1))
        title = match.group(2).strip()
        desc = match.group(3).strip()
        priorities.append({"rank": rank, "title": title, "description": desc})
    return sorted(priorities, key=lambda p: p["rank"])


def retrieve_memories(context_text: str, k: int = 5, snapshot: dict | None = None, message_text: str = "") -> dict:
    """检索记忆。"""
    if snapshot and message_text:
        return build_field(message_text, snapshot=snapshot)
    
    result = search_memory(context_text, k)
    return {"results": result.get("results", [])}


def run_decision_engine(message_text: str, snapshot: dict, memories: list[dict]) -> dict:
    """执行决策引擎。"""
    me = snapshot.get("me", {})
    dashboard = snapshot.get("dashboard", {})
    priorities = me.get("top_priorities", [])
    projects = dashboard.get("strategic_projects", [])
    
    priority, priority_reason = _judge_priority(message_text, priorities)
    linked_project = _match_project(message_text, projects)
    anti_pattern = _check_anti_patterns(message_text, memories)
    history_refs = _extract_history_references(memories)
    principle_matches = _match_principles(message_text, memories)
    autonomy = _judge_autonomy(message_text, priority)
    next_step = _suggest_next_step(message_text, priority, linked_project)
    should_capture = _should_capture(priority, linked_project)
    
    return {
        "priority": priority,
        "priority_reason": priority_reason,
        "linked_project": linked_project,
        "history_references": history_refs,
        "anti_pattern_risk": anti_pattern,
        "principle_matches": principle_matches,
        "principle_preference_deviation": {"detected": False, "detail": None},
        "autonomy_level": autonomy,
        "suggested_next_step": next_step,
        "should_capture_memory": should_capture,
        "capture_candidates": [],
        "decided_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _judge_priority(text: str, priorities: list) -> tuple[str, str]:
    """判断优先级。"""
    text_lower = text.lower()
    for p in priorities:
        title = p.get("title", "")
        desc = p.get("description", "")
        if _text_overlap(text_lower, f"{title} {desc}"):
            return "HIGH", f"直接关联 P{p['rank']}：{title}"
    
    knowledge_domains = ["AI", "设计", "财务", "创作", "思维", "新能源", "交互", "前端", "代码"]
    for kw in knowledge_domains:
        if kw.lower() in text_lower:
            return "MEDIUM", f"匹配知识域关键词「{kw}」"
    return "LOW", "未匹配任何优先级或知识域"


def _match_project(text: str, projects: list) -> str | None:
    """匹配项目。"""
    text_lower = text.lower()
    for proj in projects:
        name = proj.get("name", "").lower()
        if name and name in text_lower:
            return proj["name"]
    return None


def _check_anti_patterns(text: str, memories: list) -> dict:
    """检查反模式。"""
    anti_patterns = {
        "过度分析": ["再看看", "再想想", "研究一下", "多了解", "不确定"],
        "完美主义": ["不够好", "还不够", "再优化", "再改改", "不完美"],
        "拖延": ["明天再做", "以后再说", "等有空", "晚点"],
    }
    text_lower = text.lower()
    for pattern_name, triggers in anti_patterns.items():
        for trigger in triggers:
            if trigger in text_lower:
                return {"detected": True, "pattern": pattern_name, "trigger": trigger}
    return {"detected": False}


def _extract_history_references(memories: list) -> list[dict]:
    """提取历史参照。"""
    return [{"id": m.get("entry_id", ""), "preview": m.get("content", "")[:50]} for m in memories[:3]]


def _match_principles(text: str, memories: list) -> list[dict]:
    """匹配原则。"""
    return [{"id": m.get("entry_id", ""), "principle": m.get("content", "")[:50]} for m in memories[:2]]


def _judge_autonomy(text: str, priority: str) -> str:
    """判断授权等级。"""
    if priority == "HIGH":
        return "L1"
    return "L0"


def _suggest_next_step(text: str, priority: str, linked_project: str | None) -> str | None:
    """建议下一步。"""
    if linked_project:
        return f"继续推进项目「{linked_project}」"
    return None


def _should_capture(priority: str, linked_project: str | None) -> bool:
    """判断是否捕获记忆。"""
    return priority in ("HIGH", "MEDIUM") or linked_project is not None


def _text_overlap(text_a: str, text_b: str) -> bool:
    """检查两段文本是否有重叠的关键词。"""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    return len(words_a & words_b) > 0
