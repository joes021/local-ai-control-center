from __future__ import annotations

import os


TARGET_PLATFORM_ENV = "CONTROL_CENTER_NEXT_TARGET_PLATFORM"


def get_target_platform() -> str:
    value = os.environ.get(TARGET_PLATFORM_ENV, "linux").strip().lower()
    if value not in {"linux", "windows"}:
        return "linux"
    return value
