from fastapi import APIRouter

from backend.app.services.repair_service import (
    run_repair_config,
    run_repair_install,
    run_repair_model,
    run_repair_runtime,
)


router = APIRouter()


@router.post("/api/repair/install")
def repair_install() -> dict[str, object]:
    return run_repair_install()


@router.post("/api/repair/model")
def repair_model() -> dict[str, object]:
    return run_repair_model()


@router.post("/api/repair/runtime")
def repair_runtime() -> dict[str, object]:
    return run_repair_runtime()


@router.post("/api/repair/config")
def repair_config() -> dict[str, object]:
    return run_repair_config()
