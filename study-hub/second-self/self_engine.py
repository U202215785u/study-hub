"""Self Engine — 决策管道

在每条消息到达 LLM 之前完成判断。不是提示词，是管道。

管道阶段：
  1. 加载 Self 层（ME.md + DASHBOARD.md）→ SelfLayerSnapshot
  2. 检索记忆（Memory Store）→ MemorySearchResult[]
  3. 决策引擎 8 步 → DecisionResult
  4. 构建代理上下文 → AgentContext
  5. 自动记忆捕获（Agent Loop 完成后调用）→ MemoryCaptureCandidate[]

纯逻辑。不调用 LLM。
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from gateway_paths import ROOT
from memory_store import search_memory, insert_entry, get_stats as memory_stats
from memory_field import build_field, format_field_for_prompt, detect_field, detect_emotional_state
from os_layer import gateway as os_gateway


def load_self_layer() -> dict:
    """读取 ME.md + DASHBOARD.md，组装 SelfLayerSnapshot。"""
    me = _parse_me()
    dashboard = _parse_dashboard()
    return {
        "me": me,
        "dashboard": dashboard,
        "snapshot_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _parse_me() -> dict:
    """解析 ME.md → 结构化 dict。"""
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
    """解析 DASHBOARD.md → 结构化 dict。"""
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
            "上次更新": "updated",
        }
        for cn_field, en_field in fields.items():
            m = re.search(rf'\*\*{cn_field}\*\*[:：]\s*(.+)', body)
            if m:
                proj[en_field] = m.group(1).strip()
        projects.append(proj)
    maintenance = []
    maint_section = _extract_section(text, "维护清单区")
    if maint_section:
        for line in maint_section.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]"):
                task = line[5:].strip()
                deadline = ""
                deadline_match = re.search(r'[（(](.+?)[）)]', task)
                if deadline_match:
                    deadline = deadline_match.group(1)
                maintenance.append({"task": task, "deadline": deadline, "status": "pending"})
    return {"strategic_projects": projects, "maintenance_items": maintenance}


def _extract_section(text: str, section_name: str) -> str | None:
    pattern = rf'##\s+{re.escape(section_name)}.*?\n(.*?)(?=\n## |\Z)'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None


def _parse_kv_pairs(text: str) -> dict:
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            line = line[2:]
        m = re.match(r'(.+?)[：:]\s*(.+)', line)
        if m:
            result[m.group(1).strip()] = m.group(2).strip()
    return result


def _parse_list(text: str) -> list:
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def _parse_priorities(text: str) -> list:
    priorities = []
    for match in re.finditer(r'(\d+)\.\s*\*\*(.+?)\*\*[:：]\s*(.+)', text):
        priorities.append({
            "rank": int(match.group(1)),
            "title": match.group(2).strip(),
            "description": match.group(3).strip(),
        })
    return sorted(priorities, key=lambda p: p["rank"])


def retrieve_memories(context_text: str, k: int = 5, snapshot: dict | None = None, message_text: str = "") -> dict:
    if snapshot and message_text:
        return build_field(message_text, snapshot=snapshot)
    result = search_memory(context_text, k)
    return {"results": result.get("results", [])}


def run_decision_engine(message_text: str, snapshot: dict, memories: list[dict]) -> dict:
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

    # OS 意图检测
    os_intent = os_gateway.detect_intent(message_text)
    if os_intent:
        autonomy = {"level": "L1", "reason": f"检测到 OS 操作意图: {os_intent}，需要用户确认", "requires_confirmation": True}
        if os_intent.startswith("fs.read") or os_intent.startswith("browser.extract") or os_intent.startswith("skill.list"):
            autonomy = {"level": "L2", "reason": f"只读 OS 操作: {os_intent}，自动执行", "requires_confirmation": False}
        next_step = f"用户请求了系统操作 [{os_intent}]。建议：确认安全后通过 OS Layer 执行。"

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
        "os_intent": os_intent,
        "decided_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _judge_priority(text: str, priorities: list) -> tuple[str, str]:
    text_lower = text.lower()
    for p in priorities:
        title = p.get("title", "")
        desc = p.get("description", "")
        if _text_overlap(text_lower, f"{title} {desc}"):
            return "HIGH", f"直接关联 P{p['rank']}：{title}"
    domains = ["AI", "设计", "财务", "创作", "思维", "新能源", "交互", "前端", "代码"]
    for kw in domains:
        if kw.lower() in text_lower:
            return "MEDIUM", f"匹配知识域关键词「{kw}」，但不直接命中优先级"
    return "LOW", "未匹配任何优先级或知识域"


def _match_project(text: str, projects: list) -> str | None:
    text_lower = text.lower()
    for proj in projects:
        name = proj.get("name", "").lower()
        if name and name in text_lower:
            return proj["name"]
    return None


def _check_anti_patterns(text: str, memories: list) -> dict:
    anti_patterns = {
        "过度分析": ["再看看", "再想想", "研究一下", "多了解", "不确定"],
        "分散精力": ["也学", "也做", "同时", "另外还"],
        "完美主义": ["完美", "最优", "最好", "完整"],
    }
    text_lower = text.lower()
    for pattern_name, keywords in anti_patterns.items():
        for kw in keywords:
            if kw in text_lower:
                return {"detected": True, "description": f"可能触发反模式「{pattern_name}」：关键词「{kw}」"}
    return {"detected": False, "description": None}


def _extract_history_references(memories: list) -> list:
    return [
        {"entry": m, "score": m.get("score", 0)}
        for m in memories[:3]
        if m.get("type") in ("decision", "thought", "milestone")
    ]


def _match_principles(text: str, memories: list) -> list:
    principles_map = {
        "行动": "P6: 行动优于分析",
        "分析": "P6: 行动优于分析",
        "完美": "P6: 行动优于分析",
        "焦虑": "P7: 能量有限是事实",
        "怕": "P7: 能量有限是事实",
        "恐惧": "P1: 不因为恐惧选安全",
        "项目": "P5: 信息先过优先级漏斗",
        "优先级": "P5: 信息先过优先级漏斗",
        "想法": "P5: 信息先过优先级漏斗",
        "逃避": "P6: 行动优于分析",
        "学习": "P6: 行动优于分析",
    }
    matches = []
    text_lower = text.lower()
    seen = set()
    for kw, principle in principles_map.items():
        if kw in text_lower and principle not in seen:
            seen.add(principle)
            matches.append({"principle": principle, "relevance": f"关键词「{kw}」命中"})
    return matches


def _judge_autonomy(text: str, priority: str) -> dict:
    permission_checks = {
        "money": _contains_any(text, ["支付", "付款", "转账", "钱", "购买", "合同"]),
        "publish": _contains_any(text, ["发布", "发送", "公开", "上传到"]),
        "delete": _contains_any(text, ["删除", "删掉", "清除"]),
        "privacy": _contains_any(text, ["身份证", "银行卡", "密码", "账号"]),
        "core_self": _contains_any(text, ["修改 ME", "改原则", "改 PRINCIPLES"]),
        "irreversible": _contains_any(text, ["不可逆", "永久"]),
    }
    any_risky = any(permission_checks.values())
    if any_risky:
        return {"level": "L1", "reason": "涉及敏感操作，需用户确认", "requires_confirmation": True}
    elif priority == "LOW":
        return {"level": "L2", "reason": "低优先级，自动处理", "requires_confirmation": False}
    else:
        return {"level": "L2", "reason": "无敏感操作，自动执行", "requires_confirmation": False}


def _suggest_next_step(text: str, priority: str, project: str | None) -> str:
    if project:
        return f"关联项目「{project}」——建议更新 DASHBOARD 的进度或阻断因素"
    if priority == "HIGH":
        return "这个想法与你的核心目标直接相关。建议：写 200 字方案，定一个本周内可完成的第一个动作。"
    if priority == "MEDIUM":
        return "有知识价值但不紧急。建议：花 15 分钟存入知识库，不要深入。"
    return "低优先级。建议：记录一句话备忘，不展开。"


def _should_capture(priority: str, project: str | None) -> bool:
    return priority in ("HIGH", "MEDIUM") or project is not None


def build_agent_context(message_text: str, snapshot: dict, memory_field: dict, decision: dict) -> dict:
    if isinstance(memory_field, dict) and "field_type" in memory_field:
        field_prompt = format_field_for_prompt(memory_field)
        relevant_memories = []
        for layer in memory_field.get("core", {}).values():
            relevant_memories.extend(layer)
        for layer in memory_field.get("activated", {}).values():
            relevant_memories.extend(layer)
    else:
        field_prompt = None
        relevant_memories = memory_field if isinstance(memory_field, list) else []
    return {
        "self_snapshot": snapshot,
        "memory_field": memory_field,
        "field_prompt": field_prompt,
        "relevant_memories": relevant_memories[:10],
        "decision": decision,
        "current_message": {
            "message_id": f"msg-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "text": message_text,
            "arrived_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "source_channel": "api",
        },
        "conversation_history": [],
        "os_capabilities": {
            "available": True,
            "intents": [
                "shell.execute", "fs.read", "fs.write", "fs.list", "fs.search", "fs.delete",
                "browser.navigate", "browser.extract", "browser.screenshot",
                "skill.execute", "skill.list",
            ],
            "detected_intent": decision.get("os_intent"),
        },
        "built_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def capture_memories(message_text: str, decision: dict, agent_response: str = "") -> list[str]:
    """Agent Loop 完成后，自动捕获对话中的记忆条目。"""
    try:
        from pipeline_dialogue import distill_dialogue
        return distill_dialogue(message_text, agent_response)
    except Exception:
        return []


def process(message_text: str) -> dict:
    """完整 Self Engine 管道：加载→检索→决策→上下文。"""
    snapshot = load_self_layer()
    context_for_search = _build_search_context(message_text, snapshot)
    memory_field = retrieve_memories(context_for_search, snapshot=snapshot, message_text=message_text)
    flat_memories = []
    if isinstance(memory_field, dict) and "activated" in memory_field:
        for layer in memory_field.get("core", {}).values():
            flat_memories.extend(layer)
        for layer in memory_field.get("activated", {}).values():
            flat_memories.extend(layer)
    else:
        flat_memories = memory_field if isinstance(memory_field, list) else []
    decision = run_decision_engine(message_text, snapshot, flat_memories)
    if isinstance(memory_field, dict):
        decision["field_type"] = memory_field.get("field_type", "通用场")
        decision["emotional_state"] = memory_field.get("emotional_state", "neutral")
        decision["emotional_tuning"] = memory_field.get("emotional_tuning", "")
    context = build_agent_context(message_text, snapshot, memory_field, decision)
    return {
        "context": context,
        "decision": decision,
        "snapshot": snapshot,
        "memory_stats": memory_stats(),
    }


def _build_search_context(text: str, snapshot: dict) -> str:
    parts = [text]
    me = snapshot.get("me", {})
    priorities = me.get("top_priorities", [])
    if priorities:
        parts.append(" ".join(p["title"] for p in priorities))
    dash = snapshot.get("dashboard", {})
    projects = dash.get("strategic_projects", [])
    if projects:
        parts.append(" ".join(p.get("name", "") for p in projects))
    return " ".join(parts)


def _text_overlap(a: str, b: str) -> bool:
    a_words = set(re.findall(r'[\w一-鿿]+', a.lower()))
    b_words = set(re.findall(r'[\w一-鿿]+', b.lower()))
    if not a_words or not b_words:
        return False
    overlap = a_words & b_words
    return len(overlap) >= min(2, len(a_words), len(b_words))


def _contains_any(text: str, keywords: list) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)
