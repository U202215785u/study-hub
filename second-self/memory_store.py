"""记忆存储 — SQLite + 关键词搜索。

核心表：
- entries: 记忆条目
- links: 记忆关联
- retrieval_log: 检索日志
- entities: 实体
- entry_entities: 条目-实体关联
- causal_links: 因果链接
- temporal_links: 时序链接
"""
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from gateway_paths import ROOT

_DB_PATH = ROOT / ".memory" / "entries.db"
_db_instance = None


def _get_db() -> sqlite3.Connection:
    """获取数据库连接（单例）。"""
    global _db_instance
    if _db_instance is None:
        _db_instance = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _db_instance.row_factory = sqlite3.Row
    return _db_instance


def _next_id() -> str:
    """生成下一个记忆 ID。"""
    now = datetime.now().strftime("%Y%m%d")
    db = _get_db()
    c = db.execute("SELECT COUNT(*) FROM entries WHERE id LIKE ?", (f"mem-{now}-%",))
    count = c.fetchone()[0] + 1
    return f"mem-{now}-{count:04d}"


def get_entry(entry_id: str) -> dict:
    """获取单条记忆。"""
    db = _get_db()
    c = db.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
    row = c.fetchone()
    if not row:
        return {}
    return dict(row)


def get_stats() -> dict:
    """获取记忆统计。"""
    db = _get_db()
    c = db.execute("SELECT COUNT(*) FROM entries WHERE status = 'active'")
    active = c.fetchone()[0]
    c = db.execute("SELECT COUNT(*) FROM entries WHERE status = 'dormant'")
    dormant = c.fetchone()[0]
    return {"total": active + dormant, "active": active, "dormant": dormant}


def insert_entry(
    source: str,
    type: str,
    content: str,
    context: dict | None = None,
    significance: str = "auto",
    field: str = "knowledge",
    depth: str = "surface",
) -> str:
    """插入新记忆条目。"""
    entry_id = _next_id()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db = _get_db()
    db.execute(
        """INSERT INTO entries
        (id, source, type, content, context_json, significance, status, created_at, field, depth)
        VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
        (entry_id, source, type, content, json.dumps(context or {}, ensure_ascii=False), significance, now, field, depth),
    )
    db.commit()
    return entry_id


def _search_sql(q: str) -> list[dict]:
    """SQLite LIKE 关键词搜索。"""
    db = _get_db()
    results = []

    keywords = [kw.strip() for kw in q.split() if len(kw.strip()) >= 1]
    if not keywords:
        keywords = [q]

    rows = db.execute(
        "SELECT * FROM entries WHERE status = 'active' ORDER BY hit_count DESC"
    ).fetchall()

    for row in rows:
        content_lower = row["content"].lower()
        match_count = sum(content_lower.count(kw) for kw in keywords)
        if match_count > 0:
            context = json.loads(row["context_json"] or "{}")
            results.append({
                "source": f"memory://{row['id']}",
                "type": row["type"],
                "preview": row["content"][:200],
                "score": match_count,
                "entry_id": row["id"],
                "domain": context.get("domain"),
                "project": context.get("project"),
            })

    if results:
        max_score = max(r["score"] for r in results)
        if max_score > 0:
            for r in results:
                r["score"] = round(r["score"] / max_score, 2)

    return results


def search_memory(query: str, k: int = 5, use_causal: bool = True) -> dict:
    """混合搜索：SQLite 关键词 + 因果检索 + 文件扫描。"""
    q = query.lower().strip()
    if not q:
        return {"query": query, "results": [], "stats": get_stats(), "causal_chains": []}

    results = []
    causal_chains = []

    # 因果记忆检索（默认开启，但容易卡住，这里简化）
    if use_causal:
        try:
            from memory_causal import causal_search
            causal_result = causal_search(query, k=k)
            for r in causal_result.get("results", []):
                results.append({
                    "source": f"memory://{r.get('entry_id', '')}",
                    "type": r.get("type", "causal"),
                    "preview": r.get("content", "")[:200],
                    "score": r.get("score", 0.8),
                    "entry_id": r.get("entry_id", ""),
                    "source_type": r.get("source_type", "causal"),
                })
            causal_chains = causal_result.get("chains", [])
        except Exception:
            pass

    # SQLite 关键词搜索
    results.extend(_search_sql(q))

    # 去重（按 source 去重，保留高分）
    seen = set()
    deduped = []
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        if r["source"] not in seen:
            seen.add(r["source"])
            deduped.append(r)

    top_k = deduped[:k]

    # 记录检索日志
    _log_retrieval(query, top_k, k)

    return {"query": q, "results": top_k, "stats": get_stats(), "causal_chains": causal_chains}


def _log_retrieval(query: str, results: list[dict], k: int) -> None:
    """记录检索日志。"""
    db = _get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for rank, r in enumerate(results, 1):
        try:
            db.execute(
                """INSERT INTO retrieval_log (query_text, query_source, entry_id, score, rank, k_value, searched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (query, "api", r.get("entry_id", ""), r.get("score", 0), rank, k, now),
            )
        except Exception:
            pass
    db.commit()


def ingest(content: str, domain: str = "ai-learning", title: str = "未命名") -> dict:
    """简单内容录入。"""
    entry_id = insert_entry(
        source="ingest",
        type="capture",
        content=content,
        context={"domain": domain, "title": title},
        field="knowledge",
    )
    return {"ok": True, "entry_id": entry_id}
