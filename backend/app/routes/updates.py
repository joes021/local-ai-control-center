from fastapi import APIRouter

from backend.app.services.updates_service import (
    check_updates,
    read_update_progress,
    start_install_update_job,
)


router = APIRouter()


@router.get("/api/updates/check")
def updates_check() -> dict[str, object]:
    return check_updates()


@router.post("/api/updates/install")
def updates_install() -> dict[str, object]:
    return start_install_update_job()


@router.get("/api/updates/progress")
def updates_progress() -> dict[str, object]:
    return read_update_progress()
