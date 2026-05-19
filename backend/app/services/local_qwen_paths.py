from __future__ import annotations

from pathlib import Path
import os

from backend.app.services.platform_config import get_target_platform

def detect_local_qwen_home() -> Path:
    override = os.environ.get("LOCAL_QWEN_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    if get_target_platform() == "windows":
        new_default = Path.home() / "LocalAIControlCenter"
        legacy_default = Path.home() / "LocalQwenHome"
        if new_default.exists():
            return new_default
        if legacy_default.exists():
            return legacy_default
        return new_default
    new_default = Path.home() / "local-ai-control-center"
    legacy_default = Path.home() / "local-qwen-home"
    if new_default.exists():
        return new_default
    if legacy_default.exists():
        return legacy_default
    return new_default


def detect_local_qwen_repo_fallback() -> Path:
    override = os.environ.get("LOCAL_QWEN_REPO_FALLBACK", "").strip()
    if override:
        return Path(override).expanduser()
    windows_default = Path(r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer")
    if windows_default.exists():
        return windows_default
    return detect_control_center_repo_root()


def detect_control_center_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
