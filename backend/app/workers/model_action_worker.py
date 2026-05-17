from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action-id", required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--kwargs-json", required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from backend.app.services import models_service

    kwargs = json.loads(args.kwargs_json)
    if not isinstance(kwargs, dict):
        kwargs = {}

    try:
        models_service._run_model_action_worker(  # type: ignore[attr-defined]
            args.action_id,
            args.kind,
            {str(key): str(value) for key, value in kwargs.items()},
        )
    except Exception as exc:  # noqa: BLE001
        models_service.complete_model_action(  # type: ignore[attr-defined]
            args.action_id,
            {
                "status": "error",
                "action": args.kind,
                "summary": f"Model akcija nije uspela: {exc}",
                "details": {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": str(exc),
                },
            },
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
