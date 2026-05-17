from fastapi import APIRouter

from backend.app.services.native_dialogs import pick_directory, pick_file


router = APIRouter()


@router.post("/api/system/pick-local-gguf")
def system_pick_local_gguf() -> dict[str, object]:
    return pick_file(title="Izaberi lokalni GGUF model", file_filter_name="GGUF", pattern="*.gguf")


@router.post("/api/system/pick-working-directory")
def system_pick_working_directory() -> dict[str, object]:
    return pick_directory(title="Izaberi working directory")
