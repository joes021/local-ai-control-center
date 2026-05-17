from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.settings_service import (
    apply_settings,
    delete_turboquant_user_preset,
    load_settings_payload,
    load_turboquant_config,
    load_turboquant_schema,
    save_turboquant_config,
    save_turboquant_user_preset,
)


router = APIRouter()


@router.get("/api/settings")
def settings() -> dict[str, int | str | bool]:
    return load_settings_payload()


@router.get("/api/settings/turboquant")
def turboquant_settings() -> dict[str, object]:
    return load_turboquant_schema()


class ApplySettingsRequest(BaseModel):
    profile: str
    context: int
    outputTokens: int
    workingDirectory: str
    thinkingMode: str
    settingsScope: str = "global"
    activeModelId: str = ""
    accessMode: str = "local-only"


@router.post("/api/settings/apply")
def settings_apply(payload: ApplySettingsRequest) -> dict[str, object]:
    return apply_settings(payload.model_dump())


class SaveTurboQuantConfigRequest(BaseModel):
    context: int
    ctk: str
    ctv: str
    ncmoe: int
    flashAttention: bool
    mlock: bool
    mmapMode: str
    runtimePreference: str


class SaveTurboQuantPresetRequest(BaseModel):
    name: str
    description: str = ""
    targetModelPattern: str = ""
    notes: str = ""
    settings: SaveTurboQuantConfigRequest


class DeleteTurboQuantPresetRequest(BaseModel):
    presetId: str


@router.get("/api/settings/turboquant-config")
def turboquant_config() -> dict[str, object]:
    return load_turboquant_config()


@router.post("/api/settings/turboquant-config")
def turboquant_config_save(payload: SaveTurboQuantConfigRequest) -> dict[str, object]:
    saved = save_turboquant_config(payload.model_dump())
    return {
        "status": "ok",
        "action": "save-turboquant-config",
        "summary": "TurboQuant konfiguracija je sacuvana.",
        "details": {
            "returncode": 0,
            "stdout": str(saved),
            "stderr": "",
        },
    }


@router.post("/api/settings/turboquant-presets/save")
def turboquant_preset_save(payload: SaveTurboQuantPresetRequest) -> dict[str, object]:
    saved = save_turboquant_user_preset(payload.model_dump())
    return {
        "status": "ok",
        "action": "save-turboquant-preset",
        "summary": f"Sacuvan je preset: {saved['name']}",
        "details": {
            "returncode": 0,
            "stdout": str(saved),
            "stderr": "",
        },
    }


@router.post("/api/settings/turboquant-presets/delete")
def turboquant_preset_delete(payload: DeleteTurboQuantPresetRequest) -> dict[str, object]:
    deleted = delete_turboquant_user_preset(payload.presetId)
    return {
        "status": "ok" if deleted else "error",
        "action": "delete-turboquant-preset",
        "summary": "Preset je obrisan." if deleted else "Preset nije pronadjen.",
        "details": {
            "returncode": 0 if deleted else 1,
            "stdout": payload.presetId if deleted else "",
            "stderr": "" if deleted else "Preset nije pronadjen.",
        },
    }
