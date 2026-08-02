"""Read-only workbench case endpoints for later app mounting."""

from fastapi import APIRouter, HTTPException, Query

from database import get_db
from workbench.cases import get_case_detail, list_case_summaries

router = APIRouter(tags=["workbench"])


@router.get("/workbench/cases")
def list_workbench_cases(
    status: str | None = None,
    task_type: str | None = None,
    case_type: str | None = Query(default=None, alias="type"),
    keyword: str | None = None,
    query: str | None = Query(default=None, alias="q"),
    sort_by: str | None = None,
    sort: str | None = None,
    sort_order: str | None = None,
    order: str | None = None,
    include_archived: bool = False,
):
    conn = get_db()
    try:
        try:
            return list_case_summaries(
                conn,
                status=status,
                task_type=task_type or case_type,
                keyword=keyword or query,
                sort_by=sort_by or sort or "updated_at",
                sort_order=sort_order or order or "desc",
                include_archived=include_archived,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        conn.close()


@router.get("/workbench/cases/{case_id}")
def get_workbench_case(case_id: str):
    conn = get_db()
    try:
        detail = get_case_detail(conn, case_id)
    finally:
        conn.close()
    if detail is None:
        raise HTTPException(status_code=404, detail="Butler case not found")
    return detail
