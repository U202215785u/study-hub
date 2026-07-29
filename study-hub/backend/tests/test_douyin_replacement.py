import hashlib

import database
import pytest

from services.douyin_content import finalize_replacement


def _doc(conn, title, content):
    cursor = conn.execute(
        "INSERT INTO documents (title, content, content_type, source, char_count, content_hash) VALUES (?, ?, 'text', 'douyin-summary', ?, ?)",
        (title, content, len(content), hashlib.sha256(content.encode()).hexdigest()),
    )
    conn.commit()
    return cursor.lastrowid


@pytest.fixture(autouse=True)
def clean_replacement_rows():
    conn = database.get_db()
    conn.execute("DELETE FROM document_replacement_audit")
    conn.execute("DELETE FROM documents WHERE source='douyin-summary'")
    conn.commit()
    conn.close()


@pytest.mark.parametrize("content", ["too short", "# title\n\n⚠️ 语音提取失败：network"])
def test_failed_quality_retains_old_document(content):
    conn = database.get_db()
    old_id = _doc(conn, "old", "old valid article content that must remain")
    new_id = _doc(conn, "new", content)
    assert finalize_replacement(conn, "quality-task", old_id, new_id) is False
    assert conn.execute("SELECT 1 FROM documents WHERE id=?", (old_id,)).fetchone()
    audit = conn.execute(
        "SELECT decision FROM document_replacement_audit WHERE task_id='quality-task' ORDER BY id DESC"
    ).fetchone()
    assert audit[0] == "retained"
    conn.close()


def test_valid_new_document_is_reread_before_old_is_removed():
    conn = database.get_db()
    old_id = _doc(conn, "old", "old article")
    new_id = _doc(conn, "new", "# New\n\nThis is a complete recognized transcript and summary.")
    assert finalize_replacement(conn, "valid-task", old_id, new_id) is True
    assert conn.execute("SELECT 1 FROM documents WHERE id=?", (old_id,)).fetchone() is None
    assert conn.execute("SELECT 1 FROM documents WHERE id=?", (new_id,)).fetchone()
    conn.close()


def test_reread_failure_retains_old_document():
    conn = database.get_db()
    old_id = _doc(conn, "old", "old article")
    assert finalize_replacement(conn, "missing-task", old_id, -999) is False
    assert conn.execute("SELECT 1 FROM documents WHERE id=?", (old_id,)).fetchone()
    conn.close()
