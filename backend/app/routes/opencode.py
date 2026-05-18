from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.opencode_service import (
    apply_opencode_settings,
    load_opencode_status_payload,
    open_opencode,
)
from backend.app.services.settings_service import (
    delete_opencode_step_preset,
    load_opencode_step_schema,
    save_opencode_step_preset,
)


router = APIRouter()


@router.get("/api/opencode/status")
def opencode_status() -> dict[str, object]:
    return load_opencode_status_payload()


@router.get("/api/opencode/steps")
def opencode_steps() -> dict[str, object]:
    status = load_opencode_status_payload()
    return load_opencode_step_schema(
        current_steps={
            "buildSteps": int(status.get("buildSteps", 140) or 140),
            "planSteps": int(status.get("planSteps", 100) or 100),
            "generalSteps": int(status.get("generalSteps", 110) or 110),
            "exploreSteps": int(status.get("exploreSteps", 80) or 80),
        }
    )


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


class SaveOpenCodeStepPresetRequest(BaseModel):
    name: str
    steps: dict[str, int]


class DeleteOpenCodeStepPresetRequest(BaseModel):
    presetId: str


@router.post("/api/opencode/settings/apply")
def opencode_settings_apply(payload: ApplyOpenCodeSettingsRequest) -> dict[str, object]:
    return apply_opencode_settings(payload.model_dump())


@router.post("/api/opencode/open")
def opencode_open(payload: OpenOpenCodeRequest) -> dict[str, object]:
    return open_opencode(payload.profile)


@router.post("/api/opencode/steps/presets/save")
def opencode_steps_preset_save(payload: SaveOpenCodeStepPresetRequest) -> dict[str, object]:
    preset = save_opencode_step_preset(payload.model_dump())
    return {
        "status": "ok",
        "action": "save-opencode-step-preset",
        "summary": f"OpenCode preset je sacuvan: {preset['name']}",
        "preset": preset,
        "details": {"returncode": 0, "stdout": "", "stderr": ""},
    }


@router.post("/api/opencode/steps/presets/delete")
def opencode_steps_preset_delete(payload: DeleteOpenCodeStepPresetRequest) -> dict[str, object]:
    deleted = delete_opencode_step_preset(payload.presetId)
    if not deleted:
        return {
            "status": "error",
            "action": "delete-opencode-step-preset",
            "summary": "OpenCode preset nije pronadjen.",
            "details": {"returncode": 1, "stdout": "", "stderr": "OpenCode preset nije pronadjen."},
        }
    return {
        "status": "ok",
        "action": "delete-opencode-step-preset",
        "summary": "OpenCode preset je obrisan.",
        "details": {"returncode": 0, "stdout": "", "stderr": ""},
    }
