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


def test_archive_duplicates_only_changes_explicitly_approved_keys():
    reconciliation = importlib.import_module("knowledge_reconciliation")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY, source TEXT, source_key TEXT, document_status TEXT,
            duplicate_of_document_id INTEGER, asr_status TEXT, created_at TEXT, title TEXT, content TEXT,
            source_url TEXT DEFAULT '', content_hash TEXT DEFAULT '', updated_at TEXT DEFAULT ''
        );
        INSERT INTO documents VALUES
          (1, 'douyin-summary', 'douyin:1', 'active', NULL, 'succeeded', '2026-08-01 10:00:00', 'keeper', 'a', '', '', ''),
          (2, 'douyin-summary', 'douyin:1', 'active', NULL, 'failed', '2026-08-01 09:00:00', 'duplicate', 'b', '', '', ''),
          (3, 'douyin-summary', 'douyin:2', 'active', NULL, 'succeeded', '2026-08-01 10:00:00', 'other', 'c', '', '', '');
    """)

    manifest = reconciliation.archive_duplicates(conn, {"douyin:1"})
    rows = conn.execute("SELECT id, document_status, duplicate_of_document_id FROM documents ORDER BY id").fetchall()

    assert manifest == [{"source": "douyin-summary", "source_key": "douyin:1", "keep_id": 1, "archived_ids": [2]}]
    assert [tuple(row) for row in rows] == [(1, "active", None), (2, "archived_duplicate", 1), (3, "active", None)]
