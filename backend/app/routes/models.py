from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.models_service import (
    activate_model,
    add_hf_model,
    add_local_model,
    add_unsloth_model,
    delete_model,
    download_model,
    get_model_action_status,
    load_download_progress_payload,
    load_models_payload,
    start_model_action,
)
from backend.app.services.platform_config import get_target_platform


router = APIRouter()


@router.get("/api/models")
def models() -> dict[str, list[dict[str, object]]]:
    return load_models_payload()


@router.get("/api/models/download-progress")
def models_download_progress() -> dict[str, object]:
    return load_download_progress_payload()


@router.get("/api/models/action-status/{action_id}")
def models_action_status(action_id: str) -> dict[str, object]:
    return get_model_action_status(action_id)


class ActivateModelRequest(BaseModel):
    modelId: str


class AddLocalModelRequest(BaseModel):
    path: str
    label: str = ""
    family: str = "Custom"


class AddHfModelRequest(BaseModel):
    repo: str
    filename: str
    label: str = ""
    family: str = "Custom"


class AddUnslothModelRequest(BaseModel):
    repo: str
    filename: str
    label: str = ""
    family: str = "Unsloth"


class DeleteModelRequest(BaseModel):
    modelId: str
    removeFile: bool = True
    removeRegistry: bool = True


@router.post("/api/models/activate")
def models_activate(payload: ActivateModelRequest) -> dict[str, object]:
    return activate_model(payload.modelId)


@router.post("/api/models/download")
def models_download(payload: ActivateModelRequest) -> dict[str, object]:
    return download_model(payload.modelId)


@router.post("/api/models/add-local")
def models_add_local(payload: AddLocalModelRequest) -> dict[str, object]:
    if get_target_platform() == "windows":
        return start_model_action("add-local", path=payload.path, label=payload.label, family=payload.family)
    return add_local_model(payload.path, payload.label, payload.family)


@router.post("/api/models/add-hf")
def models_add_hf(payload: AddHfModelRequest) -> dict[str, object]:
    if get_target_platform() == "windows":
        return start_model_action(
            "add-hf",
            repo=payload.repo,
            filename=payload.filename,
            label=payload.label,
            family=payload.family,
        )
    return add_hf_model(payload.repo, payload.filename, payload.label, payload.family)


@router.post("/api/models/add-unsloth")
def models_add_unsloth(payload: AddUnslothModelRequest) -> dict[str, object]:
    if get_target_platform() == "windows":
        return start_model_action(
            "add-unsloth",
            repo=payload.repo,
            filename=payload.filename,
            label=payload.label,
            family=payload.family,
        )
    return add_unsloth_model(payload.repo, payload.filename, payload.label, payload.family)


@router.post("/api/models/delete")
def models_delete(payload: DeleteModelRequest) -> dict[str, object]:
    return delete_model(
        payload.modelId,
        remove_file=payload.removeFile,
        remove_registry=payload.removeRegistry,
    )
