"""Test-version actions for WB-07 to mount."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from workbench.release_approval import ReleaseApprovalError, ReleaseApprovalService


router = APIRouter(prefix="/workbench/test-versions", tags=["workbench-test-versions"])
test_versions_router = router


def _meta(request: Request) -> dict:
    return {
        "schema_version": "workbench.v1",
        "request_id": request.headers.get("X-Request-ID") or uuid4().hex,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def _error(request: Request, error: ReleaseApprovalError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "ok": False,
            "data": None,
            "error": {
                "code": error.code,
                "message": str(error),
                "details": error.details,
                "retryable": False,
            },
            "meta": _meta(request),
        },
    )


@router.post("/{test_version_id}/submit-approval")
def submit_test_version_approval(
    request: Request,
    test_version_id: int,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    try:
        data = ReleaseApprovalService().submit(
            test_version_id, idempotency_key=idempotency_key
        )
    except ReleaseApprovalError as exc:
        return _error(request, exc)
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "data": None,
                "error": {
                    "code": "WB_INTERNAL",
                    "message": "Unable to submit release approval",
                    "details": {},
                    "retryable": False,
                },
                "meta": _meta(request),
            },
        )

    return JSONResponse(
        status_code=201,
        content={"ok": True, "data": data, "meta": _meta(request)},
    )


__all__ = ("router", "test_versions_router", "submit_test_version_approval")
