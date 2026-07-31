import database


def test_initialize_butler_schema_creates_all_runtime_tables():
    from butler.storage import initialize_butler_schema

    conn = database.get_db()
    try:
        initialize_butler_schema(conn)
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        conn.close()

    assert {
        "butler_tasks",
        "butler_events",
        "butler_approvals",
        "butler_evidence",
        "butler_memory_drafts",
    } <= names


def test_database_bootstrap_creates_butler_runtime_tables():
    database.init_db()
    conn = database.get_db()
    try:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        conn.close()

    assert "butler_tasks" in names
