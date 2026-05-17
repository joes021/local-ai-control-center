from fastapi import APIRouter

from backend.app.services.updates_service import check_updates, install_update


router = APIRouter()


@router.get("/api/updates/check")
def updates_check() -> dict[str, object]:
    return check_updates()


@router.post("/api/updates/install")
def updates_install() -> dict[str, object]:
    return install_update()
