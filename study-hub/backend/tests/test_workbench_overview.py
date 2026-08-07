from fastapi.testclient import TestClient

import database
from butler.runtime import ButlerRuntime
from workbench.versions import VersionService


def _client():
    from main import app

    return TestClient(app)


def _reset_workbench_data():
    conn = database.get_db()
    try:
        for table in (
            "workbench_version_tickets",
            "workbench_versions",
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


def _case(runtime, *, title):
    case = runtime.open_case(task_type="change", title=title, description=title)
    runtime.record_context(
        case["id"],
        project_index_hits=["SH.WORKBENCH"],
        owner_files=["backend/workbench"],
    )
    runtime.assign(case["id"], role="implementer")
    return case


def test_overview_aggregates_cases_approvals_versions_health_and_roadmap():
    _reset_workbench_data()
    runtime = ButlerRuntime(database.get_db)
    pending = _case(runtime, title="Pending workbench case")
    verifying = _case(runtime, title="Verifying workbench case")
    runtime.begin_implementation(verifying["id"])
    runtime.record_change(verifying["id"], summary="ready for audit", files=["backend/workbench/overview.py"])
    runtime.record_audit(
        verifying["id"],
        verdict="passed",
        checklist={key: "passed" for key in ("null", "boundary", "error", "impact", "regression", "pattern")},
    )
    approval_case = _case(runtime, title="Approval workbench case")
    approval = runtime.request_approval(
        approval_case["id"], risk_kind="release", summary="Approve workbench release"
    )

    conn = database.get_db()
    try:
        service = VersionService(conn)
        service.record_formal_version(workbench_id="study-hub", version="1.0.0", title="Current")
        service.record_test_version(workbench_id="study-hub", version="1.1.0-rc.1", title="Latest test")
    finally:
        conn.close()

    response = _client().get("/workbench/overview", headers={"X-Request-ID": "overview-test"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["meta"]["schema_version"] == "workbench.v1"
    assert body["meta"]["request_id"] == "overview-test"
    data = body["data"]
    assert data["pending_approvals"] == 1
    assert approval_case["id"] in {item["id"] for item in data["pending_cases"]}
    assert [item["id"] for item in data["verification_cases"]] == [verifying["id"]]
    assert data["case_counts"]["investigating"] == 1
    assert data["case_counts"]["awaiting_approval"] == 1
    assert data["case_counts"]["verifying"] == 1
    assert data["current_version"]["version"] == "1.0.0"
    assert data["latest_test_version"]["version"] == "1.1.0-rc.1"
    assert data["health"]["status"] in {"ok", "degraded", "error"}
    assert set(data["roadmap"]) >= {"status", "missing"}
    assert len(data["recent_cases"]) <= 5


def test_overview_is_stable_for_empty_data_and_api_prefix():
    _reset_workbench_data()

    response = _client().get("/api/workbench/overview")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["pending_cases"] == []
    assert data["verification_cases"] == []
    assert data["pending_approvals"] == 0
    assert data["current_version"] is None
    assert data["latest_test_version"] is None
    assert data["recent_cases"] == []
    assert data["active_versions"] == []
    assert data["environments"] == []
    assert set(data["roadmap"]) >= {"status", "missing"}


def test_main_mounts_workbench_child_routes_once():
    _reset_workbench_data()
    client = _client()

    cases = client.get("/workbench/cases")
    approvals = client.get("/workbench/approvals")
    versions = client.get("/workbench/versions")
    test_version_submit = client.post(
        "/workbench/test-versions/999999/submit-approval"
    )
    environment = client.get("/workbench/environment")
    roadmap = client.get("/workbench/roadmap")

    assert cases.status_code == 200
    assert approvals.status_code == 200
    assert versions.status_code == 200
    assert test_version_submit.status_code == 404
    assert test_version_submit.json()["error"]["code"] == "WB_NOT_FOUND"
    assert environment.status_code == 200
    assert roadmap.status_code == 200

    from main import app

    overview_routes = [route for route in app.routes if route.path == "/workbench/overview"]
    case_routes = [route for route in app.routes if route.path == "/workbench/cases"]
    test_version_submit_routes = [
        route
        for route in app.routes
        if route.path == "/workbench/test-versions/{test_version_id}/submit-approval"
    ]
    assert len(overview_routes) == 1
    assert len(case_routes) == 1
    assert len(test_version_submit_routes) == 1
