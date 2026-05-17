from __future__ import annotations

import json
from pathlib import Path
import contextlib
import re
from uuid import uuid4

from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.local_qwen_state import read_json_file
from backend.app.services.runtime_config_service import (
    load_runtime_config,
    save_runtime_config,
)
from backend.app.services.script_runner import run_linux_launcher


THINKING_PRESETS = {
    "no-thinking": {
        "thinkingMode": "no-thinking",
        "buildSteps": 20,
        "planSteps": 20,
        "generalSteps": 20,
        "exploreSteps": 10,
    },
    "low": {
        "thinkingMode": "low",
        "buildSteps": 40,
        "planSteps": 30,
        "generalSteps": 35,
        "exploreSteps": 20,
    },
    "mid": {
        "thinkingMode": "mid",
        "buildSteps": 80,
        "planSteps": 60,
        "generalSteps": 70,
        "exploreSteps": 40,
    },
    "high": {
        "thinkingMode": "high",
        "buildSteps": 120,
        "planSteps": 100,
        "generalSteps": 100,
        "exploreSteps": 60,
    },
    "extra-high": {
        "thinkingMode": "extra-high",
        "buildSteps": 180,
        "planSteps": 160,
        "generalSteps": 160,
        "exploreSteps": 100,
    },
}

MODEL_OVERRIDE_FILE = "control-center-next-model-settings.json"
GLOBAL_DEFAULTS_FILE = "control-center-next-global-settings.json"
PROJECT_STATE_DIR = Path(__file__).resolve().parents[3] / "state"
LEGACY_BACKEND_STATE_DIR = Path(__file__).resolve().parents[2] / "state"
TURBOQUANT_CONFIG_FILE = "control-center-next-turboquant-config.json"
TURBOQUANT_PRESETS_FILE = "control-center-next-turboquant-presets.json"

TURBOQUANT_PARAMETERS = [
    {
        "id": "context",
        "label": "Context",
        "whatIsIt": "Koliko tokena razgovora i radnog konteksta zadrzavas u KV cache-u.",
        "effect": "Najveci memorijski prekidac: veci context trosi vise memorije, ali drzi duze sesije.",
        "recommendation": "Prvo diraj context, pa tek onda agresivnije TurboQuant nivoe.",
        "safeChoices": ["65536", "131072"],
        "advancedChoices": ["262144", "327680"],
        "defaultValue": 131072,
    },
    {
        "id": "ctk",
        "label": "ctk",
        "whatIsIt": "Tip kompresije za K deo KV cache-a.",
        "effect": "turbo4 manje kompresuje i bezbedniji je; turbo3 je balans; turbo2 najvise stedi memoriju, ali je najagresivniji.",
        "recommendation": "Za 3060 12 GB kreni sa turbo4.",
        "safeChoices": ["turbo4"],
        "advancedChoices": ["turbo3", "turbo2"],
        "defaultValue": "turbo4",
    },
    {
        "id": "ctv",
        "label": "ctv",
        "whatIsIt": "Tip kompresije za V deo KV cache-a.",
        "effect": "Moze mrvu agresivnije od ctk bez prejakog udara po kvalitetu.",
        "recommendation": "Daily balans je turbo3, a safe je turbo4.",
        "safeChoices": ["turbo4", "turbo3"],
        "advancedChoices": ["turbo2"],
        "defaultValue": "turbo3",
    },
    {
        "id": "ncmoe",
        "label": "ncmoe",
        "whatIsIt": "Broj ranih MoE slojeva cije expert tezine prebacujes na CPU.",
        "effect": "Visa vrednost stedi VRAM, ali usporava rad.",
        "recommendation": "Za 3060 12 GB daily kreni oko 20; max-context idi 30-35.",
        "safeChoices": ["20"],
        "advancedChoices": ["30", "35"],
        "defaultValue": 20,
    },
    {
        "id": "flashAttention",
        "label": "Flash attention",
        "whatIsIt": "Brzi attention put kada ga runtime podrzava.",
        "effect": "Najcesce povoljan za performanse i obicno ga vredi drzati ukljucenim.",
        "recommendation": "Drzi ukljuceno osim ako imas konkretan bug.",
        "safeChoices": ["on"],
        "advancedChoices": ["off"],
        "defaultValue": True,
    },
    {
        "id": "mlock",
        "label": "mlock",
        "whatIsIt": "Pokusava da drzi model u RAM-u umesto da ga OS lakse swapuje.",
        "effect": "Smanjuje swap/paging rizik, ali moze da bude stroziji prema memoriji.",
        "recommendation": "Uglavnom bezbedno za desktop masinu kada hoces stabilniji rad.",
        "safeChoices": ["on"],
        "advancedChoices": ["off"],
        "defaultValue": True,
    },
    {
        "id": "mmapMode",
        "label": "mmap mode",
        "whatIsIt": "Menja nacin ucitavanja modela sa diska u memoriju.",
        "effect": "mmap brze pali model; no-mmap ume da bude stabilniji kod cudnih pageout situacija.",
        "recommendation": "Za tvoj setup daily koristi no-mmap samo ako vec vidis mmap probleme.",
        "safeChoices": ["mmap"],
        "advancedChoices": ["no-mmap"],
        "defaultValue": "mmap",
    },
    {
        "id": "runtimePreference",
        "label": "Runtime preference",
        "whatIsIt": "Koji runtime zelis da forsiras kad su oba dostupna.",
        "effect": "TurboQuant jace stedi memoriju; llama.cpp je jednostavniji fallback.",
        "recommendation": "Ako je TurboQuant stabilan na masini, koristi turboquant kao prvi izbor.",
        "safeChoices": ["turboquant", "llama.cpp"],
        "advancedChoices": [],
        "defaultValue": "turboquant",
    },
]

TURBOQUANT_BUILTIN_PRESETS = [
    {
        "id": "safe",
        "name": "safe",
        "description": "Najbezbedniji preset za duzi rad i najmanji rizik po kvalitet.",
        "targetModelPattern": "qwen36-*",
        "notes": "Manje agresivna kompresija, oprezniji context i stabilniji izbori.",
        "settings": {
            "context": 131072,
            "ctk": "turbo4",
            "ctv": "turbo4",
            "ncmoe": 20,
            "flashAttention": True,
            "mlock": True,
            "mmapMode": "mmap",
            "runtimePreference": "turboquant",
        },
    },
    {
        "id": "daily",
        "name": "daily",
        "description": "Najbolji balans brzine, memorije i svakodnevnog rada na 3060 12 GB.",
        "targetModelPattern": "qwen36-*",
        "notes": "Preporuceni daily izbor za llama.cpp + TurboQuant.",
        "settings": {
            "context": 262144,
            "ctk": "turbo4",
            "ctv": "turbo3",
            "ncmoe": 20,
            "flashAttention": True,
            "mlock": True,
            "mmapMode": "mmap",
            "runtimePreference": "turboquant",
        },
    },
    {
        "id": "max-context",
        "name": "max-context",
        "description": "Agresivniji preset kada je najveci prioritet duzi context.",
        "targetModelPattern": "qwen36-*",
        "notes": "Jace stedi memoriju, ali je manje bezbedan od safe/daily pristupa.",
        "settings": {
            "context": 327680,
            "ctk": "turbo3",
            "ctv": "turbo3",
            "ncmoe": 35,
            "flashAttention": True,
            "mlock": True,
            "mmapMode": "no-mmap",
            "runtimePreference": "turboquant",
        },
    },
]

UNSLOTH_RECOMMENDED_MODELS = [
    {
        "id": "unsloth-Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
        "label": "Qwen3.6 35B A3B",
        "repo": "unsloth/Qwen3.6-35B-A3B-GGUF",
        "filename": "Qwen3.6-35B-A3B-UD-IQ2_M.gguf",
        "quantization": "UD-IQ2_M",
        "fitNote": "Realan daily izbor za 3060 12 GB uz TurboQuant.",
        "mtp": False,
    },
    {
        "id": "unsloth-Qwen3.6-35B-A3B-UD-IQ3_S.gguf",
        "label": "Qwen3.6 35B A3B",
        "repo": "unsloth/Qwen3.6-35B-A3B-GGUF",
        "filename": "Qwen3.6-35B-A3B-UD-IQ3_S.gguf",
        "quantization": "UD-IQ3_S",
        "fitNote": "Stretch izbor kada hoces bolji kvalitet, ali uz veci pritisak.",
        "mtp": False,
    },
    {
        "id": "unsloth-Qwen3.6-27B-UD-IQ3_XXS.gguf",
        "label": "Qwen3.6 27B",
        "repo": "unsloth/Qwen3.6-27B-GGUF",
        "filename": "Qwen3.6-27B-UD-IQ3_XXS.gguf",
        "quantization": "UD-IQ3_XXS",
        "fitNote": "Najzdraviji 27B balans za tvoj hardver.",
        "mtp": False,
    },
    {
        "id": "unsloth-Qwen3.6-27B-UD-Q2_K_XL.gguf",
        "label": "Qwen3.6 27B",
        "repo": "unsloth/Qwen3.6-27B-GGUF",
        "filename": "Qwen3.6-27B-UD-Q2_K_XL.gguf",
        "quantization": "UD-Q2_K_XL",
        "fitNote": "Stretch 27B izbor kad juris veci model po svaku cenu.",
        "mtp": False,
    },
]


def apply_thinking_mode(mode: str) -> dict[str, int | str]:
    return THINKING_PRESETS.get(mode, THINKING_PRESETS["mid"]).copy()


def load_settings_payload() -> dict[str, int | str | bool]:
    home = detect_local_qwen_home()
    settings = read_json_file(home / "state" / "settings.json")
    install_state = read_json_file(home / "state" / "install-state.json")
    profile = str(settings.get("profile", "balanced"))
    llama = settings.get("llama") or {}
    opencode = settings.get("opencode") or {}
    active_model_id = str(install_state.get("modelId", "") or "")
    active_model_label = _resolve_model_label(home, active_model_id)

    payload = _infer_thinking_payload(
        int(opencode.get("buildSteps", 80) or 80),
        int(opencode.get("planSteps", 60) or 60),
        int(opencode.get("generalSteps", 70) or 70),
        int(opencode.get("exploreSteps", 40) or 40),
    )
    payload.update(
        {
            "profile": profile,
            "context": int(llama.get("contextSize", 262144) or 262144),
            "outputTokens": int(llama.get("maxOutputTokens", 8192) or 8192),
            "workingDirectory": str(opencode.get("workingDirectory") or Path.home()),
            "settingsScope": "global",
            "activeModelId": active_model_id,
            "activeModelLabel": active_model_label,
            "modelOverrideExists": False,
            "accessMode": load_runtime_config(state_dir=PROJECT_STATE_DIR)["accessMode"],
        }
    )

    if active_model_id:
        override = load_model_override_payload(active_model_id, local_qwen_home=home)
        if override:
            payload.update(override)
            payload["settingsScope"] = "model"
            payload["modelOverrideExists"] = True
            payload["activeModelId"] = active_model_id
            payload["activeModelLabel"] = active_model_label
            return payload

    global_defaults = load_global_defaults_payload(local_qwen_home=home)
    if global_defaults:
        payload.update(global_defaults)
        payload["settingsScope"] = "global"
        payload["activeModelId"] = active_model_id
        payload["activeModelLabel"] = active_model_label

    return payload


def build_configure_settings_env(payload: dict[str, object]) -> dict[str, str]:
    thinking_mode = str(payload.get("thinkingMode", "mid") or "mid")
    thinking = apply_thinking_mode(thinking_mode)
    return {
        "PROFILE": str(payload.get("profile", "balanced") or "balanced"),
        "CONTEXT_SIZE": str(int(payload.get("context", 262144) or 262144)),
        "MAX_OUTPUT_TOKENS": str(int(payload.get("outputTokens", 8192) or 8192)),
        "WORKING_DIRECTORY": str(payload.get("workingDirectory", Path.home()) or Path.home()),
        "BUILD_STEPS": str(thinking["buildSteps"]),
        "PLAN_STEPS": str(thinking["planSteps"]),
        "GENERAL_STEPS": str(thinking["generalSteps"]),
        "EXPLORE_STEPS": str(thinking["exploreSteps"]),
    }


def apply_settings(payload: dict[str, object]) -> dict[str, object]:
    scope = str(payload.get("settingsScope", "global") or "global")
    home = detect_local_qwen_home()
    active_model_id = str(payload.get("activeModelId", "") or "")
    runtime_config = save_runtime_config(payload, state_dir=PROJECT_STATE_DIR)
    _remove_legacy_runtime_config()

    if scope == "model" and active_model_id:
        save_model_override_payload(
            {
                "modelId": active_model_id,
                "profile": str(payload.get("profile", "balanced") or "balanced"),
                "context": int(payload.get("context", 262144) or 262144),
                "outputTokens": int(payload.get("outputTokens", 8192) or 8192),
                "workingDirectory": str(payload.get("workingDirectory", Path.home()) or Path.home()),
                "thinkingMode": str(payload.get("thinkingMode", "mid") or "mid"),
            },
            local_qwen_home=home,
        )
    else:
        save_global_defaults_payload(
            {
                "profile": str(payload.get("profile", "balanced") or "balanced"),
                "context": int(payload.get("context", 262144) or 262144),
                "outputTokens": int(payload.get("outputTokens", 8192) or 8192),
                "workingDirectory": str(payload.get("workingDirectory", Path.home()) or Path.home()),
                "thinkingMode": str(payload.get("thinkingMode", "mid") or "mid"),
            },
            local_qwen_home=home,
        )

    env = build_configure_settings_env(payload)
    result = run_linux_launcher("configure-settings.sh", extra_env=env)
    if scope == "model" and active_model_id and result.get("status") == "ok":
        result["summary"] = f"Model override sacuvan za {active_model_id}"
    if result.get("status") == "ok":
        result["summary"] = f"{result.get('summary', '')} | Access mode: {runtime_config['accessMode']}".strip(" |")
    return result


def load_model_override_payload(
    model_id: str,
    *,
    local_qwen_home: Path | None = None,
) -> dict[str, int | str] | None:
    home = local_qwen_home or detect_local_qwen_home()
    registry = _read_model_override_registry(home)
    model_payload = registry.get("models", {}).get(model_id)
    if not isinstance(model_payload, dict):
        return None
    return {
        "modelId": model_id,
        "profile": str(model_payload.get("profile", "balanced") or "balanced"),
        "context": int(model_payload.get("context", 262144) or 262144),
        "outputTokens": int(model_payload.get("outputTokens", 8192) or 8192),
        "workingDirectory": str(model_payload.get("workingDirectory", Path.home()) or Path.home()),
        "thinkingMode": str(model_payload.get("thinkingMode", "mid") or "mid"),
        **apply_thinking_mode(str(model_payload.get("thinkingMode", "mid") or "mid")),
    }


def save_model_override_payload(
    payload: dict[str, object],
    *,
    local_qwen_home: Path | None = None,
) -> None:
    home = local_qwen_home or detect_local_qwen_home()
    model_id = str(payload.get("modelId", "") or "").strip()
    if not model_id:
        raise ValueError("modelId je obavezan za model override settings.")
    registry = _read_model_override_registry(home)
    models = registry.setdefault("models", {})
    models[model_id] = {
        "profile": str(payload.get("profile", "balanced") or "balanced"),
        "context": int(payload.get("context", 262144) or 262144),
        "outputTokens": int(payload.get("outputTokens", 8192) or 8192),
        "workingDirectory": str(payload.get("workingDirectory", Path.home()) or Path.home()),
        "thinkingMode": str(payload.get("thinkingMode", "mid") or "mid"),
    }
    _write_model_override_registry(home, registry)


def load_model_override_registry(local_qwen_home: Path | None = None) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    return _read_model_override_registry(home)


def load_global_defaults_payload(
    *,
    local_qwen_home: Path | None = None,
) -> dict[str, int | str] | None:
    home = local_qwen_home or detect_local_qwen_home()
    path = _global_defaults_path(home)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None
    return {
        "profile": str(payload.get("profile", "balanced") or "balanced"),
        "context": int(payload.get("context", 262144) or 262144),
        "outputTokens": int(payload.get("outputTokens", 8192) or 8192),
        "workingDirectory": str(payload.get("workingDirectory", Path.home()) or Path.home()),
        "thinkingMode": str(payload.get("thinkingMode", "mid") or "mid"),
        **apply_thinking_mode(str(payload.get("thinkingMode", "mid") or "mid")),
    }


def save_global_defaults_payload(
    payload: dict[str, object],
    *,
    local_qwen_home: Path | None = None,
) -> None:
    home = local_qwen_home or detect_local_qwen_home()
    path = _global_defaults_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "profile": str(payload.get("profile", "balanced") or "balanced"),
                "context": int(payload.get("context", 262144) or 262144),
                "outputTokens": int(payload.get("outputTokens", 8192) or 8192),
                "workingDirectory": str(payload.get("workingDirectory", Path.home()) or Path.home()),
                "thinkingMode": str(payload.get("thinkingMode", "mid") or "mid"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_turboquant_schema(
    *,
    local_qwen_home: Path | None = None,
) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    return {
        "parameters": TURBOQUANT_PARAMETERS,
        "builtInPresets": TURBOQUANT_BUILTIN_PRESETS,
        "userPresets": load_turboquant_user_presets(local_qwen_home=home),
        "currentConfig": load_turboquant_config(local_qwen_home=home),
        "recommendedModels": UNSLOTH_RECOMMENDED_MODELS,
    }


def load_turboquant_config(
    *,
    local_qwen_home: Path | None = None,
) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    path = _turboquant_config_path(home)
    baseline = dict(TURBOQUANT_BUILTIN_PRESETS[1]["settings"])
    if not path.exists():
        return baseline
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return baseline
    merged = dict(baseline)
    merged.update({key: payload.get(key, value) for key, value in baseline.items()})
    return merged


def save_turboquant_config(
    payload: dict[str, object],
    *,
    local_qwen_home: Path | None = None,
) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    normalized = _normalize_turboquant_settings(payload)
    path = _turboquant_config_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized


def load_turboquant_user_presets(
    *,
    local_qwen_home: Path | None = None,
) -> list[dict[str, object]]:
    home = local_qwen_home or detect_local_qwen_home()
    path = _turboquant_presets_path(home)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return []
    presets = payload.get("presets") or []
    if not isinstance(presets, list):
        return []
    return [item for item in presets if isinstance(item, dict)]


def save_turboquant_user_preset(
    payload: dict[str, object],
    *,
    local_qwen_home: Path | None = None,
) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    name = str(payload.get("name", "") or "").strip()
    if not name:
        raise ValueError("Ime preset-a je obavezno.")
    preset = {
        "id": _slugify_preset_name(name),
        "name": name,
        "description": str(payload.get("description", "") or "").strip(),
        "targetModelPattern": str(payload.get("targetModelPattern", "") or "").strip(),
        "notes": str(payload.get("notes", "") or "").strip(),
        "settings": _normalize_turboquant_settings(payload.get("settings", {})),
    }
    existing = load_turboquant_user_presets(local_qwen_home=home)
    filtered = [item for item in existing if str(item.get("id")) != preset["id"]]
    filtered.append(preset)
    _write_turboquant_presets(home, filtered)
    return preset


def delete_turboquant_user_preset(
    preset_id: str,
    *,
    local_qwen_home: Path | None = None,
) -> bool:
    home = local_qwen_home or detect_local_qwen_home()
    existing = load_turboquant_user_presets(local_qwen_home=home)
    filtered = [item for item in existing if str(item.get("id")) != str(preset_id)]
    if len(filtered) == len(existing):
        return False
    _write_turboquant_presets(home, filtered)
    return True


def _infer_thinking_payload(
    build_steps: int,
    plan_steps: int,
    general_steps: int,
    explore_steps: int,
) -> dict[str, int | str]:
    chosen_name = "mid"
    chosen_distance = None
    for name, preset in THINKING_PRESETS.items():
        distance = (
            abs(int(preset["buildSteps"]) - build_steps)
            + abs(int(preset["planSteps"]) - plan_steps)
            + abs(int(preset["generalSteps"]) - general_steps)
            + abs(int(preset["exploreSteps"]) - explore_steps)
        )
        if chosen_distance is None or distance < chosen_distance:
            chosen_name = name
            chosen_distance = distance
    payload = THINKING_PRESETS[chosen_name].copy()
    payload.update(
        {
            "buildSteps": build_steps,
            "planSteps": plan_steps,
            "generalSteps": general_steps,
            "exploreSteps": explore_steps,
        }
    )
    return payload


def _resolve_model_label(home: Path, model_id: str) -> str:
    if not model_id:
        return "Nema aktivnog modela"
    defaults = read_json_file(home / "config" / "profiles" / "defaults.json")
    for item in (defaults.get("modelChoices") or {}).values():
        if isinstance(item, dict) and (item.get("id") == model_id or item.get("filename") == model_id):
            return str(item.get("label", model_id) or model_id)
    custom = read_json_file(home / "state" / "custom-models.json")
    for item in custom.get("models") or []:
        if isinstance(item, dict) and item.get("id") == model_id:
            return str(item.get("label", model_id) or model_id)
    return model_id


def _model_override_path(home: Path) -> Path:
    return home / "state" / MODEL_OVERRIDE_FILE


def _read_model_override_registry(home: Path) -> dict[str, object]:
    path = _model_override_path(home)
    if not path.exists():
        return {"models": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {"models": {}}


def _write_model_override_registry(home: Path, payload: dict[str, object]) -> None:
    path = _model_override_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _global_defaults_path(home: Path) -> Path:
    return home / "state" / GLOBAL_DEFAULTS_FILE


def _remove_legacy_runtime_config() -> None:
    legacy = LEGACY_BACKEND_STATE_DIR / "runtime-config.json"
    if legacy.exists():
        with contextlib.suppress(OSError):
            legacy.unlink()


def _turboquant_config_path(home: Path) -> Path:
    return home / "state" / TURBOQUANT_CONFIG_FILE


def _turboquant_presets_path(home: Path) -> Path:
    return home / "state" / TURBOQUANT_PRESETS_FILE


def _write_turboquant_presets(home: Path, presets: list[dict[str, object]]) -> None:
    path = _turboquant_presets_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"presets": presets}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _slugify_preset_name(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not base:
        base = "preset"
    return f"user-{base}-{uuid4().hex[:6]}"


def _normalize_turboquant_settings(payload: object) -> dict[str, object]:
    raw = payload if isinstance(payload, dict) else {}
    return {
        "context": int(raw.get("context", 131072) or 131072),
        "ctk": str(raw.get("ctk", "turbo4") or "turbo4"),
        "ctv": str(raw.get("ctv", "turbo3") or "turbo3"),
        "ncmoe": int(raw.get("ncmoe", 20) or 20),
        "flashAttention": bool(raw.get("flashAttention", True)),
        "mlock": bool(raw.get("mlock", True)),
        "mmapMode": str(raw.get("mmapMode", "mmap") or "mmap"),
        "runtimePreference": str(raw.get("runtimePreference", "turboquant") or "turboquant"),
    }
