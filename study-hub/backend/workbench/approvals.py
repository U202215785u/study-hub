"""Approval facts and transitions used by the workbench API."""

from __future__ import annotations

from database import get_db

from butler.models import ButlerStateError
from butler.runtime import ButlerRuntime
from butler.storage import initialize_butler_schema, list_events, read_task


class ApprovalNotFoundError(LookupError):
    """Raised when an approval id is not present in the Butler fact store."""


class ApprovalConflictError(RuntimeError):
    """Raised when an approval cannot be resolved in its current state."""


def _connection():
    conn = get_db()
    initialize_butler_schema(conn)
    return conn


def _approval_item(conn, approval: dict) -> dict:
    item = dict(approval)
    case = read_task(conn, approval["task_id"])
    item["case"] = case
    item["timeline"] = list_events(conn, approval["task_id"])
    return item


def list_approvals(*, status: str | None = None) -> list[dict]:
    """Read approval rows and their related Butler timeline without mutating them."""
    if status is not None and status not in {"pending", "approved", "rejected"}:
        raise ValueError("status must be pending, approved, or rejected")

    conn = _connection()
    try:
        query = "SELECT * FROM butler_approvals"
        values: list[str] = []
        if status is not None:
            query += " WHERE status = ?"
            values.append(status)
        query += " ORDER BY created_at DESC, id DESC"
        rows = conn.execute(query, values).fetchall()
        return [_approval_item(conn, dict(row)) for row in rows]
    finally:
        conn.close()


def get_approval(approval_id: str) -> dict:
    """Read one approval, its case and the complete Butler timeline."""
    conn = _connection()
    try:
        row = conn.execute(
            "SELECT * FROM butler_approvals WHERE id = ?", (approval_id,)
        ).fetchone()
        if row is None:
            raise ApprovalNotFoundError(f"unknown approval: {approval_id}")
        return _approval_item(conn, dict(row))
    finally:
        conn.close()


def resolve_approval(approval_id: str, *, approved: bool, response: str = "") -> dict:
    """Resolve through ButlerRuntime so status, case gates, and timeline stay atomic."""
    try:
        return ButlerRuntime(_connection).resolve_approval(
            approval_id, approved=approved, response=response
        )
    except ButlerStateError as exc:
        message = str(exc)
        if message.startswith("unknown approval:"):
            raise ApprovalNotFoundError(message) from exc
        raise ApprovalConflictError(message) from exc
