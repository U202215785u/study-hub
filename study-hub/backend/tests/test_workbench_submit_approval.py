from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import database
from butler.runtime import ButlerRuntime
from workbench.versions import VersionService


@pytest.fixture(autouse=True)
def clean_submit_approval_facts():
    yield
    conn = database.get_db()
    try:
        version_ids = [
            row[0]
            for row in conn.execute(
                "SELECT id FROM workbench_versions WHERE workbench_id LIKE 'submit-approval-%'"
            ).fetchall()
        ]
        if version_ids:
            placeholders = ", ".join("?" for _ in version_ids)
            case_ids = [
                row[0]
                for row in conn.execute(
                    "SELECT case_id FROM workbench_release_approval_requests "
                    f"WHERE test_version_id IN ({placeholders}) AND case_id IS NOT NULL",
                    version_ids,
                ).fetchall()
            ]
            conn.execute(
                "DELETE FROM workbench_release_approval_requests "
                f"WHERE test_version_id IN ({placeholders})",
                version_ids,
            )
            if case_ids:
                case_placeholders = ", ".join("?" for _ in case_ids)
                conn.execute(
                    "DELETE FROM butler_events "
                    f"WHERE task_id IN ({case_placeholders})",
                    case_ids,
                )
                conn.execute(
                    "DELETE FROM butler_approvals "
                    f"WHERE task_id IN ({case_placeholders})",
                    case_ids,
                )
                conn.execute(
                    "DELETE FROM butler_tasks "
                    f"WHERE id IN ({case_placeholders})",
                    case_ids,
                )
            conn.execute(
                "DELETE FROM workbench_version_tickets "
                f"WHERE version_id IN ({placeholders})",
                version_ids,
            )
            conn.execute(
                "DELETE FROM workbench_versions "
                f"WHERE id IN ({placeholders})",
                version_ids,
            )
        conn.commit()
    finally:
        conn.close()


def _client() -> TestClient:
    from endpoints.workbench_test_versions import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _test_version(*, status: str = "passed") -> dict:
    version = VersionService(database.get_db()).record_test_version(
        workbench_id=f"submit-approval-{uuid4().hex}",
        version="1.0.0-rc.1",
        title="Release candidate",
    )
    conn = database.get_db()
    try:
        conn.execute(
            "UPDATE workbench_versions SET status = ? WHERE id = ?",
            (status, version["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return version


def _approval_count(test_version_id: int) -> int:
    conn = database.get_db()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM workbench_release_approval_requests "
            "WHERE test_version_id = ? AND approval_id IS NOT NULL",
            (test_version_id,),
        ).fetchone()[0]
    finally:
        conn.close()


def test_missing_test_version_returns_explicit_not_found_error():
    response = _client().post("/workbench/test-versions/999999/submit-approval")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WB_NOT_FOUND"


def test_only_passed_test_versions_can_request_release_approval():
    version = _test_version(status="failed")

    response = _client().post(
        f"/workbench/test-versions/{version['id']}/submit-approval",
        headers={"Idempotency-Key": "failed-test-version"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "WB_TEST_NOT_PASSED"
    assert _approval_count(version["id"]) == 0


def test_passed_test_version_creates_pending_release_approval_only():
    version = _test_version()

    response = _client().post(
        f"/workbench/test-versions/{version['id']}/submit-approval",
        headers={"Idempotency-Key": "passed-test-version"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["test_version_id"] == version["id"]
    assert body["data"]["approval"]["risk_kind"] == "release"
    assert body["data"]["approval"]["status"] == "pending"
    assert body["data"]["case"]["status"] == "awaiting_approval"
    assert _approval_count(version["id"]) == 1

    stored = VersionService(database.get_db()).get_version(version["id"])
    assert stored["status"] == "passed"


def test_repeated_request_reuses_idempotency_result_and_does_not_duplicate():
    version = _test_version()
    client = _client()
    headers = {"Idempotency-Key": "same-request"}

    first = client.post(
        f"/workbench/test-versions/{version['id']}/submit-approval",
        headers=headers,
    )
    second = client.post(
        f"/workbench/test-versions/{version['id']}/submit-approval",
        headers=headers,
    )

    assert first.status_code == second.status_code == 201
    assert second.json()["data"] == first.json()["data"]
    assert _approval_count(version["id"]) == 1


def test_pending_or_approved_release_approval_blocks_a_new_request():
    version = _test_version()
    client = _client()
    path = f"/workbench/test-versions/{version['id']}/submit-approval"

    first = client.post(path, headers={"Idempotency-Key": "first-key"})
    second = client.post(path, headers={"Idempotency-Key": "second-key"})

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "WB_APPROVAL_PENDING"
    approval_id = first.json()["data"]["approval"]["id"]
    ButlerRuntime(database.get_db).resolve_approval(
        approval_id, approved=True, response="approved for release review"
    )

    third = client.post(path, headers={"Idempotency-Key": "third-key"})
    assert third.status_code == 409
    assert third.json()["error"]["code"] == "WB_APPROVAL_PENDING"
    assert _approval_count(version["id"]) == 1


def test_concurrent_requests_create_one_butler_approval_and_share_result():
    version = _test_version()
    path = f"/workbench/test-versions/{version['id']}/submit-approval"

    def submit():
        return _client().post(path, headers={"Idempotency-Key": "concurrent-key"})

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: submit(), range(2)))

    assert [response.status_code for response in responses] == [201, 201]
    assert responses[0].json()["data"] == responses[1].json()["data"]
    assert _approval_count(version["id"]) == 1
