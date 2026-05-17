from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.platform_config import get_target_platform
from backend.app.services.local_qwen_state import read_json_file
from backend.app.services.script_runner import run_linux_launcher
from backend.app.services.settings_service import (
    UNSLOTH_RECOMMENDED_MODELS,
    apply_settings,
    load_global_defaults_payload,
    load_model_override_payload,
)
from backend.app.services.windows_common_runner import invoke_windows_common_json


def load_models_payload() -> dict[str, list[dict[str, object]]]:
    home = detect_local_qwen_home()
    defaults = read_json_file(home / "config" / "profiles" / "defaults.json")
    install_state = read_json_file(home / "state" / "install-state.json")
    custom_registry = read_json_file(home / "state" / "custom-models.json")
    models_dir = home / "models"

    entries: list[dict[str, object]] = []
    active_model_id = str(install_state.get("modelId", "") or "")
    seen_ids: set[str] = set()

    for raw in (defaults.get("modelChoices") or {}).values():
        if not isinstance(raw, dict):
            continue
        built = _build_model_entry(raw, "curated", active_model_id, models_dir)
        entries.append(built)
        seen_ids.add(str(built["id"]))

    for raw in UNSLOTH_RECOMMENDED_MODELS:
        built = _build_model_entry(
            {
                "id": raw["id"],
                "label": raw["label"],
                "filename": raw["filename"],
                "family": "Unsloth",
                "description": raw["fitNote"],
            },
            "unsloth",
            active_model_id,
            models_dir,
        )
        if str(built["id"]) not in seen_ids:
            entries.append(built)
            seen_ids.add(str(built["id"]))

    for raw in custom_registry.get("models") or []:
        if not isinstance(raw, dict):
            continue
        custom_source = str(raw.get("customSource", "") or "").lower()
        if custom_source == "huggingface":
            source = "huggingface"
        elif custom_source == "unsloth":
            source = "unsloth"
        else:
            source = "local"
        built = _build_model_entry(raw, source, active_model_id, models_dir)
        entries = [item for item in entries if str(item.get("id")) != str(built["id"])]
        entries.append(built)
        seen_ids.add(str(built["id"]))

    return normalize_models(entries)


def normalize_models(models: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    payload = {
        "curated": [],
        "local": [],
        "huggingFace": [],
        "unsloth": [],
    }
    for model in models:
        source = model.get("source")
        if source == "local":
            payload["local"].append(model)
        elif source == "unsloth":
            payload["unsloth"].append(model)
        elif source == "huggingface":
            payload["huggingFace"].append(model)
        else:
            payload["curated"].append(model)
    return payload


def activate_model(model_id: str) -> dict[str, object]:
    if get_target_platform() == "windows":
        return _activate_model_windows(model_id)
    ensure_result = _ensure_unsloth_registered(model_id)
    if ensure_result is not None and ensure_result.get("status") != "ok":
        return ensure_result
    result = run_linux_launcher("manage-models.sh", "use", model_id)
    if result.get("status") != "ok":
        return result

    override = load_model_override_payload(model_id)
    payload_to_apply = None
    label = ""
    if override:
        override["settingsScope"] = "model"
        override["activeModelId"] = model_id
        payload_to_apply = override
        label = f"override primenjen za {model_id}"
    else:
        global_defaults = load_global_defaults_payload()
        if global_defaults:
            global_defaults["settingsScope"] = "global"
            global_defaults["activeModelId"] = model_id
            payload_to_apply = global_defaults
            label = "globalni defaults su vraceni"

    if payload_to_apply:
        apply_result = apply_settings(payload_to_apply)
        if apply_result.get("status") == "ok":
            result["summary"] = f"{result['summary']} | {label}"
            details = result.get("details", {})
            if isinstance(details, dict):
                details["stdout"] = (
                    f"{details.get('stdout', '')}\n{apply_result.get('details', {}).get('stdout', '')}".strip()
                )
        else:
            return apply_result
    return result


def download_model(model_id: str) -> dict[str, object]:
    if get_target_platform() == "windows":
        return _download_model_windows(model_id)
    ensure_result = _ensure_unsloth_registered(model_id)
    if ensure_result is not None and ensure_result.get("status") != "ok":
        return ensure_result
    return run_linux_launcher("manage-models.sh", "download", model_id)


def add_local_model(path: str, label: str = "", family: str = "Custom") -> dict[str, object]:
    if get_target_platform() == "windows":
        result = invoke_windows_common_json("Import-LocalGgufModel", path, label, family)
        payload = result.get("payload", {})
        if result.get("status") == "ok":
            model_id = payload.get("id", "") if isinstance(payload, dict) else ""
            return {
                "status": "ok",
                "action": "Import-LocalGgufModel",
                "summary": f"Lokalni model dodat: {model_id or path}",
                "details": {
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                },
            }
        result.pop("payload", None)
        return result
    args = ["add-local", path]
    if label:
        args.append(label)
    if family:
        args.append(family)
    return run_linux_launcher("manage-models.sh", *args)


def add_hf_model(
    repo: str,
    filename: str,
    label: str = "",
    family: str = "Custom",
) -> dict[str, object]:
    if get_target_platform() == "windows":
        result = invoke_windows_common_json("Add-HuggingFaceCustomModel", repo, filename, label, family)
        payload = result.get("payload", {})
        if result.get("status") == "ok":
            model_id = payload.get("id", "") if isinstance(payload, dict) else ""
            return {
                "status": "ok",
                "action": "Add-HuggingFaceCustomModel",
                "summary": f"HF model dodat: {model_id or filename}",
                "details": {
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                },
            }
        result.pop("payload", None)
        return result
    args = ["add-hf", repo, filename]
    if label:
        args.append(label)
    if family:
        args.append(family)
    return run_linux_launcher("manage-models.sh", *args)


def add_unsloth_model(
    repo: str,
    filename: str,
    label: str = "",
    family: str = "Unsloth",
) -> dict[str, object]:
    if get_target_platform() == "windows":
        result = invoke_windows_common_json("Add-UnslothCustomModel", repo, filename, label, family)
        payload = result.get("payload", {})
        if result.get("status") == "ok":
            model_id = payload.get("id", "") if isinstance(payload, dict) else ""
            return {
                "status": "ok",
                "action": "Add-UnslothCustomModel",
                "summary": f"Unsloth model dodat: {model_id or filename}",
                "details": {
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                },
            }
        result.pop("payload", None)
        return result
    args = ["add-unsloth", repo, filename]
    if label:
        args.append(label)
    if family:
        args.append(family)
    return run_linux_launcher("manage-models.sh", *args)


def delete_model(
    model_id: str,
    *,
    local_qwen_home: Path | None = None,
    remove_file: bool = True,
    remove_registry: bool = True,
) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    install_state = read_json_file(home / "state" / "install-state.json")
    active_model_id = str(install_state.get("modelId", "") or "")
    defaults = read_json_file(home / "config" / "profiles" / "defaults.json")
    custom_registry_path = home / "state" / "custom-models.json"
    custom_registry = read_json_file(custom_registry_path)
    models_dir = home / "models"

    metadata = _find_model_metadata(model_id, defaults, custom_registry)
    if not metadata:
        return _result("error", "delete-model", f"Model nije pronadjen: {model_id}")

    if active_model_id == model_id and remove_file:
        return _result(
            "error",
            "delete-model",
            f"Aktivni model ne moze da se obrise sa diska dok je aktivan: {model_id}",
        )
    if not remove_file and not remove_registry:
        return _result("error", "delete-model", "Izaberi bar jednu delete akciju.")

    filename = str(metadata.get("filename", "") or "")
    target_path = models_dir / filename if filename else None
    removed_file = False
    removed_registry = False

    if remove_file and target_path and target_path.is_file():
        target_path.unlink()
        removed_file = True

    if remove_registry and metadata.get("isCustom"):
        models = [
            item
            for item in (custom_registry.get("models") or [])
            if not (isinstance(item, dict) and str(item.get("id")) == model_id)
        ]
        custom_registry["models"] = models
        custom_registry_path.write_text(
            json.dumps(custom_registry, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        removed_registry = True

    if remove_registry and not metadata.get("isCustom"):
        removed_registry = False

    summary_bits = []
    if removed_file:
        summary_bits.append("fajl obrisan sa diska")
    elif remove_file:
        summary_bits.append("fajl nije postojao")
    if removed_registry:
        summary_bits.append("uklonjen iz kataloga")
    elif metadata.get("isCustom") and remove_registry:
        summary_bits.append("nije bilo potrebe za dodatnim uklanjanjem iz kataloga")
    if not summary_bits:
        summary_bits.append("nije bilo promena")

    return {
        "status": "ok",
        "action": "delete-model",
        "summary": f"{model_id}: " + ", ".join(summary_bits),
        "details": {
            "returncode": 0,
            "stdout": json.dumps(
                {
                    "modelId": model_id,
                    "removedFile": removed_file,
                    "removedRegistry": removed_registry,
                    "targetPath": str(target_path) if target_path else "",
                },
                ensure_ascii=False,
            ),
            "stderr": "",
        },
    }


def _build_model_entry(
    raw: dict[str, object],
    source: str,
    active_model_id: str,
    models_dir: Path,
) -> dict[str, object]:
    filename = str(raw.get("filename", "") or "")
    model_id = str(raw.get("id", filename) or filename)
    installed = bool(filename and (models_dir / filename).is_file())
    return {
        "id": model_id,
        "label": str(raw.get("label", model_id) or model_id),
        "source": source,
        "active": model_id == active_model_id,
        "installed": installed,
        "filename": filename,
        "family": str(raw.get("family", "Unknown")),
        "description": str(raw.get("description", "")),
        "isCustom": source in {"local", "huggingface", "unsloth"},
    }


def _ensure_unsloth_registered(model_id: str) -> dict[str, object] | None:
    metadata = _find_unsloth_recommendation(model_id)
    if not metadata:
        return None
    registry = read_json_file(detect_local_qwen_home() / "state" / "custom-models.json")
    for item in registry.get("models") or []:
        if isinstance(item, dict) and str(item.get("id")) == model_id:
            return None
    return add_unsloth_model(
        str(metadata["repo"]),
        str(metadata["filename"]),
        str(metadata["label"]),
        "Unsloth",
    )


def _find_unsloth_recommendation(model_id: str) -> dict[str, object] | None:
    for item in UNSLOTH_RECOMMENDED_MODELS:
        if str(item.get("id")) == str(model_id):
            return item
    return None


def _find_model_metadata(
    model_id: str,
    defaults: dict[str, object],
    custom_registry: dict[str, object],
) -> dict[str, object] | None:
    for raw in (defaults.get("modelChoices") or {}).values():
        if isinstance(raw, dict) and (raw.get("id") == model_id or raw.get("filename") == model_id):
            payload = dict(raw)
            payload["isCustom"] = False
            return payload
    for raw in custom_registry.get("models") or []:
        if isinstance(raw, dict) and raw.get("id") == model_id:
            payload = dict(raw)
            payload["isCustom"] = True
            return payload
    return None


def _result(status: str, action: str, summary: str) -> dict[str, object]:
    return {
        "status": status,
        "action": action,
        "summary": summary,
        "details": {
            "returncode": 1 if status != "ok" else 0,
            "stdout": "",
            "stderr": "" if status == "ok" else summary,
        },
    }


def _activate_model_windows(model_id: str) -> dict[str, object]:
    result = invoke_windows_common_json("Set-SelectedModel", model_id)
    if result.get("status") != "ok":
        return result
    return {
        "status": "ok",
        "action": "Set-SelectedModel",
        "summary": f"Model postavljen na: {model_id}",
        "details": result["details"],
    }


def _download_model_windows(model_id: str) -> dict[str, object]:
    result = invoke_windows_common_json("Download-RecommendedModel", model_id)
    if result.get("status") != "ok":
        return result
    return {
        "status": "ok",
        "action": "Download-RecommendedModel",
        "summary": f"Model download pokrenut za: {model_id}",
        "details": result["details"],
    }
