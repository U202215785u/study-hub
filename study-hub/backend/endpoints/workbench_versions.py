"""Read-only workbench version history endpoints."""

import importlib.util
import os

from fastapi import APIRouter, HTTPException, Query

from database import get_db


def _load_version_service():
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "workbench", "versions.py"
    )
    spec = importlib.util.spec_from_file_location(
        "study_hub_workbench_versions_for_endpoint", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VersionService


VersionService = _load_version_service()
router = APIRouter(prefix="/workbench/versions", tags=["workbench-versions"])


@router.get("")
def list_workbench_versions(
    workbench_id: str | None = None,
    version_type: str | None = Query(default=None, pattern="^(formal|test)$"),
    current_only: bool = False,
    ticket_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    conn = get_db()
    try:
        service = VersionService(conn)
        versions = service.list_versions(
            workbench_id=workbench_id,
            version_type=version_type,
            current_only=current_only,
            ticket_id=ticket_id,
            limit=limit,
            offset=offset,
        )
        return {
            "versions": versions,
            "total": len(versions),
            "limit": limit,
            "offset": offset,
        }
    finally:
        conn.close()


@router.get("/{version_id}")
def get_workbench_version(version_id: int):
    conn = get_db()
    try:
        version = VersionService(conn).get_version(version_id)
        if version is None:
            raise HTTPException(status_code=404, detail="Workbench version not found")
        return version
    finally:
        conn.close()
