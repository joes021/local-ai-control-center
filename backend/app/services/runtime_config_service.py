from __future__ import annotations

import json
from pathlib import Path


RUNTIME_CONFIG_FILE = "runtime-config.json"


def load_runtime_config(*, state_dir: Path) -> dict[str, str]:
    path = state_dir / RUNTIME_CONFIG_FILE
    if not path.exists():
        return {"accessMode": "local-only"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {"accessMode": "local-only"}
    access_mode = str(payload.get("accessMode", "local-only") or "local-only")
    if access_mode not in {"local-only", "tailscale"}:
        access_mode = "local-only"
    return {"accessMode": access_mode}


def save_runtime_config(payload: dict[str, object], *, state_dir: Path) -> dict[str, str]:
    state_dir.mkdir(parents=True, exist_ok=True)
    access_mode = str(payload.get("accessMode", "local-only") or "local-only")
    if access_mode not in {"local-only", "tailscale"}:
        access_mode = "local-only"
    config = {"accessMode": access_mode}
    (state_dir / RUNTIME_CONFIG_FILE).write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config
