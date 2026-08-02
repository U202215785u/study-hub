"""Read-only workbench case endpoints for later app mounting."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from database import get_db
from workbench.cases import get_case_detail, list_case_summaries

router = APIRouter(tags=["workbench"])


def _meta(request: Request) -> dict:
    return {
        "schema_version": "workbench.v1",
        "request_id": request.headers.get("X-Request-ID") or uuid4().hex,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def _invalid_query(request: Request, message: str, field: str | None = None):
    return JSONResponse(
        status_code=400,
        content={
            "ok": False,
            "data": None,
            "error": {
                "code": "WB_INVALID_QUERY",
                "message": message,
                "details": {"field": field} if field else {},
                "retryable": False,
            },
            "meta": _meta(request),
        },
    )


@router.get("/workbench/cases")
def list_workbench_cases(
    request: Request,
    status: str | None = None,
    task_type: str | None = None,
    case_type: str | None = Query(default=None, alias="type"),
    risk_level: str | None = None,
    feature_code: str | None = None,
    keyword: str | None = None,
    query: str | None = Query(default=None, alias="q"),
    sort_by: str | None = None,
    sort: str | None = None,
    sort_order: str | None = None,
    order: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    include_archived: bool = False,
):
    conn = get_db()
    try:
        try:
            items = list_case_summaries(
                conn,
                status=status,
                task_type=task_type or case_type,
                risk_level=risk_level,
                feature_code=feature_code,
                keyword=keyword or query,
                sort_by=sort_by or sort or "updated_at",
                sort_order=sort_order or order or "desc",
                include_archived=include_archived,
            )
        except ValueError as exc:
            return _invalid_query(request, str(exc), "sort_by" if "sort_by" in str(exc) else "sort_order")
        total = len(items)
        start = (page - 1) * page_size
        return {
            "ok": True,
            "data": {
                "items": items[start:start + page_size],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "has_next": start + page_size < total,
                    "has_previous": page > 1 and start < total,
                },
                "sort": {
                    "by": sort_by or sort or "updated_at",
                    "order": sort_order or order or "desc",
                    "tie_breaker": "id desc",
                },
            },
            "meta": _meta(request),
        }
    finally:
        conn.close()


@router.get("/workbench/cases/{case_id}")
def get_workbench_case(request: Request, case_id: str):
    conn = get_db()
    try:
        detail = get_case_detail(conn, case_id)
    finally:
        conn.close()
    if detail is None:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "data": None,
                "error": {
                    "code": "WB_NOT_FOUND",
                    "message": "Butler case not found",
                    "details": {"resource_type": "case", "resource_id": case_id},
                    "retryable": False,
                },
                "meta": _meta(request),
            },
        )
    return {"ok": True, "data": detail, "meta": _meta(request)}
