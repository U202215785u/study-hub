"""Server-side read model for the Study-Hub workbench overview."""

from __future__ import annotations

from typing import Any, Callable

from butler.models import TERMINAL_STATUSES
from database import get_db
from workbench.approvals import list_approvals
from workbench.cases import STATUS_LABELS, list_case_summaries
from workbench.environment import get_environment_info, get_roadmap
from workbench.versions import VersionService


def _safe_read(reader: Callable[[], Any], fallback: Any) -> Any:
    try:
        value = reader()
    except Exception:
        return fallback
    return fallback if value is None else value


def _read_cases() -> list[dict[str, Any]]:
    conn = get_db()
    try:
        return list_case_summaries(
            conn,
            include_archived=True,
            sort_by="updated_at",
            sort_order="desc",
        )
    finally:
        conn.close()


def _read_current_version(version_type: str) -> dict[str, Any] | None:
    conn = get_db()
    try:
        versions = VersionService(conn).list_versions(
            version_type=version_type,
            current_only=True,
            limit=200,
        )
    finally:
        conn.close()
    return versions[0] if versions else None


def _roadmap_summary(roadmap: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": roadmap.get("status", "missing"),
        "missing": bool(roadmap.get("missing", False)),
        "source": roadmap.get("source"),
        "updated_at": roadmap.get("updated_at"),
        "content": roadmap.get("content"),
    }


def build_overview() -> dict[str, Any]:
    """Build one stable snapshot from the existing workbench read services."""
    cases = _safe_read(_read_cases, [])
    case_counts = {status: 0 for status in STATUS_LABELS}
    for case in cases:
        status = case.get("status", "")
        case_counts[status] = case_counts.get(status, 0) + 1

    pending_cases = [
        case
        for case in cases
        if case.get("status") not in TERMINAL_STATUSES
        and case.get("status") != "verifying"
    ]
    verification_cases = [case for case in cases if case.get("status") == "verifying"]

    pending_approvals = _safe_read(lambda: list_approvals(status="pending"), [])
    environment = _safe_read(
        get_environment_info,
        {
            "status": "unknown",
            "runtime": {},
            "health": {"status": "unknown", "checks": {}},
            "paths": {},
        },
    )
    roadmap = _safe_read(
        get_roadmap,
        {
            "status": "missing",
            "missing": True,
            "content": None,
            "source": None,
            "relative_path": None,
            "mtime": None,
            "updated_at": None,
            "error": None,
        },
    )
    current_version = _safe_read(lambda: _read_current_version("formal"), None)
    latest_test_version = _safe_read(lambda: _read_current_version("test"), None)
    active_versions = [
        version
        for version in (current_version, latest_test_version)
        if version is not None
    ]

    return {
        "case_counts": case_counts,
        "pending_cases": pending_cases,
        "verification_cases": verification_cases,
        "pending_approvals": len(pending_approvals),
        "recent_cases": cases[:5],
        "current_version": current_version,
        "latest_test_version": latest_test_version,
        "active_versions": active_versions,
        "environment": environment,
        "health": environment.get("health", {"status": "unknown", "checks": {}}),
        "environments": [],
        "roadmap": roadmap,
        "roadmap_summary": _roadmap_summary(roadmap),
    }
