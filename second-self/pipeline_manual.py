"""手动录入 — 增强型内容入库。"""
from memory_store import insert_entry


def ingest_enhanced(content: str, domain: str = "ai-learning", title: str = "未命名", user_note: str = "") -> dict:
    """增强型内容录入。"""
    full_content = f"# {title}\n\n{content}"
    if user_note:
        full_content += f"\n\n## 用户备注\n{user_note}"
    
    entry_id = insert_entry(
        source="ingest",
        type="capture",
        content=full_content,
        context={"domain": domain, "title": title, "user_note": user_note},
        significance="B",
        field="knowledge",
    )
    return {"ok": True, "entry_id": entry_id, "title": title}
