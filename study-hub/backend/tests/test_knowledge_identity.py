import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database


@pytest.fixture
def isolated_database(monkeypatch, tmp_path):
    db_path = tmp_path / "study_hub.db"
    monkeypatch.setattr(database, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    database.init_db()
    conn = database.get_db()
    yield conn
    conn.close()


def test_init_db_adds_identity_and_processing_columns(isolated_database):
    document_columns = {row[1] for row in isolated_database.execute("PRAGMA table_info(documents)")}
    task_columns = {row[1] for row in isolated_database.execute("PRAGMA table_info(task_queue)")}
    tables = {row[0] for row in isolated_database.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}

    assert {
        "source_key",
        "source_url",
        "document_status",
        "duplicate_of_document_id",
        "asr_status",
        "asr_error",
        "updated_at",
    } <= document_columns
    assert {"document_id", "reparse_mode", "asr_status", "asr_error"} <= task_columns
    assert "document_source_claims" in tables


def test_douyin_short_and_long_urls_use_distinct_namespaces():
    spec = importlib.util.find_spec("knowledge_identity")

    assert spec is not None
    identity = importlib.import_module("knowledge_identity")

    assert identity.source_identity("douyin-summary", "https://v.douyin.com/ZWW0XlOlwdM/") == "douyin:short:ZWW0XlOlwdM"
    assert identity.source_identity("douyin-summary", "https://www.douyin.com/video/7634595063334554889") == "douyin:7634595063334554889"
    assert identity.source_identity("douyin-summary", "https://example.com/video/1") is None


def test_new_douyin_import_uses_parser_video_id_as_its_canonical_identity():
    from endpoints.automation import _resolved_source_identity

    source_url, source_key = _resolved_source_identity(
        "douyin-summary",
        "https://v.douyin.com/ZWW0XlOlwdM/",
        {"video_id": "7634595063334554889"},
    )

    assert source_url == "https://www.douyin.com/video/7634595063334554889"
    assert source_key == "douyin:7634595063334554889"
