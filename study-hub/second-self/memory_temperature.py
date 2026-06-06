"""记忆温度系统 — 模拟人脑记忆的激活强度

温度 = 记忆被激活的容易程度
- 烫 (0.8-1.0): 刚发生、高频使用、情绪强烈、深度核心
- 温 (0.4-0.8): 近期用过、有一定关联
- 凉 (0.1-0.4): 很久不用、关联弱
- 冻 (0.0-0.1): 休眠状态、几乎不激活
"""
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path

from memory_store import _get_db, get_entry, update_hit


TEMPERATURE_CONFIG = {
    "time_decay_per_day": 0.02,
    "time_decay_max": 0.3,
    "emotional_bonus": {
        "high": 0.25,
        "anxiety": 0.2,
        "excitement": 0.2,
        "frustration": 0.15,
        "pride": 0.15,
        "neutral": 0.0,
    },
    "hit_count_multiplier": 0.015,
    "hit_count_max": 0.15,
    "semantic_max": 0.2,
    "depth_bonus": {
        "core": 0.2,
        "deep": 0.1,
        "surface": 0.0,
    },
    "dormant_cap": 0.1,
}


def calculate_temperature(entry: dict, context: dict | None = None) -> float:
    """计算记忆的温度（0.0-1.0）。"""
    temp = 0.0
    config = TEMPERATURE_CONFIG
    
    last_hit = entry.get("last_hit_at")
    if last_hit:
        try:
            last_dt = datetime.fromisoformat(last_hit)
            days_since = (datetime.now() - last_dt).days
            time_bonus = max(0, config["time_decay_max"] - days_since * config["time_decay_per_day"])
            temp += time_bonus
        except (ValueError, TypeError):
            pass
    
    emotional_tag = entry.get("emotional_tag")
    if emotional_tag:
        bonus = config["emotional_bonus"].get(emotional_tag, 0.0)
        temp += bonus
    
    hit_count = entry.get("hit_count", 0) or 0
    freq_bonus = min(config["hit_count_max"], hit_count * config["hit_count_multiplier"])
    temp += freq_bonus
    
    if context and "message" in context:
        semantic_sim = _semantic_similarity(entry.get("content", ""), context["message"])
        temp += semantic_sim * config["semantic_max"]
    
    depth = entry.get("depth", "surface")
    temp += config["depth_bonus"].get(depth, 0.0)
    
    if entry.get("status") == "dormant":
        temp = min(temp, config["dormant_cap"])
    
    return round(min(1.0, max(0.0, temp)), 3)


def batch_calculate_temperature(entry_ids: list[str], context: dict | None = None) -> dict[str, float]:
    """批量计算温度。"""
    results = {}
    for eid in entry_ids:
        entry = get_entry(eid)
        if entry:
            results[eid] = calculate_temperature(entry, context)
    return results


def filter_by_temperature(entries: list[dict], min_temp: float = 0.0, max_temp: float = 1.0, context: dict | None = None) -> list[dict]:
    """按温度筛选记忆。"""
    results = []
    for entry in entries:
        temp = calculate_temperature(entry, context)
        if min_temp <= temp <= max_temp:
            entry["temperature"] = temp
            results.append(entry)
    results.sort(key=lambda x: x["temperature"], reverse=True)
    return results


def _semantic_similarity(text_a: str, text_b: str) -> float:
    """计算两段文本的语义相似度（简化版）。"""
    def extract_keywords(text):
        words = set()
        for w in re.findall(r'[\u4e00-\u9fff]{2,}', text):
            words.add(w)
        for w in re.findall(r'[a-zA-Z]{3,}', text.lower()):
            words.add(w)
        return words
    
    kw_a = extract_keywords(text_a)
    kw_b = extract_keywords(text_b)
    
    if not kw_a or not kw_b:
        return 0.0
    
    intersection = len(kw_a & kw_b)
    union = len(kw_a | kw_b)
    
    if union == 0:
        return 0.0
    
    return round(intersection / union, 3)


def print_temperature_report(limit: int = 20):
    """打印温度报告。"""
    db = _get_db()
    rows = db.execute("SELECT * FROM entries WHERE status = 'active' ORDER BY hit_count DESC").fetchall()
    
    print("=== 记忆温度报告 ===")
    print(f"{'ID':<20} {'Field':<12} {'Depth':<8} {'Hit':<5} {'Temp':<6} {'Preview'}")
    print("-" * 80)
    
    for row in rows[:limit]:
        entry = dict(row)
        temp = calculate_temperature(entry)
        preview = entry.get("content", "")[:30].replace("\n", " ")
        print(f"{entry['id']:<20} {entry.get('field', '?'):<12} {entry.get('depth', '?'):<8} {entry.get('hit_count', 0):<5} {temp:<6.2f} {preview}")


if __name__ == "__main__":
    print_temperature_report()
