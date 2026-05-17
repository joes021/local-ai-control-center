from __future__ import annotations

from backend.app.services.script_runner import run_linux_launcher


def load_logs_preview() -> dict[str, object]:
    return run_linux_launcher("show-logs.sh")
