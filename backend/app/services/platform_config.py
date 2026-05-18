from __future__ import annotations

import os
import platform
import sys


TARGET_PLATFORM_ENV = "CONTROL_CENTER_NEXT_TARGET_PLATFORM"
TARGET_ARCHITECTURE_ENV = "CONTROL_CENTER_NEXT_TARGET_ARCHITECTURE"


def detect_host_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    return "linux"


def detect_host_architecture() -> str:
    machine = platform.machine().strip().lower()
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    if machine in {"x86_64", "amd64"}:
        return "x64"
    if machine in {"armv7l", "armv8l", "arm"}:
        return "arm"
    return machine or "unknown"


def get_target_platform() -> str:
    value = os.environ.get(TARGET_PLATFORM_ENV, "").strip().lower()
    if not value:
        return detect_host_platform()
    if value not in {"linux", "windows"}:
        return detect_host_platform()
    return value


def get_target_architecture() -> str:
    value = os.environ.get(TARGET_ARCHITECTURE_ENV, "").strip().lower()
    if not value:
        return detect_host_architecture()
    if value in {"aarch64", "arm64"}:
        return "arm64"
    if value in {"x86_64", "amd64", "x64"}:
        return "x64"
    if value in {"armv7l", "armv8l", "arm"}:
        return "arm"
    return value
