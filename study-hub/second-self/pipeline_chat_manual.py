"""聊天记录批量导入 — 从导出的聊天记录中提取记忆。"""
import re
from datetime import datetime
from typing import Any

from memory_store import insert_entry


def distill_chat(chat_text: str, context_hint: str = "") -> dict:
    """从单段聊天记录中提取记忆。"""
    lines = [l.strip() for l in chat_text.split("\n") if l.strip()]
    if not lines:
        return {"error": "empty chat"}
    
    content = "\n".join(lines[:10])  # 取前 10 行
    
    entry_id = insert_entry(
        source="chat_distill",
        type="capture",
        content=content,
        context={"context_hint": context_hint, "line_count": len(lines)},
        significance="B",
        field="history",
    )
    return {"ok": True, "entry_id": entry_id, "extracted": len(lines)}


def batch_distill_from_export(chat_text: str, context_hint: str = "", my_aliases: list[str] | None = None) -> dict:
    """从批量导出的聊天记录中提取多条记忆。"""
    lines = chat_text.split("\n")
    extracted = []
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        
        # 简单过滤：包含说话人标记的才提取
        if "：" in line or ":" in line:
            entry_id = insert_entry(
                source="chat_distill",
                type="capture",
                content=line,
                context={"context_hint": context_hint, "batch": True},
                significance="C",
                field="history",
            )
            extracted.append(entry_id)
    
    return {"ok": True, "extracted": len(extracted), "entry_ids": extracted[:20]}
