import importlib
import importlib.util
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_dry_run_groups_same_source_key_without_writing_rows():
    spec = importlib.util.find_spec("knowledge_reconciliation")

    assert spec is not None
    reconciliation = importlib.import_module("knowledge_reconciliation")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            source_key TEXT DEFAULT '',
            source_url TEXT DEFAULT '',
            content_hash TEXT DEFAULT '',
            document_status TEXT NOT NULL DEFAULT 'active',
            asr_status TEXT NOT NULL DEFAULT 'not_applicable',
            created_at TEXT NOT NULL
        );
    """)
    conn.executemany(
        """INSERT INTO documents
           (id, title, content, source, source_key, source_url, content_hash, document_status, asr_status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (1, "fallback", "old", "douyin-summary", "douyin:short:same", "https://v.douyin.com/same/", "old", "active", "fallback", "2026-08-01 10:00:00"),
            (2, "transcript", "new", "douyin-summary", "douyin:short:same", "https://v.douyin.com/same/", "new", "active", "succeeded", "2026-08-01 09:00:00"),
            (3, "unknown", "body", "douyin-summary", "", "", "unknown", "active", "not_applicable", "2026-08-01 11:00:00"),
        ],
    )
    before = [tuple(row) for row in conn.execute("SELECT * FROM documents ORDER BY id")]

    report = reconciliation.build_reconciliation_report(conn)

    after = [tuple(row) for row in conn.execute("SELECT * FROM documents ORDER BY id")]
    assert before == after
    assert report["summary"] == {"active_documents": 3, "duplicate_groups": 1, "unresolved_documents": 1}
    assert report["groups"][0]["keep_id"] == 2
    assert report["groups"][0]["archive_ids"] == [1]
    assert report["unresolved"] == [{"id": 3, "title": "unknown", "source": "douyin-summary"}]
