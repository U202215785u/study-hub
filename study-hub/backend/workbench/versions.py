"""Version history models and read/query services for the workbench."""

import importlib.util
import json
import os
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from database import get_db


VersionType = Literal["formal", "test"]


class VersionTicket(BaseModel):
    ticket_id: str
    title: str = ""
    status: str = ""


class VersionCreate(BaseModel):
    workbench_id: str
    version: str
    title: str = ""
    description: str = ""
    content_hash: str = ""
    commit_sha: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    tickets: list[VersionTicket | str | dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[str] = None


class FormalVersionCreate(VersionCreate):
    pass


class TestVersionCreate(VersionCreate):
    base_formal_version_id: Optional[int] = None


class VersionSummary(BaseModel):
    id: int
    workbench_id: str
    version_type: VersionType
    version: str
    title: str
    description: str
    content_hash: str
    commit_sha: str
    base_formal_version_id: Optional[int]
    status: str
    metadata: dict[str, Any]
    ticket_ids: list[str]
    tickets: list[VersionTicket]
    is_current: bool
    created_at: str


class FormalVersion(VersionSummary):
    version_type: Literal["formal"] = "formal"


class TestVersion(VersionSummary):
    version_type: Literal["test"] = "test"


def _ensure_schema(conn) -> None:
    migration_path = os.path.join(os.path.dirname(__file__), "migrations.py")
    spec = importlib.util.spec_from_file_location(
        "study_hub_workbench_migrations_for_versions", migration_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate(conn)


def _ticket_dict(ticket: VersionTicket | str | dict[str, Any]) -> dict[str, str]:
    if isinstance(ticket, str):
        return {"ticket_id": ticket, "title": "", "status": ""}
    if isinstance(ticket, VersionTicket):
        return ticket.model_dump()
    ticket_id = ticket.get("ticket_id", ticket.get("id", ""))
    if not ticket_id:
        raise ValueError("ticket_id is required")
    return {
        "ticket_id": str(ticket_id),
        "title": str(ticket.get("title", ticket.get("ticket_title", ""))),
        "status": str(ticket.get("status", ticket.get("ticket_status", ""))),
    }


class VersionService:
    """Persist immutable version records and expose read-only projections."""

    def __init__(self, conn=None):
        self._conn = conn or get_db()
        self._owns_connection = conn is None
        _ensure_schema(self._conn)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()

    def record_formal_version(self, **kwargs) -> dict[str, Any]:
        return self._record(version_type="formal", **kwargs)

    def record_test_version(self, **kwargs) -> dict[str, Any]:
        return self._record(version_type="test", **kwargs)

    create_formal_version = record_formal_version
    create_test_version = record_test_version

    def _record(self, version_type: VersionType, **kwargs) -> dict[str, Any]:
        payload = (FormalVersionCreate if version_type == "formal" else TestVersionCreate)(**kwargs)
        base_id = getattr(payload, "base_formal_version_id", None)
        if version_type == "formal":
            base_id = None

        columns = [
            "workbench_id", "version_type", "version", "title", "description",
            "content_hash", "commit_sha", "base_formal_version_id", "metadata_json",
        ]
        values = [
            payload.workbench_id, version_type, payload.version, payload.title,
            payload.description, payload.content_hash, payload.commit_sha, base_id,
            json.dumps(payload.metadata, ensure_ascii=False, sort_keys=True),
        ]
        if payload.created_at is not None:
            columns.append("created_at")
            values.append(payload.created_at)

        placeholders = ", ".join("?" for _ in values)
        try:
            cursor = self._conn.execute(
                f"INSERT INTO workbench_versions ({', '.join(columns)}) VALUES ({placeholders})",
                values,
            )
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise ValueError("version already exists for this workbench and type") from exc
            raise

        version_id = cursor.lastrowid
        for raw_ticket in payload.tickets:
            ticket = _ticket_dict(raw_ticket)
            self._conn.execute(
                "INSERT INTO workbench_version_tickets "
                "(version_id, ticket_id, ticket_title, ticket_status) VALUES (?, ?, ?, ?)",
                (version_id, ticket["ticket_id"], ticket["title"], ticket["status"]),
            )
        self._conn.commit()
        return self.get_version(version_id)

    def get_version(self, version_id: int) -> Optional[dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM workbench_versions WHERE id = ?", (version_id,)
        ).fetchone()
        if row is None:
            return None
        current_id = self._current_id(row["workbench_id"], row["version_type"])
        return self._serialize(row, current_id == row["id"])

    def list_versions(
        self,
        workbench_id: Optional[str] = None,
        version_type: Optional[VersionType] = None,
        current_only: bool = False,
        ticket_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if version_type not in (None, "formal", "test"):
            raise ValueError("version_type must be formal or test")
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        conditions = []
        params: list[Any] = []
        if workbench_id:
            conditions.append("v.workbench_id = ?")
            params.append(workbench_id)
        if version_type:
            conditions.append("v.version_type = ?")
            params.append(version_type)
        if ticket_id:
            conditions.append(
                "EXISTS (SELECT 1 FROM workbench_version_tickets vt "
                "WHERE vt.version_id = v.id AND vt.ticket_id = ?)"
            )
            params.append(ticket_id)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self._conn.execute(
            f"SELECT v.* FROM workbench_versions v {where} "
            "ORDER BY v.created_at DESC, v.id DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        current_ids = {
            (row["workbench_id"], row["version_type"]): self._current_id(
                row["workbench_id"], row["version_type"]
            )
            for row in rows
        }
        items = [
            self._serialize(
                row,
                row["id"] == current_ids[(row["workbench_id"], row["version_type"])],
            )
            for row in rows
        ]
        return [item for item in items if not current_only or item["is_current"]]

    def list_formal_versions(self, **kwargs) -> list[dict[str, Any]]:
        return self.list_versions(version_type="formal", **kwargs)

    def list_test_versions(self, **kwargs) -> list[dict[str, Any]]:
        return self.list_versions(version_type="test", **kwargs)

    def _current_id(self, workbench_id: str, version_type: str) -> Optional[int]:
        row = self._conn.execute(
            "SELECT id FROM workbench_versions "
            "WHERE workbench_id = ? AND version_type = ? "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            (workbench_id, version_type),
        ).fetchone()
        return row["id"] if row else None

    def _serialize(self, row, is_current: bool) -> dict[str, Any]:
        tickets = self._conn.execute(
            "SELECT ticket_id, ticket_title, ticket_status "
            "FROM workbench_version_tickets WHERE version_id = ? ORDER BY ticket_id",
            (row["id"],),
        ).fetchall()
        ticket_items = [
            {
                "ticket_id": ticket["ticket_id"],
                "title": ticket["ticket_title"],
                "status": ticket["ticket_status"],
            }
            for ticket in tickets
        ]
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        return {
            "id": row["id"],
            "workbench_id": row["workbench_id"],
            "version_type": row["version_type"],
            "version": row["version"],
            "title": row["title"],
            "description": row["description"],
            "content_hash": row["content_hash"],
            "commit_sha": row["commit_sha"],
            "base_formal_version_id": row["base_formal_version_id"],
            "status": row["status"],
            "metadata": metadata,
            "ticket_ids": [ticket["ticket_id"] for ticket in tickets],
            "tickets": ticket_items,
            "is_current": is_current,
            "created_at": row["created_at"],
        }
