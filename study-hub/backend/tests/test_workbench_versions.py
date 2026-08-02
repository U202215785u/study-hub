import importlib.util
from pathlib import Path

import database
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest


def _load_versions_module():
    path = Path(database.__file__).with_name("workbench") / "versions.py"
    spec = importlib.util.spec_from_file_location("workbench_versions_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_endpoint_module():
    path = Path(database.__file__).parent / "endpoints" / "workbench_versions.py"
    spec = importlib.util.spec_from_file_location("workbench_versions_endpoint_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_workbench_version_migration_is_idempotent_and_creates_relational_schema():
    database.init_db()
    database.init_db()

    conn = database.get_db()
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "workbench_versions" in tables
        assert "workbench_version_tickets" in tables

        version_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(workbench_versions)")
        }
        assert {
            "id",
            "workbench_id",
            "version_type",
            "version",
            "title",
            "description",
            "metadata_json",
            "created_at",
        } <= version_columns

        ticket_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(workbench_version_tickets)")
        }
        assert {"version_id", "ticket_id", "ticket_title", "ticket_status"} <= ticket_columns

        conn.execute(
            "INSERT INTO workbench_versions "
            "(workbench_id, version_type, version, title) VALUES (?, ?, ?, ?)",
            ("parser", "formal", "1.0.0", "First"),
        )
        conn.commit()
        assert conn.execute("SELECT COUNT(*) FROM workbench_versions").fetchone()[0] == 1
    finally:
        conn.close()


def test_version_service_separates_formal_and_test_histories_and_resolves_current_records():
    versions = _load_versions_module()
    service = versions.VersionService(database.get_db())

    formal_one = service.record_formal_version(
        workbench_id="version-service-test",
        version="1.0.0",
        title="Initial release",
        description="First formal version",
        commit_sha="abc123",
        metadata={"channel": "stable"},
        tickets=[{"ticket_id": "WB-101", "title": "Initial case", "status": "done"}],
    )
    test_one = service.record_test_version(
        workbench_id="version-service-test",
        version="1.1.0-rc.1",
        title="Candidate",
        base_formal_version_id=formal_one["id"],
        tickets=[{"ticket_id": "WB-102", "title": "Candidate case", "status": "testing"}],
    )
    formal_two = service.record_formal_version(
        workbench_id="version-service-test",
        version="1.1.0",
        title="Second release",
        tickets=["WB-103"],
    )

    formal_history = service.list_versions(
        workbench_id="version-service-test", version_type="formal"
    )
    test_history = service.list_versions(
        workbench_id="version-service-test", version_type="test"
    )
    assert [item["id"] for item in formal_history] == [formal_two["id"], formal_one["id"]]
    assert [item["id"] for item in test_history] == [test_one["id"]]
    assert formal_history[0]["is_current"] is True
    assert formal_history[1]["is_current"] is False
    assert test_history[0]["is_current"] is True
    assert formal_history[0]["ticket_ids"] == ["WB-103"]

    detail = service.get_version(formal_one["id"])
    assert detail["version_type"] == "formal"
    assert detail["metadata"] == {"channel": "stable"}
    assert detail["ticket_ids"] == ["WB-101"]
    assert detail["tickets"] == [
        {"ticket_id": "WB-101", "title": "Initial case", "status": "done"}
    ]
    assert service.list_versions(ticket_id="WB-101")[0]["id"] == formal_one["id"]
    assert service.list_versions(current_only=True, workbench_id="version-service-test")[0]["id"] == formal_two["id"]
    assert not hasattr(service, "rollback")
    assert not hasattr(service, "publish")


@pytest.mark.asyncio
async def test_version_router_exposes_only_list_and_detail_get_endpoints():
    versions = _load_versions_module()
    endpoint = _load_endpoint_module()
    service = versions.VersionService(database.get_db())
    record = service.record_formal_version(
        workbench_id="router-test",
        version="2.0.0",
        title="Router release",
    )

    app = FastAPI()
    app.include_router(endpoint.router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listing = await client.get(
            "/workbench/versions",
            params={"workbench_id": "router-test", "version_type": "formal"},
        )
        detail = await client.get(f"/workbench/versions/{record['id']}")
        missing = await client.get("/workbench/versions/999999")

    assert listing.status_code == 200
    assert listing.json()["versions"][0]["version"] == "2.0.0"
    assert listing.json()["versions"][0]["is_current"] is True
    assert detail.status_code == 200
    assert detail.json()["id"] == record["id"]
    assert missing.status_code == 404
    methods = {method for route in endpoint.router.routes for method in route.methods}
    assert methods <= {"GET"}
