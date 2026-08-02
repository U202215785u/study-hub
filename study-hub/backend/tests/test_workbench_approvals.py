from fastapi import FastAPI
from fastapi.testclient import TestClient

import database


def _client():
    from endpoints.workbench_approvals import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _pending_approval():
    from butler.runtime import ButlerRuntime

    runtime = ButlerRuntime(database.get_db)
    case = runtime.open_case(task_type="change", description="approval workbench test")
    runtime.record_context(case["id"], project_index_hits=["SH.WORKBENCH"], owner_files=[])
    runtime.assign(case["id"], role="implementer")
    approval = runtime.request_approval(
        case["id"], risk_kind="release", summary="run the approved workbench action"
    )
    return runtime, case, approval


def test_approval_list_and_detail_read_butler_facts_and_timeline():
    runtime, case, approval = _pending_approval()
    client = _client()

    listed = client.get("/workbench/approvals")
    detail = client.get(f"/workbench/approvals/{approval['id']}")

    assert listed.status_code == 200
    item = next(item for item in listed.json()["items"] if item["id"] == approval["id"])
    assert item["status"] == "pending"
    assert item["task_id"] == case["id"]
    assert listed.json()["total"] >= 1

    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == approval["id"]
    assert body["case"]["id"] == case["id"]
    assert [event["type"] for event in body["timeline"]] == [
        "received",
        "context_recorded",
        "handoff",
        "approval_requested",
    ]


def test_resolve_pending_approval_uses_runtime_and_keeps_response_and_timeline():
    runtime, _, approval = _pending_approval()
    client = _client()

    response = client.post(
        f"/workbench/approvals/{approval['id']}/resolve",
        json={"approved": True, "response": "approved by reviewer"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["response"] == "approved by reviewer"

    detail = client.get(f"/workbench/approvals/{approval['id']}").json()
    assert detail["response"] == "approved by reviewer"
    assert detail["timeline"][-1]["type"] == "approval_resolved"
    assert detail["timeline"][-1]["payload"]["response"] == "approved by reviewer"
    assert runtime.get_case(approval["task_id"])["status"] == "awaiting_approval"


def test_resolving_processed_approval_returns_conflict_without_second_change():
    runtime, _, approval = _pending_approval()
    client = _client()
    first = client.post(
        f"/workbench/approvals/{approval['id']}/resolve",
        json={"approved": True, "response": "first decision"},
    )
    before = client.get(f"/workbench/approvals/{approval['id']}").json()

    second = client.post(
        f"/workbench/approvals/{approval['id']}/resolve",
        json={"approved": False, "response": "second decision must not apply"},
    )
    after = client.get(f"/workbench/approvals/{approval['id']}").json()

    assert first.status_code == 200
    assert second.status_code == 409
    assert after["status"] == before["status"] == "approved"
    assert after["response"] == before["response"] == "first decision"
    assert after["decided_at"] == before["decided_at"]
    assert after["timeline"] == before["timeline"]
    assert runtime.get_case(approval["task_id"])["status"] == "awaiting_approval"


def test_resolving_missing_approval_returns_not_found():
    client = _client()

    response = client.post(
        "/workbench/approvals/missing-approval/resolve",
        json={"approved": True, "response": "does not exist"},
    )

    assert response.status_code == 404

