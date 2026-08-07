"""Top-level router for the Study-Hub workbench API."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Request

from endpoints.workbench_approvals import router as approvals_router
from endpoints.workbench_cases import router as cases_router
from endpoints.workbench_environment import router as environment_router
from endpoints.workbench_test_versions import router as test_versions_router
from endpoints.workbench_versions import router as versions_router
from workbench.overview import build_overview


router = APIRouter(tags=["workbench"])


def _meta(request: Request) -> dict[str, str]:
    return {
        "schema_version": "workbench.v1",
        "request_id": request.headers.get("X-Request-ID") or uuid4().hex,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
    }


@router.get("/workbench/overview")
def workbench_overview(request: Request):
    return {"ok": True, "data": build_overview(), "meta": _meta(request)}


router.include_router(cases_router)
router.include_router(approvals_router)
router.include_router(versions_router)
router.include_router(environment_router)
router.include_router(test_versions_router)


__all__ = ("router", "workbench_overview")
