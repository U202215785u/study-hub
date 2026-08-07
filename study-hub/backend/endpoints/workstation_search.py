import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from database import get_db

router = APIRouter()

CATALOG_PATH = Path(__file__).resolve().parents[2] / "shared" / "workstation-search-catalog.json"
GROUPS = (
    ("features", "功能入口"),
    ("knowledge", "文章与知识"),
    ("records", "工作记录"),
)
MAX_ITEMS_PER_GROUP = 5


def _catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _matches(query: str, *values: str) -> bool:
    needle = query.casefold()
    return any(needle in (value or "").casefold() for value in values)


def _snippet(value: str, query: str, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if not text:
        return ""
    start = text.casefold().find(query.casefold())
    if start < 0:
        return text[:limit]
    before = max(0, start - limit // 3)
    after = min(len(text), start + len(query) + (limit * 2 // 3))
    return f"{'…' if before else ''}{text[before:after]}{'…' if after < len(text) else ''}"


def _route_item(item_id: str, kind: str, title: str, summary: str, path: str) -> dict:
    return {
        "id": item_id,
        "kind": kind,
        "title": title,
        "summary": summary,
        "navigation": {"kind": "route", "path": path, "query": {}},
    }


def search_features(query: str) -> list[dict]:
    return [
        {
            "id": entry["id"],
            "kind": "feature",
            "title": entry["title"],
            "summary": entry["summary"],
            "navigation": entry["navigation"],
        }
        for entry in _catalog()
        if _matches(query, entry["title"], entry["summary"], *entry.get("aliases", []))
    ][:MAX_ITEMS_PER_GROUP]


def search_knowledge(query: str) -> list[dict]:
    like = f"%{query}%"
    conn = get_db()
    try:
        documents = conn.execute(
            """SELECT id, title, content, tags FROM documents
               WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (like, like, like, MAX_ITEMS_PER_GROUP),
        ).fetchall()
        wiki_pages = conn.execute(
            """SELECT id, title, slug, content, summary, tags FROM wiki_pages
               WHERE title LIKE ? OR content LIKE ? OR summary LIKE ? OR tags LIKE ?
               ORDER BY updated_at DESC LIMIT ?""",
            (like, like, like, like, MAX_ITEMS_PER_GROUP),
        ).fetchall()
    finally:
        conn.close()

    items = [
        {
            "id": f"document:{row['id']}",
            "kind": "document",
            "title": row["title"],
            "summary": _snippet(row["content"], query),
            "navigation": {"kind": "document", "document_id": row["id"]},
        }
        for row in documents
    ]
    items.extend(
        _route_item(f"wiki:{row['id']}", "wiki", row["title"], row["summary"] or _snippet(row["content"], query), f"/wiki/{row['slug']}")
        for row in wiki_pages
    )
    return items[:MAX_ITEMS_PER_GROUP]


def search_records(query: str) -> list[dict]:
    like = f"%{query}%"
    conn = get_db()
    try:
        butler_tasks = conn.execute(
            """SELECT id, title, description FROM butler_tasks
               WHERE title LIKE ? OR description LIKE ? ORDER BY updated_at DESC LIMIT ?""",
            (like, like, MAX_ITEMS_PER_GROUP),
        ).fetchall()
        ddl_tasks = conn.execute(
            """SELECT id, title, description FROM ddl_tasks
               WHERE title LIKE ? OR description LIKE ? ORDER BY updated_at DESC LIMIT ?""",
            (like, like, MAX_ITEMS_PER_GROUP),
        ).fetchall()
        journals = conn.execute(
            """SELECT id, date, content FROM journal_entries
               WHERE content LIKE ? ORDER BY date DESC LIMIT ?""",
            (like, MAX_ITEMS_PER_GROUP),
        ).fetchall()
        workflows = conn.execute(
            """SELECT id, name, description, trigger_keywords FROM workflows
               WHERE name LIKE ? OR description LIKE ? OR trigger_keywords LIKE ?
               ORDER BY updated_at DESC LIMIT ?""",
            (like, like, like, MAX_ITEMS_PER_GROUP),
        ).fetchall()
    finally:
        conn.close()

    items = [
        _route_item(f"task:{row['id']}", "task", row["title"], _snippet(row["description"], query), "/workbench")
        for row in butler_tasks
    ]
    items.extend(
        _route_item(f"ddl:{row['id']}", "ddl", row["title"], _snippet(row["description"], query), "/ddl")
        for row in ddl_tasks
    )
    items.extend(
        _route_item(f"journal:{row['id']}", "journal", f"{row['date']} 手账", _snippet(row["content"], query), "/journal")
        for row in journals
    )
    items.extend(
        _route_item(f"workflow:{row['id']}", "workflow", row["name"], _snippet(row["description"], query), "/workflow")
        for row in workflows
    )
    return items[:MAX_ITEMS_PER_GROUP]


def _group(group_id: str, label: str, provider, query: str) -> dict:
    try:
        return {"id": group_id, "label": label, "status": "ready", "items": provider(query)}
    except Exception:
        return {
            "id": group_id,
            "label": label,
            "status": "unavailable",
            "message": f"{label}暂时不可用",
            "items": [],
        }


@router.get("/workstation/search")
def workstation_search(q: str = Query(...)):
    query = q.strip()
    if not query:
        raise HTTPException(status_code=422, detail="请输入搜索内容")
    providers = (search_features, search_knowledge, search_records)
    return {
        "query": query,
        "groups": [_group(group_id, label, provider, query) for (group_id, label), provider in zip(GROUPS, providers)],
        "assistant": {"enabled": False, "label": "问一问 AI 助手", "status": "暂未开放"},
    }
