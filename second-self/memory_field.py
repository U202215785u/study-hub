"""记忆场系统 — 情境识别与记忆激活

模拟人脑的"场景绑定"机制：
- 不同情境激活不同的记忆网络
- 核心记忆（身份、优先级）几乎总是激活
- 情境记忆根据场类型选择性激活
- 冲突记忆被主动抑制
"""
import json
import re
from typing import Any

from memory_store import search_memory, get_entry, _get_db
from memory_temperature import calculate_temperature, filter_by_temperature


FIELD_PROFILES = {
    "通用场": {
        "description": "默认场，当无法识别具体情境时使用",
        "keywords": [],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "general": {
                "min_temp": 0.1,
                "max_count": 5,
                "source": None,
                "field": None,
            },
        },
        "suppress": [],
        "emotional_tuning": {},
    },
    "创作场": {
        "description": "创作内容、制作作品、输出表达",
        "keywords": ["创作", "写", "做", "设计", "视频", "文章", "作品", "输出", "制作", "画图", "拍", "剪", "文案", "脚本", "内容"],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "style": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["preference", "principle"]},
            "skill": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["identity", "action"]},
            "method": {"min_temp": 0.15, "max_count": 3, "source": None, "field": ["knowledge", "method", "capture"]},
            "project": {"min_temp": 0.25, "max_count": 2, "source": None, "field": ["project"]},
        },
        "suppress": ["finance", "risk_aversion", "autonomy"],
        "emotional_tuning": {
            "anxiety": "给具体可执行的步骤，不要开放式建议。每次只给一个下一步。",
            "perfectionism": "鼓励'先做一个烂的'。完成比完美重要。",
            "excitement": "很好，把能量聚焦到一个具体动作上。",
        },
    },
    "决策场": {
        "description": "做选择、评估选项、分析利弊",
        "keywords": ["决定", "选择", "选", "要不要", "是否", "纠结", "犹豫", "分析", "评估", "对比", "利弊", "建议", "推荐", "怎么选"],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "principle": {"min_temp": 0.25, "max_count": 4, "source": None, "field": ["principle"]},
            "history": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["history", "decision", "thought"]},
            "anti_pattern": {"min_temp": 0.2, "max_count": 2, "source": None, "field": ["preference"]},
            "project": {"min_temp": 0.25, "max_count": 2, "source": None, "field": ["project"]},
        },
        "suppress": ["creative_style", "technical_detail", "method"],
        "emotional_tuning": {
            "fear": "引用 P1 原则：不因为恐惧选择安全。区分'害怕'和'不合理'。",
            "over_analysis": "引用 P6 原则：行动优于分析。信息够70%就动。",
            "anxiety": "列出最坏情况和应对方案，然后推进。",
        },
    },
    "学习场": {
        "description": "学习新知、研究问题、理解概念",
        "keywords": ["学", "了解", "研究", "什么是", "怎么", "为什么", "教程", "课程", "书", "知识", "概念", "原理", "技术", "工具"],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "knowledge": {"min_temp": 0.2, "max_count": 4, "source": None, "field": ["knowledge", "capture", "fact"]},
            "method": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["method", "action"]},
            "question": {"min_temp": 0.15, "max_count": 2, "source": None, "field": ["thought"]},
            "project": {"min_temp": 0.2, "max_count": 2, "source": None, "field": ["project"]},
        },
        "suppress": ["finance", "social"],
        "emotional_tuning": {
            "overwhelm": "PF2 反模式提醒：不要收集10篇教程但一行代码没写。边学边做。",
            "excitement": "很好，但设定一个具体产出目标：学完后要做出什么？",
        },
    },
    "社交场": {
        "description": "人际互动、沟通、关系处理",
        "keywords": ["聊", "说", "沟通", "关系", "朋友", "同事", "领导", "约会", "聚会", "社交", "人际", "冲突", "合作", "团队"],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "relationship": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["emotion", "history"]},
            "boundary": {"min_temp": 0.2, "max_count": 2, "source": None, "field": ["principle", "preference"]},
            "emotion_history": {"min_temp": 0.15, "max_count": 2, "source": None, "field": ["emotion"]},
        },
        "suppress": ["technical_detail", "method"],
        "emotional_tuning": {
            "conflict_avoidance": "PF7 提醒：关键问题上没有表达真实立场，事后后悔。温和但清晰地表达。",
            "anxiety": "P4 原则：维持关系稳定质量是长期生产力的基础设施。",
        },
    },
    "执行场": {
        "description": "执行任务、推进项目、具体操作",
        "keywords": ["做", "执行", "推进", "完成", "搞定", "实施", "落地", "操作", "步骤", "流程", "任务", "todo", "安排"],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "action_history": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["action", "history"]},
            "method": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["method", "knowledge"]},
            "project": {"min_temp": 0.25, "max_count": 3, "source": None, "field": ["project"]},
            "autonomy": {"min_temp": 0.2, "max_count": 2, "source": None, "field": ["autonomy"]},
        },
        "suppress": ["creative_style", "emotion"],
        "emotional_tuning": {
            "procrastination": "P6 原则：行动优于分析。先动5分钟。",
            "overwhelm": "拆成最小下一步。只做接下来5分钟的事。",
        },
    },
}


def detect_field(message: str, history: list[dict] | None = None) -> str:
    message_lower = message.lower()
    scores = {}
    for field_name, profile in FIELD_PROFILES.items():
        if field_name == "通用场":
            continue
        score = 0
        for kw in profile.get("keywords", []):
            if kw in message_lower:
                score += 1
        if history and len(history) > 0:
            last_field = history[-1].get("field_type", "")
            if last_field == field_name:
                score += 0.5
        scores[field_name] = score
    if scores:
        best_field = max(scores, key=scores.get)
        if scores[best_field] > 0:
            return best_field
    return "通用场"


def detect_emotional_state(message: str, history: list[dict] | None = None) -> str:
    message_lower = message.lower()
    emotional_signals = {
        "anxiety": ["焦虑", "担心", "怕", "紧张", "不确定", "迷茫", "压力", "烦", "急"],
        "excitement": ["兴奋", "期待", "想试试", "迫不及待", "激动", "好想", "跃跃欲试"],
        "frustration": ["烦", "累", "失望", "郁闷", "挫败", "没劲", "不想", "放弃", "算了"],
        "fear": ["害怕", "恐惧", "不敢", "万一", "要是", "风险", "失败", "输"],
        "overwhelm": ["太多", "忙不过来", " overwhelm", "爆炸", "崩溃", "应付不了"],
        "perfectionism": ["完美", "最好", "最优", "完整", "准备好了", "还不够"],
        "procrastination": ["明天", "以后", "晚点", "再想想", "还没", "等"],
        "conflict_avoidance": ["算了", "随便", "都行", "无所谓", "不想争", "忍"],
        "pride": ["做到了", "完成", "搞定", "不错", "满意", "骄傲"],
    }
    scores = {}
    for emotion, signals in emotional_signals.items():
        score = sum(1 for s in signals if s in message_lower)
        if score > 0:
            scores[emotion] = score
    if scores:
        return max(scores, key=scores.get)
    return "neutral"


def build_field(message: str, field_type: str | None = None, history: list[dict] | None = None, snapshot: dict | None = None) -> dict:
    if field_type is None:
        field_type = detect_field(message, history)
    profile = FIELD_PROFILES.get(field_type, FIELD_PROFILES["通用场"])
    emotional_state = detect_emotional_state(message, history)
    core_layers = _build_core_layers(snapshot)
    activated_layers = _build_activated_layers(profile, message, emotional_state)
    suppressed = profile.get("suppress", [])
    emotional_tuning = profile.get("emotional_tuning", {}).get(emotional_state, "")
    return {
        "field_type": field_type,
        "emotional_state": emotional_state,
        "core": core_layers,
        "activated": activated_layers,
        "suppressed": suppressed,
        "emotional_tuning": emotional_tuning,
    }


def _build_core_layers(snapshot: dict | None) -> dict:
    layers = {}
    if snapshot and "me" in snapshot:
        me = snapshot["me"]
        layers["identity"] = [{
            "source": "self://ME.md",
            "type": "identity",
            "content": _format_identity(me),
            "temperature": 1.0,
            "field": "identity",
            "depth": "core",
        }]
    if snapshot and "dashboard" in snapshot:
        dash = snapshot["dashboard"]
        projects = dash.get("strategic_projects", [])
        if projects:
            layers["priorities"] = [{
                "source": "self://DASHBOARD.md",
                "type": "project",
                "content": _format_projects(projects),
                "temperature": 0.9,
                "field": "project",
                "depth": "core",
            }]
    return layers


def _build_activated_layers(profile: dict, message: str, emotional_state: str) -> dict:
    layers = {}
    for layer_name, config in profile.get("activate", {}).items():
        candidates = _retrieve_candidates(message, config)
        min_temp = config.get("min_temp", 0.0)
        max_count = config.get("max_count", 5)
        heated = filter_by_temperature(candidates, min_temp=min_temp)
        layers[layer_name] = heated[:max_count]
    return layers


def _retrieve_candidates(message: str, config: dict) -> list[dict]:
    result = search_memory(message, k=30, use_causal=False)
    candidates = result.get("results", [])
    full_entries = []
    for c in candidates:
        entry_id = c.get("entry_id")
        if entry_id:
            entry = get_entry(entry_id)
            if entry:
                full_entries.append(entry)
    target_fields = config.get("field")
    if target_fields:
        full_entries = [e for e in full_entries if e.get("field") in target_fields]
    return full_entries


def _format_identity(me: dict) -> str:
    identity = me.get("identity", {})
    career = me.get("career", {})
    traits = me.get("traits", {})
    parts = [
        f"代号 L，{identity.get('年龄', '?')}岁，{identity.get('学历', '?')}，{identity.get('城市', '?')}",
        f"{career.get('公司', '?')} · {career.get('岗位', '?')} · 月入{career.get('月到手', '?')}",
    ]
    if traits:
        trait_str = "、".join([f"{k}:{v}" for k, v in list(traits.items())[:3]])
        parts.append(f"性格：{trait_str}")
    return "\n".join(parts)


def _format_projects(projects: list) -> str:
    lines = ["当前战略项目："]
    for p in projects:
        name = p.get("name", "")
        progress = p.get("progress", "")
        blocker = p.get("blocker", "")
        lines.append(f"- {name}：{progress}")
        if blocker:
            lines.append(f"  ⚠ 阻断：{blocker}")
    return "\n".join(lines)


def format_field_for_prompt(field: dict) -> str:
    lines = [f"【当前情境：{field['field_type']}】"]
    if field["emotional_state"] != "neutral":
        lines.append(f"情绪状态：{field['emotional_state']}")
    lines.append("\n=== 核心认知 ===")
    for layer_name, memories in field["core"].items():
        for mem in memories:
            lines.append(mem["content"])
    if field["activated"]:
        lines.append("\n=== 相关记忆 ===")
        for layer_name, memories in field["activated"].items():
            if memories:
                lines.append(f"\n【{layer_name}】")
                for mem in memories:
                    temp = mem.get("temperature", 0)
                    preview = mem.get("content", "")[:150].replace("\n", " ")
                    lines.append(f"  · [{temp:.2f}] {preview}")
    if field["emotional_tuning"]:
        lines.append(f"\n=== 情绪调制 ===")
        lines.append(field["emotional_tuning"])
    if field["suppressed"]:
        lines.append(f"\n=== 当前抑制 ===")
        lines.append(f"以下主题与当前情境不相关，降低权重：{', '.join(field['suppressed'])}")
    return "\n".join(lines)
