from datetime import datetime, timezone
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from endpoints.workbench_environment import router
from workbench.environment import get_environment_info, get_roadmap


def test_environment_returns_only_controlled_fields_and_surfaces_health_failure(tmp_path):
    secret = "super-secret-value"

    data = get_environment_info(
        project_root=tmp_path,
        health_checker=lambda: {
            "status": "degraded",
            "checks": {"database": {"status": "error", "message": "unavailable"}},
        },
    )

    assert data["status"] == "degraded"
    assert data["health"]["status"] == "degraded"
    assert data["health"]["checks"]["database"]["status"] == "error"
    assert data["paths"]["project_root"] == "."
    assert str(tmp_path) not in str(data)
    assert secret not in str(data)
    assert set(data) == {"status", "runtime", "health", "paths"}
    assert set(data["runtime"]) == {"python_version", "platform", "implementation"}


def test_environment_redacts_arbitrary_health_check_details(tmp_path):
    data = get_environment_info(
        project_root=tmp_path,
        health_checker=lambda: {
            "status": "error",
            "checks": {
                "database": {
                    "status": "error",
                    "message": "C:/Users/Alice/.env SUPER_SECRET",
                    "password": "do-not-return",
                }
            },
            "detail": "private diagnostic",
        },
    )

    assert data["health"] == {
        "status": "error",
        "checks": {"database": {"status": "error"}},
    }


def test_roadmap_prefers_project_memory_and_returns_relative_path_and_mtime(tmp_path):
    project_memory = tmp_path / "project-memory"
    docs = tmp_path / "docs"
    project_memory.mkdir()
    docs.mkdir()
    preferred = project_memory / "未来规划.md"
    preferred.write_text("# Preferred roadmap\n", encoding="utf-8")
    (docs / "roadmap.md").write_text("# Lower priority\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("## Roadmap\nREADME\n", encoding="utf-8")
    expected_mtime = 1_700_000_000
    import os

    os.utime(preferred, (expected_mtime, expected_mtime))

    data = get_roadmap(tmp_path)

    assert data["status"] == "available"
    assert data["missing"] is False
    assert data["source"] == "project-memory/未来规划.md"
    assert data["relative_path"] == "project-memory/未来规划.md"
    assert data["content"] == "# Preferred roadmap\n"
    assert data["mtime"] == pytest.approx(expected_mtime)
    assert data["updated_at"] == datetime.fromtimestamp(
        expected_mtime, timezone.utc
    ).isoformat()
    assert str(tmp_path) not in str(data)


def test_roadmap_falls_back_to_docs_then_readme_planning_section(tmp_path):
    (tmp_path / "docs").mkdir()
    docs_roadmap = tmp_path / "docs" / "roadmap.md"
    docs_roadmap.write_text("# Docs roadmap\n", encoding="utf-8")

    docs_data = get_roadmap(tmp_path)
    assert docs_data["source"] == "docs/roadmap.md"
    assert docs_data["content"] == "# Docs roadmap\n"

    docs_roadmap.unlink()
    (tmp_path / "README.md").write_text(
        "# Project\n\n## Planning\n\n- P0 item\n\n## Usage\n\nRun it.\n",
        encoding="utf-8",
    )

    readme_data = get_roadmap(tmp_path)
    assert readme_data["source"] == "README.md#Planning"
    assert readme_data["relative_path"] == "README.md"
    assert readme_data["content"] == "## Planning\n\n- P0 item\n"


def test_roadmap_reports_missing_without_leaking_paths(tmp_path):
    data = get_roadmap(tmp_path)

    assert data == {
        "status": "missing",
        "missing": True,
        "content": None,
        "source": None,
        "relative_path": None,
        "mtime": None,
        "updated_at": None,
        "error": None,
    }
    assert str(tmp_path) not in str(data)


@pytest.mark.asyncio
async def test_router_exports_both_read_only_workbench_endpoints(monkeypatch, tmp_path):
    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(
        "endpoints.workbench_environment.get_environment_info",
        lambda: get_environment_info(tmp_path),
    )
    monkeypatch.setattr(
        "endpoints.workbench_environment.get_roadmap",
        lambda: get_roadmap(tmp_path),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        environment_response = await client.get("/workbench/environment")
        roadmap_response = await client.get("/workbench/roadmap")

    assert environment_response.status_code == 200
    assert roadmap_response.status_code == 200
    assert environment_response.json()["status"] in {"ok", "degraded", "error"}
    assert roadmap_response.json()["missing"] is True
