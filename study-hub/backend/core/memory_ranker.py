"""
记忆混合加权排序模块

得分公式：score = access_count * 0.5 + confidence * 0.3 + recency * 0.2
其中 recency = 1 / (1 + days_since_last_access)，越近越高
"""

from datetime import datetime
from typing import List, Dict, Any


def calculate_memory_score(row: Dict[str, Any]) -> float:
    """计算单条记忆的综合得分

    参数:
        row: 记忆行数据（sqlite3.Row 或 dict），需包含 access_count, confidence, last_accessed, created_at

    返回:
        综合得分（float）
    """
    access_count = row.get("access_count") or 0
    confidence = row.get("confidence") or 0.0

    # 计算 recency：基于 last_accessed 或 created_at
    last_accessed = row.get("last_accessed")
    if last_accessed:
        try:
            # 解析 ISO 格式时间字符串
            last_dt = datetime.fromisoformat(str(last_accessed).replace("Z", "+00:00"))
            days_since = (datetime.now() - last_dt).days
            if days_since < 0:
                days_since = 0
        except (ValueError, TypeError):
            days_since = 30  # 解析失败时给一个中等衰减
    else:
        # 没有 last_accessed，用 created_at
        created_at = row.get("created_at")
        if created_at:
            try:
                created_dt = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                days_since = (datetime.now() - created_dt).days
                if days_since < 0:
                    days_since = 0
            except (ValueError, TypeError):
                days_since = 30
        else:
            days_since = 30

    recency = 1.0 / (1.0 + days_since)

    # 加权得分
    score = access_count * 0.5 + confidence * 0.3 + recency * 0.2
    return score


def rank_memories(rows: List[Any], top_k: int = 3) -> List[Any]:
    """对记忆列表按综合得分排序，返回 top_k 条

    参数:
        rows: 记忆行列表
        top_k: 返回条数（默认 3）

    返回:
        排序后的前 top_k 条记忆
    """
    scored = [(row, calculate_memory_score(row)) for row in rows]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [row for row, _ in scored[:top_k]]
