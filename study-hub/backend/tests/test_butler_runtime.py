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


def test_open_case_persists_original_report_and_returns_locating_action():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(
        task_type="bug",
        description="内容解析确认后一直转圈",
        feature_code="CP.IMPORT.SUBMIT",
    )

    assert case["status"] == "received"
    assert case["description"] == "内容解析确认后一直转圈"
    assert runtime.next_action(case["id"])["kind"] == "locate_context"


def test_record_context_then_assign_debugger_records_handoff_event():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(task_type="bug", description="页面保存失败")
    runtime.record_context(
        case["id"],
        project_index_hits=["P4"],
        owner_files=[".agents/owners/frontend-owner.md"],
    )
    handoff = runtime.assign(
        case["id"],
        role="debugger",
        experts=["frontend-expert", "backend-expert"],
    )

    assert handoff["status"] == "investigating"
    assert [event["type"] for event in runtime.events(case["id"])] == [
        "received",
        "context_recorded",
        "handoff",
    ]


def test_case_remains_available_from_a_new_runtime_instance():
    from butler.runtime import ButlerRuntime

    first_runtime = ButlerRuntime(database.get_db)
    case = first_runtime.open_case(task_type="research", description="研究 Agent 协作方式")

    second_runtime = ButlerRuntime(database.get_db)

    assert second_runtime.get_case(case["id"])["description"] == "研究 Agent 协作方式"
    assert case["id"] in {item["id"] for item in second_runtime.list_cases()}
