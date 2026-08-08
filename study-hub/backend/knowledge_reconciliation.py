"""Read-only reconciliation reporting for knowledge-base document identities."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Any

from knowledge_identity import extract_source_url, source_identity


def _keeper_rank(row: sqlite3.Row) -> tuple[int, str, int]:
    """Prefer a successful transcript, then the latest documented result."""
    return (
        1 if row["asr_status"] == "succeeded" else 0,
        row["created_at"] or "",
        row["id"],
    )


def build_reconciliation_report(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return archival candidates without modifying the database."""
    rows = conn.execute(
        """
        SELECT id, title, source, source_key, source_url, content_hash,
               asr_status, created_at
        FROM documents
        WHERE document_status = 'active'
        ORDER BY source ASC, source_key ASC, created_at DESC, id DESC
        """
    ).fetchall()

    known_keys: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
    unresolved: list[dict[str, Any]] = []
    for row in rows:
        if row["source_key"]:
            known_keys[(row["source"], row["source_key"])].append(row)
        else:
            unresolved.append({"id": row["id"], "title": row["title"], "source": row["source"]})

    groups: list[dict[str, Any]] = []
    for (source, source_key), candidates in known_keys.items():
        if len(candidates) < 2:
            continue
        keeper = max(candidates, key=_keeper_rank)
        archive_rows = sorted((row for row in candidates if row["id"] != keeper["id"]), key=lambda row: row["id"])
        groups.append(
            {
                "source": source,
                "source_key": source_key,
                "keep_id": keeper["id"],
                "archive_ids": [row["id"] for row in archive_rows],
                "documents": [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "source_url": row["source_url"],
                        "content_hash": row["content_hash"],
                        "asr_status": row["asr_status"],
                    }
                    for row in candidates
                ],
            }
        )

    groups.sort(key=lambda group: (group["source"], group["source_key"]))
    return {
        "summary": {
            "active_documents": len(rows),
            "duplicate_groups": len(groups),
            "unresolved_documents": len(unresolved),
        },
        "groups": groups,
        "unresolved": unresolved,
    }


def backfill_source_identities(conn: sqlite3.Connection) -> dict[str, int]:
    """Populate safe historical source keys without following short links or archiving rows."""
    rows = conn.execute(
        "SELECT id, source, source_url, content FROM documents WHERE source_key = '' OR source_key IS NULL"
    ).fetchall()
    updated = 0
    unresolved = 0
    for row in rows:
        source_url = row["source_url"] or extract_source_url(row["content"] or "")
        source_key = source_identity(row["source"], source_url or "") if source_url else None
        if not source_key:
            unresolved += 1
            continue
        conn.execute(
            "UPDATE documents SET source_url = ?, source_key = ?, updated_at = datetime('now') WHERE id = ?",
            (source_url, source_key, row["id"]),
        )
        updated += 1
    conn.commit()
    return {"updated": updated, "unresolved": unresolved}


def backfill_asr_statuses(conn: sqlite3.Connection) -> dict[str, int]:
    """Convert known historical body markers into explicit ASR outcomes once."""
    rows = conn.execute(
        """
        SELECT id, content FROM documents
        WHERE source IN ('douyin-summary', 'bilibili-summary', 'xiaohongshu-summary')
          AND asr_status = 'not_applicable'
        """
    ).fetchall()
    result = {"failed": 0, "fallback": 0, "unchanged": 0}
    for row in rows:
        content = row["content"] or ""
        preview = content[:1200]
        if any(marker in content for marker in ("语音提取失败", "语音识别失败", "ASR 失败", "asr_error")) or (
            "API" in preview and any(marker in preview for marker in ("不可用", "欠费", "Invalid API-key"))
        ):
            status, error_key = "failed", "historical_asr_failure_marker"
        elif "Level 3" in content[:1000] and "基于视频标题" in content[:1000]:
            status, error_key = "fallback", "historical_metadata_fallback_marker"
        else:
            result["unchanged"] += 1
            continue
        conn.execute(
            "UPDATE documents SET asr_status = ?, asr_error = ?, updated_at = datetime('now') WHERE id = ?",
            (status, error_key, row["id"]),
        )
        result[status] += 1
    conn.commit()
    return result


def archive_duplicates(conn: sqlite3.Connection, approved_keys: set[str]) -> list[dict[str, Any]]:
    """Reversibly archive only duplicate groups explicitly selected from a dry-run report."""
    manifest: list[dict[str, Any]] = []
    for group in build_reconciliation_report(conn)["groups"]:
        if group["source_key"] not in approved_keys:
            continue
        archive_ids = group["archive_ids"]
        if not archive_ids:
            continue
        placeholders = ",".join("?" for _ in archive_ids)
        conn.execute(
            f"""
            UPDATE documents
            SET document_status = 'archived_duplicate', duplicate_of_document_id = ?, updated_at = datetime('now')
            WHERE id IN ({placeholders}) AND document_status = 'active'
            """,
            [group["keep_id"], *archive_ids],
        )
        manifest.append(
            {
                "source": group["source"],
                "source_key": group["source_key"],
                "keep_id": group["keep_id"],
                "archived_ids": archive_ids,
            }
        )
    conn.commit()
    return manifest
