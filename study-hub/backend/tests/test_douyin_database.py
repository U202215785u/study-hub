import sqlite3

import database


EXPECTED_TABLES = {
    "secure_settings",
    "douyin_preflight_batches",
    "douyin_preflight_items",
    "automation_runtime_state",
    "document_replacement_audit",
}


def test_init_db_adds_douyin_import_tables():
    database.init_db()
    with sqlite3.connect(database.DB_PATH) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert EXPECTED_TABLES <= tables


def test_preflight_work_is_unique_within_a_batch():
    database.init_db()
    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            "INSERT INTO douyin_preflight_batches "
            "(batch_id, raw_input, status) VALUES ('batch-1', 'share', 'ready')"
        )
        conn.execute(
            "INSERT INTO douyin_preflight_items "
            "(item_id, batch_id, input_url, work_id, status) "
            "VALUES ('item-1', 'batch-1', 'https://v.douyin.com/one', '123', 'ready')"
        )

        try:
            conn.execute(
                "INSERT INTO douyin_preflight_items "
                "(item_id, batch_id, input_url, work_id, status) "
                "VALUES ('item-2', 'batch-1', 'https://v.douyin.com/two', '123', 'ready')"
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("duplicate work ID was accepted in one batch")


def test_task_queue_migration_preserves_rows_and_accepts_new_states(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE task_queue (
                task_id TEXT PRIMARY KEY,
                module_id TEXT NOT NULL,
                module_name TEXT DEFAULT '',
                input_text TEXT NOT NULL,
                input_hash TEXT DEFAULT '',
                status TEXT DEFAULT 'pending' CHECK(status IN (
                    'pending','extracting','summarizing','importing','done','error'
                )),
                progress TEXT DEFAULT '',
                error TEXT DEFAULT '',
                result_doc_id INTEGER DEFAULT NULL,
                result_title TEXT DEFAULT '',
                steps_json TEXT DEFAULT '[]',
                current_step TEXT DEFAULT '',
                api_key_error INTEGER DEFAULT 0,
                api_key_error_msg TEXT DEFAULT '',
                replace_doc_id INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO task_queue (task_id, module_id, input_text, status) "
            "VALUES ('legacy-task', 'douyin-summary', 'share', 'pending')"
        )

    monkeypatch.setattr(database, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    database.init_db()

    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT status FROM task_queue WHERE task_id = 'legacy-task'"
        ).fetchone() == ("pending",)
        conn.execute(
            "UPDATE task_queue SET status = 'transcribing' "
            "WHERE task_id = 'legacy-task'"
        )
        conn.execute(
            "UPDATE task_queue SET status = 'validating' "
            "WHERE task_id = 'legacy-task'"
        )

