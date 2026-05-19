from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


def _write_error_progress(model_id: str, message: str) -> None:
    from backend.app.services.local_qwen_paths import detect_local_qwen_home

    progress_path = detect_local_qwen_home() / "state" / "model-download-progress.json"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "error",
        "modelId": model_id,
        "fileName": "",
        "source": "",
        "percent": None,
        "downloadedGiB": None,
        "totalGiB": None,
        "speedMBps": None,
        "etaSeconds": None,
        "message": message,
        "updatedAt": time.time(),
    }
    progress_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    os.environ.setdefault("CONTROL_CENTER_NEXT_TARGET_PLATFORM", "windows")

    from backend.app.services import models_service

    try:
        models_service._run_windows_download_worker(args.model_id)  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001
        _write_error_progress(args.model_id, str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
