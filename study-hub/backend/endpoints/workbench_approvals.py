"""Approval endpoints for the Study-Hub workbench."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from workbench.approvals import (
    ApprovalConflictError,
    ApprovalNotFoundError,
    get_approval,
    list_approvals,
    resolve_approval as resolve_approval_fact,
)


router = APIRouter(prefix="/workbench/approvals", tags=["workbench-approvals"])
approvals_router = router


class ApprovalResolution(BaseModel):
    approved: bool
    response: str = ""


@router.get("")
def approval_list(status: str | None = None):
    try:
        items = list_approvals(status=status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"items": items, "total": len(items)}


@router.get("/{approval_id}")
def approval_detail(approval_id: str):
    try:
        return get_approval(approval_id)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{approval_id}/resolve")
def approval_resolve(approval_id: str, payload: ApprovalResolution):
    try:
        resolve_approval_fact(
            approval_id,
            approved=payload.approved,
            response=payload.response,
        )
        return get_approval(approval_id)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ApprovalConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


__all__ = ("ApprovalResolution", "approvals_router", "router")
