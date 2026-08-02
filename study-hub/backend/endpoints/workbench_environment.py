"""Workstation environment and roadmap endpoints for WB-07 to mount."""

from fastapi import APIRouter

from workbench.environment import get_environment_info, get_roadmap


router = APIRouter(prefix="/workbench", tags=["workbench"])


@router.get("/environment")
def environment():
    return get_environment_info()


@router.get("/roadmap")
def roadmap():
    return get_roadmap()
