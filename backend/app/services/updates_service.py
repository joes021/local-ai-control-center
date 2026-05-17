from __future__ import annotations

from backend.app.services.script_runner import run_launcher_by_platform


def check_updates() -> dict[str, object]:
    return run_launcher_by_platform("check-updates.sh", "check-updates.ps1")


def install_update() -> dict[str, object]:
    return run_launcher_by_platform("install-update.sh", "install-update.ps1")
