import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database
from endpoints import automation


def test_reparse_queues_an_in_place_task_and_keeps_the_existing_document(monkeypatch):
    conn = database.get_db()
    cur = conn.execute(
        """INSERT INTO documents
           (title, content, source, asr_status, document_status)
           VALUES (?, ?, 'douyin-summary', 'failed', 'active')""",
        ("reparse-contract", "# Summary\nhttps://v.douyin.com/contract/"),
    )
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()

    monkeypatch.setattr(automation._executor, "submit", lambda *_args, **_kwargs: None)
    response = automation.reparse_document(doc_id)

    assert response["status"] == "queued"
    assert response["document_id"] == doc_id
    conn = database.get_db()
    document = conn.execute("SELECT content, asr_status FROM documents WHERE id = ?", (doc_id,)).fetchone()
    task = conn.execute(
        "SELECT document_id, reparse_mode, replace_doc_id FROM task_queue WHERE task_id = ?",
        (response["task_id"],),
    ).fetchone()
    conn.execute("DELETE FROM task_queue WHERE task_id = ?", (response["task_id"],))
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    assert document["content"].startswith("# Summary")
    assert document["asr_status"] == "pending"
    assert task["document_id"] == doc_id
    assert task["reparse_mode"] == "in_place"
    assert task["replace_doc_id"] is None


def test_in_place_worker_updates_the_target_row_and_rebuilds_its_vectors(monkeypatch):
    conn = database.get_db()
    cur = conn.execute(
        """INSERT INTO documents
           (title, content, source, asr_status, document_status)
           VALUES ('worker-contract', 'old transcript https://v.douyin.com/worker/', 'douyin-summary', 'pending', 'active')"""
    )
    doc_id = cur.lastrowid
    before_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.commit()
    conn.close()

    class Collection:
        def get(self, **_kwargs):
            return {"ids": []}

        def delete(self, **_kwargs):
            raise AssertionError("no existing vector ids should be deleted in this test")

    class VectorStore:
        collection = Collection()

        def __init__(self):
            self.added = []

        def add_document(self, got_doc_id, _title, chunks):
            self.added.append((got_doc_id, chunks))

    vector_store = VectorStore()
    monkeypatch.setattr(automation, "_extract_douyin_raw", lambda *_args, **_kwargs: {"platform": "Douyin", "title": "Worker title", "video_id": "123"})
    monkeypatch.setattr(automation, "_run_claude", lambda *_args, **_kwargs: {"content": "# Worker title\nnew transcript"})
    monkeypatch.setattr(automation, "_cleanup_tutorial_workspace", lambda *_args: None)
    monkeypatch.setattr(automation, "chunk_text", lambda content: [content])
    monkeypatch.setattr(automation, "get_vector_store", lambda: vector_store)

    task_id = "in-place-worker-contract"
    automation._tasks[task_id] = {
        "task_id": task_id,
        "module_id": "douyin-summary",
        "module_name": "Douyin",
        "input": "https://v.douyin.com/worker/",
        "status": "pending",
        "progress": "",
        "created_at": "2026-08-08 00:00:00",
        "document_id": doc_id,
        "reparse_mode": "in_place",
        "asr_status": "pending",
        "include_tutorial": False,
    }
    try:
        automation._process_single_task(task_id)
        conn = database.get_db()
        document = conn.execute("SELECT content, asr_status FROM documents WHERE id = ?", (doc_id,)).fetchone()
        after_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        conn.execute("DELETE FROM task_queue WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
    finally:
        automation._tasks.pop(task_id, None)

    assert document["content"] == "# Worker title\nnew transcript"
    assert document["asr_status"] == "succeeded"
    assert after_count == before_count
    assert vector_store.added == [(doc_id, ["# Worker title\nnew transcript"])]


def test_reparseable_documents_use_stored_asr_status_not_markdown_markers():
    conn = database.get_db()
    conn.execute("DELETE FROM documents WHERE title LIKE 'reparseable-status-%'")
    conn.executemany(
        """INSERT INTO documents (title, content, source, asr_status, document_status)
           VALUES (?, ?, 'douyin-summary', ?, 'active')""",
        [
            ("reparseable-status-fallback", "normal body", "fallback"),
            ("reparseable-status-failed", "normal body", "failed"),
            ("reparseable-status-success", "语音提取失败 marker must not control state", "succeeded"),
        ],
    )
    conn.commit()
    conn.close()

    response = automation.list_reparseable()

    conn = database.get_db()
    conn.execute("DELETE FROM documents WHERE title LIKE 'reparseable-status-%'")
    conn.commit()
    conn.close()
    titles = {item["title"] for item in response["documents"]}
    assert "reparseable-status-fallback" in titles
    assert "reparseable-status-failed" in titles
    assert "reparseable-status-success" not in titles


def test_historical_asr_backfill_sets_explicit_status_only_when_unset():
    from knowledge_reconciliation import backfill_asr_statuses

    conn = database.get_db()
    conn.execute("DELETE FROM documents WHERE title LIKE 'asr-backfill-contract-%'")
    conn.executemany(
        """INSERT INTO documents (title, content, source, asr_status, document_status)
           VALUES (?, ?, 'douyin-summary', ?, 'active')""",
        [
            ("asr-backfill-contract-failed", "语音提取失败，请重试", "not_applicable"),
            ("asr-backfill-contract-fallback", "Level 3 基于视频标题生成的摘要", "not_applicable"),
            ("asr-backfill-contract-existing", "语音提取失败", "succeeded"),
        ],
    )
    conn.commit()

    result = backfill_asr_statuses(conn)
    rows = conn.execute(
        "SELECT title, asr_status FROM documents WHERE title LIKE 'asr-backfill-contract-%' ORDER BY title"
    ).fetchall()
    conn.execute("DELETE FROM documents WHERE title LIKE 'asr-backfill-contract-%'")
    conn.commit()
    conn.close()

    statuses = {row["title"]: row["asr_status"] for row in rows}
    assert result["failed"] == 1
    assert result["fallback"] == 1
    assert statuses["asr-backfill-contract-failed"] == "failed"
    assert statuses["asr-backfill-contract-fallback"] == "fallback"
    assert statuses["asr-backfill-contract-existing"] == "succeeded"


def test_task_status_reads_persisted_document_asr_state():
    conn = database.get_db()
    cur = conn.execute(
        "INSERT INTO documents (title, content, source, asr_status) VALUES ('task-status-contract', 'body', 'douyin-summary', 'failed')"
    )
    doc_id = cur.lastrowid
    conn.execute(
        """INSERT INTO task_queue (task_id, module_id, input_text, status, document_id, reparse_mode, asr_status, asr_error)
           VALUES ('task-status-contract', 'douyin-summary', 'https://v.douyin.com/task/', 'error', ?, 'in_place', 'failed', 'token=secret')""",
        (doc_id,),
    )
    conn.commit()
    conn.close()

    response = automation.get_task_processing_status("task-status-contract")

    conn = database.get_db()
    conn.execute("DELETE FROM task_queue WHERE task_id = 'task-status-contract'")
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    assert response["task_id"] == "task-status-contract"
    assert response["document_id"] == doc_id
    assert response["asr_status"] == "failed"
    assert "secret" not in response["asr_error"]
