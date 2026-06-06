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
        "description": "默认场",
        "keywords": [],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "general": {"min_temp": 0.1, "max_count": 5, "source": None, "field": None},
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
            "anti_pattern": {"min_temp": 0.2, "max_count": 2, "source": None, "field": ["anti_pattern"]},
            "risk": {"min_temp": 0.2, "max_count": 2, "source": None, "field": ["risk", "constraint"]},
        },
        "suppress": ["creativity", "exploration"],
        "emotional_tuning": {
            "anxiety": "列出最坏情况和概率。通常没那么糟。",
            "frustration": "情绪会放大风险。24小时后再看。",
        },
    },
    "学习场": {
        "description": "学习新知识、技能、方法",
        "keywords": ["学习", "学", "教程", "怎么", "如何", "什么是", "解释", "原理", "概念", "入门", "基础"],
        "core": ["identity", "priorities", "conversation"],
        "activate": {
            "knowledge": {"min_temp": 0.15, "max_count": 5, "source": None, "field": ["knowledge", "method"]},
            "resource": {"min_temp": 0.2, "max_count": 3, "source": None, "field": ["resource", "tool"]},
            "project": {"min_temp": 0.25, "max_count": 2, "source": None, "field": ["project"]},
        },
        "suppress": ["finance", "risk_aversion"],
        "emotional_tuning": {
            "anxiety": "学习是螺旋上升，不是线性。卡住是正常的。",
            "excitement": "很好，但要警惕'收藏即学会'。马上动手试。",
        },
    },
}


def detect_field(message: str) -> str:
    """识别当前情境类型。"""
    text = message.lower()
    for field_name, profile in FIELD_PROFILES.items():
        if field_name == "通用场":
            continue
        for kw in profile["keywords"]:
            if kw in text:
                return field_name
    return "通用场"


def build_field(message: str, snapshot: dict | None = None) -> dict:
    """构建记忆场。"""
    field_name = detect_field(message)
    profile = FIELD_PROFILES.get(field_name, FIELD_PROFILES["通用场"])
    
    db = _get_db()
    candidates = []
    
    # 核心层
    core_ids = []
    if snapshot and "me" in snapshot:
        me = snapshot["me"]
        priorities = me.get("top_priorities", [])
        for p in priorities:
            candidates.append({
                "id": f"priority:{p.get('rank', 0)}",
                "content": f"P{p.get('rank', 0)}: {p.get('title', '')}",
                "type": "priority",
                "temperature": 1.0,
                "layer": "core",
            })
    
    # 情境层
    for zone_name, config in profile["activate"].items():
        min_temp = config["min_temp"]
        max_count = config["max_count"]
        field_filter = config.get("field")
        
        if field_filter:
            placeholders = ",".join("?" * len(field_filter))
            rows = db.execute(
                f"SELECT * FROM entries WHERE status = 'active' AND field IN ({placeholders})",
                tuple(field_filter),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM entries WHERE status = 'active'").fetchall()
        
        entries = [dict(row) for row in rows]
        heated = filter_by_temperature(entries, min_temp=min_temp)
        
        for entry in heated[:max_count]:
            candidates.append({
                "id": entry["id"],
                "content": entry["content"],
                "type": entry["type"],
                "temperature": entry.get("temperature", 0.5),
                "layer": "context",
                "zone": zone_name,
            })
    
    # 按温度排序
    candidates.sort(key=lambda x: x["temperature"], reverse=True)
    
    return {
        "field": field_name,
        "description": profile["description"],
        "candidates": candidates,
        "suppress": profile["suppress"],
        "emotional_tuning": profile["emotional_tuning"],
    }


def format_field_for_prompt(field_result: dict) -> str:
    """将记忆场格式化为 prompt 文本。"""
    lines = [f"【当前情境: {field_result['field']}】"]
    
    core = [c for c in field_result["candidates"] if c.get("layer") == "core"]
    context = [c for c in field_result["candidates"] if c.get("layer") == "context"]
    
    if core:
        lines.append("核心记忆：")
        for c in core:
            lines.append(f"  • {c['content'][:60]}")
    
    if context:
        lines.append("情境记忆：")
        for c in context[:5]:
            lines.append(f"  • [{c.get('zone', '?')}] {c['content'][:60]} (温度: {c['temperature']:.2f})")
    
    return "\n".join(lines)


def detect_emotional_state(message: str) -> str | None:
    """检测情绪状态。"""
    text = message.lower()
    patterns = {
        "anxiety": ["焦虑", "担心", "害怕", "紧张", "压力", "慌", "不确定", "迷茫"],
        "excitement": ["兴奋", "激动", "开心", "期待", "机会", "太好了"],
        "frustration": ["沮丧", "失望", "挫败", "生气", "烦", "累", "不想"],
        "pride": ["自豪", "成就感", "做到了", "成功", "满意"],
    }
    for emotion, keywords in patterns.items():
        for kw in keywords:
            if kw in text:
                return emotion
    return None
