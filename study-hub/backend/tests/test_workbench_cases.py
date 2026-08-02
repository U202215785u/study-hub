from fastapi import FastAPI
from fastapi.testclient import TestClient

import database


def _client():
    from endpoints.workbench_cases import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _reset_butler_tables():
    conn = database.get_db()
    try:
        for table in (
            "butler_memory_drafts",
            "butler_evidence",
            "butler_approvals",
            "butler_events",
            "butler_tasks",
        ):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
    finally:
        conn.close()


def _runtime():
    from butler.runtime import ButlerRuntime

    return ButlerRuntime(database.get_db)


def _make_case(*, task_type="change", title="Workbench case", description="聚合工作台案件"):
    runtime = _runtime()
    case = runtime.open_case(task_type=task_type, title=title, description=description)
    runtime.record_context(case["id"], project_index_hits=["SH.WORKBENCH"], owner_files=["backend/workbench"])
    runtime.assign(case["id"], role="debugger")
    return runtime, case


def test_cases_list_returns_empty_array_when_no_butler_tasks_exist():
    _reset_butler_tables()

    response = _client().get("/workbench/cases")

    assert response.status_code == 200
    assert response.json() == []


def test_cases_list_filters_and_sorts_source_tasks_by_updated_at():
    _reset_butler_tables()
    runtime, first = _make_case(title="Older backend task", description="needle backend")
    _, second = _make_case(task_type="bug", title="Newer frontend task", description="needle frontend")
    conn = database.get_db()
    try:
        conn.execute("UPDATE butler_tasks SET updated_at = ? WHERE id = ?", ("2026-08-01 10:00:00", first["id"]))
        conn.execute("UPDATE butler_tasks SET updated_at = ? WHERE id = ?", ("2026-08-02 10:00:00", second["id"]))
        conn.commit()
    finally:
        conn.close()

    response = _client().get(
        "/workbench/cases",
        params={"task_type": "bug", "keyword": "frontend", "sort_order": "asc"},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [second["id"]]
    assert response.json()[0]["status"] == "investigating"


def test_case_detail_aggregates_events_files_attempts_audit_validation_and_approvals():
    _reset_butler_tables()
    runtime, case = _make_case()
    draft = runtime.create_memory_draft(
        case["id"], target_path="project-memory/workbench.md", content="工作台聚合证据"
    )
    runtime.record_attempt(case["id"], action="读取事实表", result="passed", learned="确认只读来源")
    approval = runtime.request_approval(case["id"], risk_kind="data", summary="需要用户确认的关联审批")
    runtime.resolve_approval(approval["id"], approved=True, response="已确认")
    runtime.begin_implementation(case["id"])
    runtime.record_change(case["id"], summary="新增聚合路由", files=["backend/workbench/cases.py"])
    runtime.record_audit(
        case["id"],
        verdict="passed",
        checklist={key: "passed" for key in ("null", "boundary", "error", "impact", "regression", "pattern")},
    )
    runtime.record_validation(case["id"], passed=True, evidence="列表与详情查询通过")
    conn = database.get_db()
    try:
        from butler.storage import create_evidence

        create_evidence(
            conn,
            {
                "task_id": case["id"],
                "evidence_type": "test_report",
                "summary": "工作台接口测试",
                "location": "tests/test_workbench_cases.py",
            },
        )
        conn.commit()
    finally:
        conn.close()

    response = _client().get(f"/workbench/cases/{case['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["id"] == case["id"]
    assert body["task"]["status"] == "verifying"
    assert {event["type"] for event in body["events"]} >= {
        "attempt_recorded",
        "approval_requested",
        "change_recorded",
        "audit_recorded",
        "validation_recorded",
    }
    assert body["files"] == ["backend/workbench/cases.py"]
    assert body["attempts"][0]["action"] == "读取事实表"
    assert body["changes"][0]["files"] == ["backend/workbench/cases.py"]
    assert body["audits"][0]["checklist"]["regression"] == "passed"
    assert body["validations"][0]["passed"] is True
    assert body["approvals"][0]["id"] == approval["id"]
    assert body["evidence"][0]["evidence_type"] == "test_report"
    assert body["memory_drafts"][0]["id"] == draft["id"]


def test_case_detail_returns_404_for_unknown_case():
    _reset_butler_tables()

    response = _client().get("/workbench/cases/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Butler case not found"
