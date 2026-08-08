import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database
from endpoints import automation


def test_orphan_recovery_deduplicates_same_douyin_short_link(monkeypatch, tmp_path):
    summary_dir = tmp_path / "douyin-summaries"
    summary_dir.mkdir()
    (summary_dir / "first.md").write_text("# First\nhttps://v.douyin.com/recovery-contract/\nfirst body", encoding="utf-8")
    (summary_dir / "second.md").write_text("# Second\nhttps://v.douyin.com/recovery-contract/\nsecond body", encoding="utf-8")

    class VectorStore:
        def add_document(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr(automation, "PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr(automation, "chunk_text", lambda content: [content])
    monkeypatch.setattr(automation, "get_vector_store", lambda: VectorStore())
    conn = database.get_db()
    conn.execute("DELETE FROM document_source_claims WHERE source = 'douyin-summary' AND source_key = 'douyin:short:recovery-contract'")
    conn.execute("DELETE FROM documents WHERE source_key = 'douyin:short:recovery-contract' OR title IN ('First', 'Second')")
    conn.commit()
    conn.close()

    first = automation.recover_orphan_summaries()
    second = automation.recover_orphan_summaries()

    conn = database.get_db()
    conn.execute("DELETE FROM document_source_claims WHERE source = 'douyin-summary' AND source_key = 'douyin:short:recovery-contract'")
    docs = conn.execute(
        "SELECT id, source_key FROM documents WHERE source_key = 'douyin:short:recovery-contract' AND document_status = 'active'"
    ).fetchall()
    conn.execute("DELETE FROM documents WHERE source_key = 'douyin:short:recovery-contract'")
    conn.commit()
    conn.close()

    assert len(docs) == 1
    assert first["recovered"] == 1
    assert second["recovered"] == 0
