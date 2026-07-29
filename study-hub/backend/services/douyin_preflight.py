import json
import uuid

from services.douyin_access import DouyinAccessGate
from services.douyin_resolver import DouyinResolveError, extract_douyin_urls


def public_item(row):
    return {
        "item_id": row["item_id"],
        "input_url": row["input_url"],
        "canonical_url": row["canonical_url"],
        "work_id": row["work_id"],
        "title": row["title"],
        "author": row["author"],
        "duration_seconds": row["duration_seconds"],
        "status": row["status"],
        "content_sources": json.loads(row["content_sources"] or "[]"),
        "task_id": row["task_id"],
        "error_code": row["error_code"],
        "error_message": row["error_message"],
    }


async def create_preflight(conn, raw_input, resolver, cookie="", gate=None):
    urls = extract_douyin_urls(raw_input)
    batch_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO douyin_preflight_batches (batch_id, raw_input, status) VALUES (?, ?, 'preflighting')",
        (batch_id, raw_input),
    )
    access = gate or DouyinAccessGate()
    seen_work_ids = set()
    for url in urls:
        item_id = str(uuid.uuid4())
        try:
            work = await access.run(conn, lambda url=url: resolver.resolve(url, cookie=cookie))
            duplicate = work.work_id in seen_work_ids
            seen_work_ids.add(work.work_id)
            sources = work.content_sources()
            status = "duplicate" if duplicate else ("ready" if sources else "needs_local_file")
            resolver_data = {
                "work_id": work.work_id,
                "canonical_url": work.canonical_url,
                "subtitle_texts": work.subtitle_texts,
                "subtitle_urls": work.subtitle_urls,
                "audio_urls": work.audio_urls,
                "media_urls": work.media_urls,
                "download_permission": work.download_permission,
            }
            conn.execute(
                """INSERT INTO douyin_preflight_items
                   (item_id, batch_id, input_url, canonical_url, work_id, title, author,
                    duration_seconds, status, content_sources, resolver_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, batch_id, url, work.canonical_url, work.work_id, work.title,
                 work.author or "", work.duration_seconds, status,
                 json.dumps(sources, ensure_ascii=False),
                 json.dumps(resolver_data, ensure_ascii=False)),
            )
        except DouyinResolveError as exc:
            status = "blocked" if exc.code in {
                "cookie_required", "cookie_expired", "access_forbidden",
                "rate_limited", "risk_verification", "daily_limit_exceeded",
            } else "failed"
            conn.execute(
                """INSERT INTO douyin_preflight_items
                   (item_id, batch_id, input_url, status, error_code, error_message)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (item_id, batch_id, url, status, exc.code, str(exc)),
            )
    conn.commit()
    rows = conn.execute(
        "SELECT * FROM douyin_preflight_items WHERE batch_id = ? ORDER BY created_at, rowid",
        (batch_id,),
    ).fetchall()
    batch_status = "ready" if any(row["status"] == "ready" for row in rows) else "blocked"
    if all(row["status"] == "failed" for row in rows):
        batch_status = "failed"
    conn.execute(
        "UPDATE douyin_preflight_batches SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE batch_id = ?",
        (batch_status, batch_id),
    )
    conn.commit()
    return {"batch_id": batch_id, "status": batch_status, "items": [public_item(row) for row in rows]}


def get_preflight(conn, batch_id):
    batch = conn.execute(
        "SELECT * FROM douyin_preflight_batches WHERE batch_id = ?", (batch_id,)
    ).fetchone()
    if not batch:
        return None
    rows = conn.execute(
        "SELECT * FROM douyin_preflight_items WHERE batch_id = ? ORDER BY created_at, rowid",
        (batch_id,),
    ).fetchall()
    return {"batch_id": batch_id, "status": batch["status"], "items": [public_item(row) for row in rows]}
