"""记忆温度系统。

温度表示记忆被激活的容易程度：
- 1.0 = 核心记忆（身份、价值观），几乎总是激活
- 0.5-0.9 = 近期高关联记忆
- 0.1-0.4 = 长期存储的休眠记忆
- < 0.1 = 深度休眠，通常不被激活

温度会随时间衰减（遗忘曲线），被命中时升高。
"""
from datetime import datetime, timedelta
from typing import Any


def calculate_temperature(entry: dict) -> float:
    """计算单条记忆的温度。"""
    base_temp = 0.5
    
    # 深度加成
    depth = entry.get("depth", "surface")
    depth_bonus = {"core": 0.4, "deep": 0.2, "surface": 0.0}.get(depth, 0.0)
    
    # 命中次数加成
    hit_count = entry.get("hit_count", 0)
    hit_bonus = min(hit_count * 0.05, 0.3)
    
    # 时间衰减
    last_hit = entry.get("last_hit_at")
    if last_hit:
        try:
            last = datetime.fromisoformat(last_hit)
            days = (datetime.now() - last).days
            decay = days * 0.02
        except (ValueError, TypeError):
            decay = 0
    else:
        decay = 0
    
    temperature = base_temp + depth_bonus + hit_bonus - decay
    return max(0.0, min(1.0, temperature))


def batch_calculate_temperature(entries: list[dict]) -> list[tuple[dict, float]]:
    """批量计算温度。"""
    return [(entry, calculate_temperature(entry)) for entry in entries]


def update_temperature_on_hit(entry_id: str) -> None:
    """记忆被命中时更新温度。"""
    from memory_store import _get_db
    db = _get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db.execute(
        "UPDATE entries SET hit_count = hit_count + 1, last_hit_at = ? WHERE id = ?",
        (now, entry_id),
    )
    db.commit()


def decay_all_temperatures() -> None:
    """全局温度衰减（由调度器定期调用）。"""
    # 温度是动态计算的，不需要持久化衰减
    pass


def filter_by_temperature(entries: list[dict], min_temp: float = 0.0) -> list[dict]:
    """按温度筛选记忆，返回温度 >= min_temp 的记忆。"""
    heated = []
    for entry in entries:
        temp = calculate_temperature(entry)
        if temp >= min_temp:
            entry = dict(entry)
            entry["temperature"] = temp
            heated.append(entry)
    # 按温度降序排列
    heated.sort(key=lambda x: x.get("temperature", 0), reverse=True)
    return heated
