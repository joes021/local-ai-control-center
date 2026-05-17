from fastapi import APIRouter

from backend.app.config import get_config
from backend.app.services.local_qwen_state import (
    build_status_payload,
    load_local_qwen_summary,
)


router = APIRouter()


@router.get("/api/status")
def status() -> dict[str, object]:
    config = get_config()
    summary = load_local_qwen_summary()
    return build_status_payload(
        summary,
        ui_port=config.ui_port,
        host=config.host,
        access_mode=config.access_mode,
    )
