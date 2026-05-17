from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.runtime_switch_service import select_runtime


router = APIRouter()


class SelectRuntimeRequest(BaseModel):
    runtime: str


@router.post("/api/runtime/select")
def runtime_select(payload: SelectRuntimeRequest) -> dict[str, object]:
    return select_runtime(payload.runtime)
