from __future__ import annotations

from pathlib import Path
import os

from backend.app.services.platform_config import get_target_platform

def detect_local_qwen_home() -> Path:
    override = os.environ.get("LOCAL_QWEN_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    if get_target_platform() == "windows":
        return Path.home() / "LocalQwenHome"
    return Path.home() / "local-qwen-home"


def detect_local_qwen_repo_fallback() -> Path:
    return Path(r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer")
