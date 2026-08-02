"""Read-only projections for the Study-Hub workbench case views."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from butler.storage import (
    evidence_from_row,
    list_events,
    list_tasks,
    task_from_row,
)

STATUS_LABELS = {
    "received": "已接收",
    "located": "已定位",
    "investigating": "调查中",
    "awaiting_approval": "待审批",
    "implementing": "执行中",
    "auditing": "待审查",
    "verifying": "验证中",
    "completed": "已完成",
    "blocked": "已阻塞",
    "cancelled": "已取消",
    "archived": "已归档",
}
TASK_TYPE_LABELS = {
    "bug": "故障排查",
    "change": "变更",
    "research": "调研",
    "health_check": "健康检查",
    "deploy": "部署",
    "memory_update": "记忆更新",
}
RISK_LEVEL_LABELS = {"normal": "普通", "protected": "受保护"}
CASE_SORT_FIELDS = {"updated_at", "created_at", "status", "attempt_count", "title"}


def _iso_timestamp(value):
    if value in (None, ""):
        return value
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except (TypeError, ValueError):
        return value


def _labels(value: str, labels: dict[str, str]) -> str:
    return labels.get(value, f"未知{value}")


def _csv_values(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def _case_summary(task: dict) -> dict:
    return {
        "id": task["id"],
        "task_type": task["task_type"],
        "task_type_label": _labels(task["task_type"], TASK_TYPE_LABELS),
        "title": task["title"],
        "feature_code": task.get("feature_code", "") or "",
        "status": task["status"],
        "status_label": _labels(task["status"], STATUS_LABELS),
        "risk_level": task["risk_level"],
        "risk_level_label": _labels(task["risk_level"], RISK_LEVEL_LABELS),
        "attempt_count": task["attempt_count"],
        "current_role": task.get("current_role", "") or "",
        "experts": list(task.get("experts", ())),
        "created_at": _iso_timestamp(task.get("created_at")),
        "updated_at": _iso_timestamp(task.get("updated_at")),
    }


def _json_task(task: dict) -> dict:
    """Keep the projection compatible with the runtime JSON shape."""
    result = dict(task)
    result["experts"] = list(result.get("experts", ()))
    return result


def _contains_keyword(task: dict, keyword: str) -> bool:
    needle = keyword.casefold()
    return any(
        needle in str(task.get(field) or "").casefold()
        for field in ("id", "title", "description", "feature_code", "task_type")
    )


def list_case_summaries(
    conn,
    *,
    status: str | None = None,
    task_type: str | None = None,
    risk_level: str | None = None,
    feature_code: str | None = None,
    keyword: str | None = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    include_archived: bool = False,
) -> list[dict]:
    """Return Butler task rows with optional read-only filters and ordering."""
    if sort_by not in CASE_SORT_FIELDS:
        raise ValueError(f"sort_by must be one of {', '.join(sorted(CASE_SORT_FIELDS))}")
    if sort_order not in {"asc", "desc"}:
        raise ValueError("sort_order must be asc or desc")

    tasks = list_tasks(conn, include_archived=include_archived)
    statuses = _csv_values(status)
    task_types = _csv_values(task_type)
    if statuses:
        tasks = [task for task in tasks if task["status"] in statuses]
    if task_types:
        tasks = [task for task in tasks if task["task_type"] in task_types]
    if risk_level:
        tasks = [task for task in tasks if task["risk_level"] == risk_level]
    if feature_code:
        tasks = [task for task in tasks if task.get("feature_code", "") == feature_code]
    if keyword and keyword.strip():
        tasks = [task for task in tasks if _contains_keyword(task, keyword.strip())]

    tasks.sort(
        key=lambda task: (task.get(sort_by) or "", task.get("id") or ""),
        reverse=sort_order == "desc",
    )
    return [_case_summary(task) for task in tasks]


def _event_projection(event: dict, fields: Iterable[str]) -> dict:
    payload = event.get("payload") or {}
    projection = {
        "id": event["id"],
        "case_id": event["task_id"],
        "actor": event["actor"],
        "created_at": _iso_timestamp(event["created_at"]),
        "summary": event["summary"],
        "payload": payload,
    }
    for field in fields:
        if field in payload:
            projection[field] = payload[field]
    return projection


def _unique_files(changes: list[dict], task: dict) -> list[str]:
    files: list[str] = []
    for change in changes:
        for path in change.get("files") or ():
            if path not in files:
                files.append(path)
    if not files:
        for path in (task.get("context") or {}).get("change", {}).get("files", ()):
            if path not in files:
                files.append(path)
    return files


def _all_approvals(conn, case_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM butler_approvals WHERE task_id = ? ORDER BY created_at, id",
        (case_id,),
    ).fetchall()
    approvals = []
    for row in rows:
        approval = dict(row)
        approval["case_id"] = approval.pop("task_id")
        approval["created_at"] = _iso_timestamp(approval.get("created_at"))
        approval["decided_at"] = _iso_timestamp(approval.get("decided_at"))
        approval["status_label"] = {"pending": "待决定", "approved": "已批准", "rejected": "已拒绝"}.get(
            approval["status"], f"未知{approval['status']}"
        )
        approvals.append(approval)
    return approvals


def _all_memory_drafts(conn, case_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM butler_memory_drafts WHERE task_id = ? ORDER BY created_at, id",
        (case_id,),
    ).fetchall()
    drafts = []
    for row in rows:
        draft = dict(row)
        draft["case_id"] = draft.pop("task_id")
        draft["created_at"] = _iso_timestamp(draft.get("created_at"))
        draft["decided_at"] = _iso_timestamp(draft.get("decided_at"))
        drafts.append(draft)
    return drafts


def _task_and_events(conn, case_id: str) -> tuple[dict | None, list[dict]]:
    task = task_from_row(
        conn.execute("SELECT * FROM butler_tasks WHERE id = ?", (case_id,)).fetchone()
    )
    if task is None:
        return None, []
    return task, list_events(conn, case_id)


def get_case_detail(conn, case_id: str) -> dict | None:
    """Aggregate one case without changing Butler state or copying its status."""
    task, events = _task_and_events(conn, case_id)
    if task is None:
        return None

    changes = [
        _event_projection(event, ("summary", "files"))
        for event in events
        if event["type"] == "change_recorded"
    ]
    attempts = [
        _event_projection(event, ("action", "result", "learned", "attempt_count"))
        for event in events
        if event["type"] == "attempt_recorded"
    ]
    audits = [
        _event_projection(event, ("verdict", "checklist"))
        for event in events
        if event["type"] == "audit_recorded"
    ]
    validations = [
        _event_projection(event, ("passed", "evidence"))
        for event in events
        if event["type"] == "validation_recorded"
    ]
    evidence = [
        evidence_from_row(row)
        for row in conn.execute(
            "SELECT * FROM butler_evidence WHERE task_id = ? ORDER BY created_at, id",
            (case_id,),
        ).fetchall()
    ]
    for item in evidence:
        item["case_id"] = item.pop("task_id")
        item["created_at"] = _iso_timestamp(item.get("created_at"))
    approvals = _all_approvals(conn, case_id)
    memory_drafts = _all_memory_drafts(conn, case_id)

    from butler.runtime import ButlerRuntime
    from database import get_db

    next_action = ButlerRuntime(get_db).next_action(case_id)

    return {
        **_case_summary(task),
        "description": task["description"],
        "context": task["context"],
        "next_action": next_action,
        "events": events,
        "files": _unique_files(changes, task),
        "attempts": attempts,
        "changes": changes,
        "audits": audits,
        "validations": validations,
        "evidence": evidence,
        "approvals": approvals,
        "memory_drafts": memory_drafts,
    }
