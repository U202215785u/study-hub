"""对话蒸馏 — 从对话中提取值得保存的记忆。"""
import json
from datetime import datetime
from typing import Any

from memory_store import insert_entry


# 待确认队列（内存中，重启后清空）
_pending_captures: list[dict] = []


def distill_dialogue(user_message: str, agent_response: str) -> list[str]:
    """从对话中蒸馏记忆。"""
    if not user_message or len(user_message) < 10:
        return []
    
    # 简单规则：用户消息中如果有"决定""选择""放弃"等词，直接捕获
    triggers = ["决定", "选择", "放弃", "开始", "完成", "改变", "发现", "意识到"]
    content = user_message.strip()
    
    if any(t in content for t in triggers):
        entry_id = insert_entry(
            source="chat",
            type="capture",
            content=content,
            context={"trigger": "dialogue_distill", "agent_reply_preview": agent_response[:100]},
            significance="B",
            field="history",
        )
        return [entry_id]
    
    # 放入待确认队列
    _pending_captures.append({
        "content": content,
        "agent_reply": agent_response,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    })
    
    return []


def get_pending_captures() -> list[dict]:
    """获取待确认的记忆捕获。"""
    return _pending_captures


def confirm_pending(index: int, approve: bool = True) -> dict:
    """确认或拒绝待捕获的记忆。"""
    if index < 0 or index >= len(_pending_captures):
        return {"error": "invalid index"}
    
    item = _pending_captures.pop(index)
    
    if approve:
        entry_id = insert_entry(
            source="chat",
            type="capture",
            content=item["content"],
            context={"approved": True, "agent_reply_preview": item["agent_reply"][:100]},
            significance="C",
            field="history",
        )
        return {"ok": True, "entry_id": entry_id, "action": "approved"}
    
    return {"ok": True, "action": "rejected"}
