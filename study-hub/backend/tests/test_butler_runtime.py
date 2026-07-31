import database
import pytest


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


def _investigating_case(runtime):
    case = runtime.open_case(task_type="bug", description="保存失败")
    runtime.record_context(case["id"], project_index_hits=[], owner_files=[])
    return runtime.assign(case["id"], role="debugger")


def test_high_risk_change_cannot_enter_implementation_before_confirmation():
    from butler.runtime import ButlerRuntime
    from butler.models import ButlerStateError

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(task_type="change", description="删除旧数据")
    runtime.record_context(case["id"], project_index_hits=[], owner_files=[])
    approval = runtime.request_approval(
        case["id"], risk_kind="data", summary="将删除旧数据"
    )

    with pytest.raises(ButlerStateError, match="approval"):
        runtime.begin_implementation(case["id"])

    runtime.resolve_approval(approval["id"], approved=True, response="确认")
    assert runtime.begin_implementation(case["id"])["status"] == "implementing"


def test_third_unsuccessful_attempt_blocks_the_case():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _investigating_case(runtime)
    for index in range(3):
        outcome = runtime.record_attempt(
            case["id"],
            action=f"检查 {index}",
            result="failed",
            learned="排除一种可能",
        )

    assert outcome["status"] == "blocked"
    assert outcome["attempt_count"] == 3


def test_rejected_approval_blocks_case_and_explicit_resume_keeps_history():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(task_type="change", description="更换部署启动方式")
    runtime.record_context(case["id"], project_index_hits=[], owner_files=[])
    approval = runtime.request_approval(
        case["id"], risk_kind="deployment", summary="将调整启动脚本"
    )

    runtime.resolve_approval(approval["id"], approved=False, response="暂不处理")
    resumed = runtime.resume(case["id"], direction="先只调查影响范围")

    assert resumed["status"] == "investigating"
    assert resumed["attempt_count"] == 0
    assert [event["type"] for event in runtime.events(case["id"])] == [
        "received",
        "context_recorded",
        "approval_requested",
        "approval_resolved",
        "resumed",
    ]


def _implementing_case(runtime):
    case = _investigating_case(runtime)
    return runtime.begin_implementation(case["id"])


def test_changed_case_requires_audit_and_original_behavior_validation_before_completion():
    from butler.runtime import ButlerRuntime
    from butler.models import ButlerStateError

    runtime = ButlerRuntime(database.get_db)
    case = _implementing_case(runtime)
    runtime.record_change(
        case["id"],
        summary="修复提交状态",
        files=["frontend/src/components/ContentImportWorkspace.vue"],
    )

    with pytest.raises(ButlerStateError, match="audit"):
        runtime.complete(case["id"])

    runtime.record_audit(
        case["id"],
        verdict="passed",
        checklist={
            "null": "passed",
            "boundary": "passed",
            "error": "passed",
            "impact": "passed",
            "regression": "passed",
            "pattern": "passed",
        },
    )
    with pytest.raises(ButlerStateError, match="validation"):
        runtime.complete(case["id"])

    runtime.record_validation(
        case["id"],
        passed=True,
        evidence="确认解析后出现进度",
    )
    assert runtime.complete(case["id"])["status"] == "completed"


def test_failed_validation_returns_case_to_investigation_and_counts_attempt():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _implementing_case(runtime)
    runtime.record_change(case["id"], summary="修复保存", files=["frontend/src/views/Home.vue"])
    runtime.record_audit(
        case["id"],
        verdict="passed",
        checklist={key: "passed" for key in ("null", "boundary", "error", "impact", "regression", "pattern")},
    )

    outcome = runtime.record_validation(case["id"], passed=False, evidence="保存仍失败")

    assert outcome["status"] == "investigating"
    assert outcome["attempt_count"] == 1


def _completed_case(runtime):
    case = _implementing_case(runtime)
    runtime.record_change(case["id"], summary="修复保存", files=["frontend/src/views/Home.vue"])
    runtime.record_audit(
        case["id"],
        verdict="passed",
        checklist={key: "passed" for key in ("null", "boundary", "error", "impact", "regression", "pattern")},
    )
    runtime.record_validation(case["id"], passed=True, evidence="保存成功")
    return runtime.complete(case["id"])


def test_memory_draft_never_writes_project_memory_before_user_confirmation():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _completed_case(runtime)
    draft = runtime.create_memory_draft(
        case["id"],
        target_path="project-memory/frontend/问题.md",
        content="保存状态问题的验证方式",
    )

    assert draft["status"] == "pending"
    assert runtime.resolve_memory_draft(draft["id"], approved=False)["status"] == "rejected"
    assert runtime.list_memory_drafts(case_id=case["id"])[0]["content"] == "保存状态问题的验证方式"


def test_approved_memory_draft_records_intent_but_never_performs_a_write():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = _completed_case(runtime)
    draft = runtime.create_memory_draft(
        case["id"], target_path="project-memory/frontend/问题.md", content="保存验证方式"
    )

    approved = runtime.resolve_memory_draft(draft["id"], approved=True, response="确认")

    assert approved["status"] == "approved"
    resolution_event = runtime.events(case["id"])[-1]
    assert resolution_event["payload"]["requested_operation"] == {
        "kind": "write_memory",
        "target_path": "project-memory/frontend/问题.md",
        "content": "保存验证方式",
    }
