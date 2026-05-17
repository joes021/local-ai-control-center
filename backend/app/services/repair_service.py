from __future__ import annotations

from backend.app.services.script_runner import run_linux_launcher


def run_repair_install() -> dict[str, object]:
    return run_linux_launcher("repair-install.sh")


def run_repair_model() -> dict[str, object]:
    return run_linux_launcher("repair-model.sh")


def run_repair_runtime() -> dict[str, object]:
    return run_linux_launcher("repair-runtime.sh")


def run_repair_config() -> dict[str, object]:
    return run_linux_launcher("repair-config.sh")
