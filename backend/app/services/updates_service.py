from __future__ import annotations

from backend.app.services.script_runner import run_linux_launcher


def check_updates() -> dict[str, object]:
    return run_linux_launcher("check-updates.sh")


def install_update() -> dict[str, object]:
    return run_linux_launcher("install-update.sh")
