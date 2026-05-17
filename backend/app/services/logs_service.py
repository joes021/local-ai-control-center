from __future__ import annotations

from backend.app.services.script_runner import run_launcher_by_platform


def load_logs_preview() -> dict[str, object]:
    return run_launcher_by_platform("show-logs.sh", "show-logs.ps1")
