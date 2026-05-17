from __future__ import annotations

import os
import sys


TARGET_PLATFORM_ENV = "CONTROL_CENTER_NEXT_TARGET_PLATFORM"


def detect_host_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    return "linux"


def get_target_platform() -> str:
    value = os.environ.get(TARGET_PLATFORM_ENV, "").strip().lower()
    if not value:
        return detect_host_platform()
    if value not in {"linux", "windows"}:
        return detect_host_platform()
    return value
