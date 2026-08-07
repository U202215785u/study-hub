"""Submit a passed workbench test version for Butler release approval."""

from __future__ import annotations

import json
import sqlite3
from threading import RLock
from typing import Any

import database
from butler.models import ButlerStateError
from butler.runtime import ButlerRuntime
from butler.storage import initialize_butler_schema
from workbench.versions import VersionService


class ReleaseApprovalError(RuntimeError):
    status_code = 409
    code = "WB_STATE_CONFLICT"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


class TestVersionNotFoundError(ReleaseApprovalError):
    status_code = 404
    code = "WB_NOT_FOUND"


class TestVersionNotPassedError(ReleaseApprovalError):
    code = "WB_TEST_NOT_PASSED"


class ReleaseApprovalPendingError(ReleaseApprovalError):
    code = "WB_APPROVAL_PENDING"


class ReleaseApprovalService:
    """Coordinate version gating, idempotency, and Butler approval creation."""

    _submit_lock = RLock()

    @staticmethod
    def _ensure_schema(conn) -> None:
        VersionService(conn)
        initialize_butler_schema(conn)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workbench_release_approval_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_version_id INTEGER NOT NULL,
                idempotency_key TEXT,
                state TEXT NOT NULL DEFAULT 'creating'
                    CHECK(state IN ('creating', 'created')),
                approval_id TEXT,
                case_id TEXT,
                result_json TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_version_id) REFERENCES workbench_versions(id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS
                uq_workbench_release_approval_idempotency
                ON workbench_release_approval_requests(test_version_id, idempotency_key)
                WHERE idempotency_key IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_workbench_release_approval_version
                ON workbench_release_approval_requests(test_version_id, state);
            """
        )
        conn.commit()

    @staticmethod
    def _version(conn, test_version_id: int) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM workbench_versions WHERE id = ? AND version_type = 'test'",
            (test_version_id,),
        ).fetchone()
        if row is None:
            raise TestVersionNotFoundError(
                "Test version not found",
                details={
                    "resource_type": "test_version",
                    "resource_id": test_version_id,
                },
            )
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        return {
            "id": row["id"],
            "workbench_id": row["workbench_id"],
            "version": row["version"],
            "status": row["status"],
            "test_status": metadata.get("test_status", row["status"]),
            "target_environment": metadata.get(
                "target_environment", metadata.get("environment", "release")
            ),
        }

    @staticmethod
    def _stored_result(conn, test_version_id: int, idempotency_key: str) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT state, result_json FROM workbench_release_approval_requests "
            "WHERE test_version_id = ? AND idempotency_key = ?",
            (test_version_id, idempotency_key),
        ).fetchone()
        if row is None or row["state"] != "created" or not row["result_json"]:
            return None
        return json.loads(row["result_json"])

    @staticmethod
    def _active_approval(conn, test_version_id: int):
        return conn.execute(
            "SELECT r.approval_id, r.case_id, a.status "
            "FROM workbench_release_approval_requests r "
            "JOIN butler_approvals a ON a.id = r.approval_id "
            "WHERE r.test_version_id = ? AND a.risk_kind = 'release' "
            "AND a.status IN ('pending', 'approved') "
            "ORDER BY a.created_at, a.id LIMIT 1",
            (test_version_id,),
        ).fetchone()

    def _claim(self, test_version_id: int, idempotency_key: str | None):
        conn = database.get_db()
        try:
            self._ensure_schema(conn)
            conn.execute("BEGIN IMMEDIATE")
            version = self._version(conn, test_version_id)
            if version["test_status"] != "passed":
                raise TestVersionNotPassedError(
                    "Test version must have passed tests before requesting release approval",
                    details={"test_version_id": test_version_id, "test_status": version["test_status"]},
                )

            if idempotency_key is not None:
                stored = self._stored_result(conn, test_version_id, idempotency_key)
                if stored is not None:
                    conn.rollback()
                    return stored

            active = self._active_approval(conn, test_version_id)
            if active is not None:
                raise ReleaseApprovalPendingError(
                    "Test version already has a pending or approved release approval",
                    details={
                        "test_version_id": test_version_id,
                        "approval_id": active["approval_id"],
                        "approval_status": active["status"],
                    },
                )

            creating = conn.execute(
                "SELECT id FROM workbench_release_approval_requests "
                "WHERE test_version_id = ? AND state = 'creating' LIMIT 1",
                (test_version_id,),
            ).fetchone()
            if creating is not None:
                raise ReleaseApprovalPendingError(
                    "A release approval request is already being created",
                    details={"test_version_id": test_version_id},
                )

            try:
                cursor = conn.execute(
                    "INSERT INTO workbench_release_approval_requests "
                    "(test_version_id, idempotency_key, state) VALUES (?, ?, 'creating')",
                    (test_version_id, idempotency_key),
                )
            except sqlite3.IntegrityError:
                conn.rollback()
                if idempotency_key is not None:
                    stored = self._stored_result(conn, test_version_id, idempotency_key)
                    if stored is not None:
                        return stored
                raise ReleaseApprovalPendingError(
                    "A release approval request is already being created",
                    details={"test_version_id": test_version_id},
                )
            conn.commit()
            return {"claim_id": cursor.lastrowid, "version": version}
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _finalize(
        claim_id: int,
        *,
        test_version_id: int,
        approval_id: str,
        case_id: str,
        result: dict[str, Any],
    ) -> None:
        conn = database.get_db()
        try:
            self = ReleaseApprovalService
            self._ensure_schema(conn)
            conn.execute(
                "UPDATE workbench_release_approval_requests "
                "SET state = 'created', approval_id = ?, case_id = ?, result_json = ? "
                "WHERE id = ? AND test_version_id = ? AND state = 'creating'",
                (
                    approval_id,
                    case_id,
                    json.dumps(result, ensure_ascii=False, sort_keys=True),
                    claim_id,
                    test_version_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def submit(self, test_version_id: int, *, idempotency_key: str | None = None) -> dict[str, Any]:
        if test_version_id < 1:
            raise TestVersionNotFoundError(
                "Test version not found",
                details={"resource_type": "test_version", "resource_id": test_version_id},
            )
        if idempotency_key is not None:
            idempotency_key = idempotency_key.strip() or None
            if idempotency_key is not None and len(idempotency_key) > 255:
                raise ReleaseApprovalError(
                    "Idempotency-Key must be 255 characters or fewer",
                    details={"field": "Idempotency-Key"},
                )

        with self._submit_lock:
            claim = self._claim(test_version_id, idempotency_key)
            if "claim_id" not in claim:
                return claim

            version = claim["version"]
            summary = f"Request release approval for test version {version['version']}"
            operation = {
                "kind": "release",
                "target_version": version["version"],
                "target_environment": version["target_environment"],
                "release_requested": True,
            }
            runtime = ButlerRuntime(database.get_db)
            approval_created = False
            try:
                case = runtime.open_case(
                    task_type="deploy",
                    feature_code="SH.WORKBENCH",
                    title=summary,
                    description=(
                        f"Submit test version {version['id']} ({version['version']}) "
                        "for release approval; do not publish resources."
                    ),
                )
                runtime.record_context(
                    case["id"],
                    project_index_hits=["SH.WORKBENCH", "WB-05"],
                    owner_files=[
                        "backend/workbench/release_approval.py",
                        "backend/endpoints/workbench_test_versions.py",
                    ],
                    memory_summary=[
                        "Only passed test versions without pending or approved release approval may submit."
                    ],
                    location_notes=[f"test_version_id={version['id']}"],
                )
                runtime.assign(case["id"], role="implementer")
                approval = runtime.request_approval(
                    case["id"], risk_kind="release", summary=summary
                )
                approval_created = True
                case = runtime.get_case(case["id"])
                approval_view = {
                    **approval,
                    "case_id": approval["task_id"],
                    "test_version_id": test_version_id,
                    "operation": operation,
                }
                result = {
                    "test_version_id": test_version_id,
                    "approval": approval_view,
                    "case": case,
                    "operation": operation,
                }
                self._finalize(
                    claim["claim_id"],
                    test_version_id=test_version_id,
                    approval_id=approval["id"],
                    case_id=case["id"],
                    result=result,
                )
                return result
            except ButlerStateError as exc:
                if approval_created:
                    raise ReleaseApprovalError(
                        "Release approval was created but its workbench link could not be completed"
                    ) from exc
                self._delete_claim(claim["claim_id"])
                raise ReleaseApprovalError("Unable to create release approval") from exc
            except Exception:
                if not approval_created:
                    self._delete_claim(claim["claim_id"])
                raise

    @staticmethod
    def _delete_claim(claim_id: int) -> None:
        conn = database.get_db()
        try:
            conn.execute(
                "DELETE FROM workbench_release_approval_requests "
                "WHERE id = ? AND state = 'creating'",
                (claim_id,),
            )
            conn.commit()
        finally:
            conn.close()


__all__ = (
    "ReleaseApprovalError",
    "ReleaseApprovalPendingError",
    "ReleaseApprovalService",
    "TestVersionNotFoundError",
    "TestVersionNotPassedError",
)
