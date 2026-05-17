from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.opencode_service import (
    apply_opencode_settings,
    load_opencode_status_payload,
    open_opencode,
)


router = APIRouter()


@router.get("/api/opencode/status")
def opencode_status() -> dict[str, object]:
    return load_opencode_status_payload()


class ApplyOpenCodeSettingsRequest(BaseModel):
    profile: str
    context: int
    outputTokens: int
    workingDirectory: str
    buildSteps: int
    planSteps: int
    generalSteps: int
    exploreSteps: int
    securityMode: str
    capabilityMode: str


class OpenOpenCodeRequest(BaseModel):
    profile: str = ""


@router.post("/api/opencode/settings/apply")
def opencode_settings_apply(payload: ApplyOpenCodeSettingsRequest) -> dict[str, object]:
    return apply_opencode_settings(payload.model_dump())


@router.post("/api/opencode/open")
def opencode_open(payload: OpenOpenCodeRequest) -> dict[str, object]:
    return open_opencode(payload.profile)
