from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.browser_catalog_service import load_catalog_payload, refresh_catalog
from backend.app.services.compatibility_service import check_model_compatibility
from backend.app.services.models_service import add_hf_model, add_unsloth_model, load_models_payload


router = APIRouter()


@router.get("/api/browser/catalog")
def browser_catalog() -> dict[str, object]:
    return load_catalog_payload()


class RefreshCatalogRequest(BaseModel):
    source: str = "all"


@router.post("/api/browser/catalog/refresh")
def browser_refresh(payload: RefreshCatalogRequest) -> dict[str, object]:
    return refresh_catalog(source=payload.source)


class AddCatalogModelRequest(BaseModel):
    source: str
    repoId: str
    filename: str
    label: str = ""
    family: str = "Custom"


def add_catalog_model(*, source: str, repo_id: str, filename: str, label: str, family: str) -> dict[str, object]:
    normalized_source = (source or "").strip().lower()
    if normalized_source == "unsloth":
        result = add_unsloth_model(repo_id, filename, label, family or "Unsloth")
    else:
        result = add_hf_model(repo_id, filename, label, family or "Custom")
    local_model_id = _resolve_local_model_id(normalized_source, filename)
    if local_model_id:
        result["localModelId"] = local_model_id
    result.setdefault("promptDownload", True)
    return result


@router.post("/api/browser/catalog/add")
def browser_add(payload: AddCatalogModelRequest) -> dict[str, object]:
    return add_catalog_model(
        source=payload.source,
        repo_id=payload.repoId,
        filename=payload.filename,
        label=payload.label,
        family=payload.family,
    )


class CheckCompatibilityRequest(BaseModel):
    modelId: str


@router.post("/api/browser/catalog/check-compatibility")
def browser_check_compatibility(payload: CheckCompatibilityRequest) -> dict[str, object]:
    return check_model_compatibility(model_id=payload.modelId)


def _resolve_local_model_id(source: str, filename: str) -> str:
    payload = load_models_payload()
    for group_name in ("local", "huggingFace", "unsloth", "curated"):
        for item in payload.get(group_name, []):
            if not isinstance(item, dict):
                continue
            if str(item.get("filename", "") or "") != filename:
                continue
            item_source = str(item.get("source", "") or "").lower()
            if item_source == source:
                return str(item.get("id", "") or "")
    return ""
