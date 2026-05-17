from fastapi import APIRouter

from backend.app.services.logs_service import load_logs_preview


router = APIRouter()


@router.get("/api/logs")
def logs() -> dict[str, object]:
    return load_logs_preview()
