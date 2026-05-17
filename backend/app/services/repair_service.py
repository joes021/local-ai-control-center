from __future__ import annotations

from backend.app.services.script_runner import run_launcher_by_platform


def run_repair_install() -> dict[str, object]:
    return run_launcher_by_platform("repair-install.sh", "repair-install.ps1")


def run_repair_model() -> dict[str, object]:
    return run_launcher_by_platform("repair-model.sh", "repair-model.ps1")


def run_repair_runtime() -> dict[str, object]:
    return run_launcher_by_platform("repair-runtime.sh", "repair-runtime.ps1")


def run_repair_config() -> dict[str, object]:
    return run_launcher_by_platform("repair-config.sh", "repair-config.ps1")
