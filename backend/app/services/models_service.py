from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
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


_MODEL_ACTIONS: dict[str, dict[str, object]] = {}
_UNSLOTH_MTP_REPO_STATUS = {
    "unsloth/qwen3.6-35b-a3b-gguf": "no-mtp",
    "unsloth/qwen3.6-35b-a3b-mtp-gguf": "has-mtp",
    "unsloth/qwen3.6-27b-gguf": "no-mtp",
    "unsloth/qwen3.6-27b-mtp-gguf": "has-mtp",
}


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


def load_download_progress_payload() -> dict[str, object]:
    home = detect_local_qwen_home()
    path = home / "state" / "model-download-progress.json"
    if not path.is_file():
        return {
            "status": "idle",
            "isActive": False,
            "modelId": "",
            "fileName": "",
            "source": "",
            "percent": None,
            "downloadedGiB": None,
            "totalGiB": None,
            "speedMBps": None,
            "etaSeconds": None,
            "message": "Nema aktivnog download-a.",
            "updatedAt": "",
        }

    payload = read_json_file(path)
    status = str(payload.get("status", "") or "idle")
    message = str(payload.get("message", "") or "").strip()
    return {
        "status": status,
        "isActive": status in {"starting", "downloading"},
        "modelId": str(payload.get("modelId", "") or ""),
        "fileName": str(payload.get("fileName", "") or ""),
        "source": str(payload.get("source", "") or ""),
        "percent": _as_float(payload.get("percent")),
        "downloadedGiB": _as_float(payload.get("downloadedGiB")),
        "totalGiB": _as_float(payload.get("totalGiB")),
        "speedMBps": _as_float(payload.get("speedMBps")),
        "etaSeconds": _as_int(payload.get("etaSeconds")),
        "message": message or _default_progress_message(status),
        "updatedAt": str(payload.get("updatedAt", "") or ""),
    }


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
                "summary": f"HF model dodat u spisak: {model_id or filename}. Sledeci korak je Download.",
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
                "summary": f"Unsloth model dodat u spisak: {model_id or filename}. Sledeci korak je Download.",
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


def start_model_action(kind: str, **kwargs: str) -> dict[str, object]:
    action_id = f"model-action-{uuid.uuid4()}"
    summary = {
        "add-local": "Dodavanje lokalnog modela je pokrenuto.",
        "add-hf": "Dodavanje Hugging Face modela je pokrenuto.",
        "add-unsloth": "Dodavanje Unsloth modela je pokrenuto.",
    }.get(kind, "Model akcija je pokrenuta.")

    _MODEL_ACTIONS[action_id] = {
        "status": "pending",
        "summary": summary,
        "result": None,
    }
    _write_model_action_status_file(
        action_id,
        {
            "actionId": action_id,
            "status": "pending",
            "summary": summary,
            "isDone": False,
            "result": None,
        },
    )
    _spawn_model_action_worker(action_id, kind, kwargs)
    return {
        "status": "accepted",
        "action": kind,
        "actionId": action_id,
        "summary": summary,
        "details": {"returncode": 0, "stdout": "", "stderr": ""},
    }


def get_model_action_status(action_id: str) -> dict[str, object]:
    file_payload = read_json_file(_get_model_action_status_path(action_id))
    if file_payload:
        return {
            "actionId": action_id,
            "status": str(file_payload.get("status", "pending") or "pending"),
            "summary": str(file_payload.get("summary", "") or ""),
            "isDone": bool(file_payload.get("isDone", False)),
            "result": file_payload.get("result"),
        }

    payload = dict(_MODEL_ACTIONS.get(action_id) or {})
    if not payload:
        return {
            "actionId": action_id,
            "status": "missing",
            "summary": "Model akcija nije pronadjena.",
            "isDone": True,
            "result": None,
        }
    status = str(payload.get("status", "pending") or "pending")
    return {
        "actionId": action_id,
        "status": status,
        "summary": str(payload.get("summary", "") or ""),
        "isDone": status in {"completed", "error"},
        "result": payload.get("result"),
    }


def complete_model_action(action_id: str, result: dict[str, object]) -> None:
    status = "completed" if result.get("status") == "ok" else "error"
    _MODEL_ACTIONS[action_id] = {
        "status": status,
        "summary": str(result.get("summary", "") or ""),
        "result": result,
    }
    _write_model_action_status_file(
        action_id,
        {
            "actionId": action_id,
            "status": status,
            "summary": str(result.get("summary", "") or ""),
            "isDone": True,
            "result": result,
        },
    )


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
    mtp_status = _classify_mtp_status(
        source=source,
        model_id=model_id,
        filename=filename,
        raw=raw,
    )
    target_path = models_dir / filename if filename else None
    installed = bool(target_path and target_path.is_file())
    installed_size_bytes = target_path.stat().st_size if installed and target_path else 0
    approx_size_gib = _as_float(raw.get("approxSizeGiB"))
    installed_size_gib = round(installed_size_bytes / (1024 ** 3), 2) if installed_size_bytes > 0 else None
    free_disk_gib = _get_free_disk_gib(models_dir)
    min_expected_bytes = _as_int(raw.get("minExpectedBytes")) or 0
    approx_size_bytes = int((approx_size_gib or 0) * (1024 ** 3))
    if min_expected_bytes > 0:
        disk_needed_bytes = max(0, min_expected_bytes - installed_size_bytes)
    else:
        disk_needed_bytes = max(0, approx_size_bytes - installed_size_bytes)
    disk_needed_gib = round(disk_needed_bytes / (1024 ** 3), 2) if disk_needed_bytes > 0 else 0.0
    has_enough_disk = None if free_disk_gib is None else free_disk_gib >= disk_needed_gib
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
        "mtpStatus": mtp_status,
        "mtpStatusLabel": _get_mtp_status_label(mtp_status),
        "approxSizeGiB": approx_size_gib,
        "minimumGpuMiB": _as_int(raw.get("minimumGpuMiB")),
        "recommendedGpuMiB": _as_int(raw.get("recommendedGpuMiB")),
        "minimumRamGiB": _as_int(raw.get("minimumRamGiB")),
        "installedSizeGiB": installed_size_gib,
        "diskNeededGiB": disk_needed_gib,
        "freeDiskGiB": free_disk_gib,
        "hasEnoughDisk": has_enough_disk,
    }


def _classify_mtp_status(*, source: str, model_id: str, filename: str, raw: dict[str, object]) -> str:
    explicit = str(raw.get("mtpStatus", "") or "").strip().lower()
    if explicit in {"no-mtp", "has-mtp", "unknown"}:
        return explicit

    repo = str(raw.get("repo", "") or raw.get("source", "") or "").strip().lower()
    if repo in _UNSLOTH_MTP_REPO_STATUS:
        return _UNSLOTH_MTP_REPO_STATUS[repo]

    joined = " ".join(
        [
            source or "",
            model_id or "",
            filename or "",
            repo,
            str(raw.get("description", "") or ""),
            str(raw.get("customSource", "") or ""),
        ]
    ).lower()

    if "mtp-gguf" in joined or "-mtp" in joined or " mtp" in joined:
        return "has-mtp"

    if source == "unsloth" and "mtp-gguf" not in joined:
        return "no-mtp"

    return "unknown"


def _get_mtp_status_label(status: str) -> str:
    return {
        "no-mtp": "bez MTP",
        "has-mtp": "ima MTP",
        "unknown": "nepoznato",
    }.get(status, "nepoznato")


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
    config_refresh = invoke_windows_common_json("Update-OpenCodeConfig")
    if config_refresh.get("status") != "ok":
        return {
            "status": "error",
            "action": "Set-SelectedModel",
            "summary": f"Model jeste promenjen na {model_id}, ali OpenCode config nije osvezen.",
            "details": config_refresh["details"],
        }
    return {
        "status": "ok",
        "action": "Set-SelectedModel",
        "summary": f"Model postavljen na: {model_id}. OpenCode config je osvezen za novi session.",
        "details": {
            "returncode": 0,
            "stdout": "\n".join(
                part
                for part in [
                    str(result["details"].get("stdout", "") or "").strip(),
                    str(config_refresh["details"].get("stdout", "") or "").strip(),
                ]
                if part
            ),
            "stderr": "",
        },
    }


def _download_model_windows(model_id: str) -> dict[str, object]:
    script_path = _resolve_windows_manage_models_script()
    if not script_path.is_file():
        return _result("error", "download-model", f"Windows manage-models skripta nije pronadjena: {script_path}")

    home = detect_local_qwen_home()
    progress_path = home / "state" / "model-download-progress.json"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps(
            {
                "status": "starting",
                "modelId": model_id,
                "fileName": "",
                "source": "",
                "percent": 0.0,
                "downloadedGiB": 0.0,
                "totalGiB": None,
                "speedMBps": None,
                "etaSeconds": None,
                "message": f"Pokrecem download za {model_id}",
                "updatedAt": "",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    creation_flags = 0
    if os.name == "nt":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    process = subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-ModelId",
            model_id,
            "-Download",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creation_flags,
        close_fds=False,
    )
    return {
        "status": "ok",
        "action": "download-model",
        "summary": f"Download je pokrenut za: {model_id}",
        "details": {
            "returncode": 0,
            "stdout": json.dumps({"pid": process.pid, "progressPath": str(progress_path)}, ensure_ascii=False),
            "stderr": "",
        },
    }


def _resolve_windows_manage_models_script() -> Path:
    installed = detect_local_qwen_home() / "launchers" / "manage-models.ps1"
    if installed.is_file():
        return installed
    return Path(r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows\manage-models.ps1")


def _as_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _default_progress_message(status: str) -> str:
    return {
        "starting": "Download se priprema.",
        "downloading": "Download je u toku.",
        "completed": "Download je zavrsen.",
        "error": "Download je prijavio gresku.",
    }.get(status, "Nema aktivnog download-a.")


def _run_model_action_worker(action_id: str, kind: str, kwargs: dict[str, str]) -> None:
    try:
        if kind == "add-local":
            result = add_local_model(
                kwargs.get("path", ""),
                kwargs.get("label", ""),
                kwargs.get("family", "Custom"),
            )
        elif kind == "add-hf":
            result = add_hf_model(
                kwargs.get("repo", ""),
                kwargs.get("filename", ""),
                kwargs.get("label", ""),
                kwargs.get("family", "Custom"),
            )
        elif kind == "add-unsloth":
            result = add_unsloth_model(
                kwargs.get("repo", ""),
                kwargs.get("filename", ""),
                kwargs.get("label", ""),
                kwargs.get("family", "Unsloth"),
            )
        else:
            result = _result("error", kind, f"Nepoznata model akcija: {kind}")
    except Exception as exc:  # noqa: BLE001
        result = _result("error", kind, str(exc))

    complete_model_action(action_id, result)


def _get_model_action_status_path(action_id: str) -> Path:
    home = detect_local_qwen_home()
    directory = home / "state" / "control-center-next" / "model-actions"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{action_id}.json"


def _write_model_action_status_file(action_id: str, payload: dict[str, object]) -> None:
    _get_model_action_status_path(action_id).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _spawn_model_action_worker(action_id: str, kind: str, kwargs: dict[str, str]) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    worker_path = repo_root / "backend" / "app" / "workers" / "model_action_worker.py"
    args_payload = json.dumps(kwargs, ensure_ascii=False)

    creation_flags = 0
    if os.name == "nt":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    process = subprocess.Popen(
        [
            sys.executable,
            str(worker_path),
            "--action-id",
            action_id,
            "--kind",
            kind,
            "--kwargs-json",
            args_payload,
        ],
        cwd=str(repo_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creation_flags,
        close_fds=False,
    )
    _MODEL_ACTIONS[action_id]["workerPid"] = process.pid


def _get_free_disk_gib(models_dir: Path) -> float | None:
    try:
        import shutil

        usage = shutil.disk_usage(models_dir)
        return round(usage.free / (1024 ** 3), 2)
    except Exception:  # noqa: BLE001
        return None
