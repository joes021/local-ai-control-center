from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.local_qwen_state import read_json_file
from backend.app.services.script_runner import run_linux_launcher


RUNTIME_CHOICE_FILE = "control-center-next-runtime-choice.json"


def select_runtime(runtime_name: str, *, local_qwen_home: Path | None = None) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    state_path = home / "state" / "install-state.json"
    report_path = home / "state" / "install-report.json"
    install_state = read_json_file(state_path)
    install_report = read_json_file(report_path)

    if not install_state:
        return _result("error", "select-runtime", "Install state nije pronadjen.")

    normalized = str(runtime_name or "").strip().lower()
    if normalized not in {"llama.cpp", "turboquant"}:
        return _result("error", "select-runtime", f"Nepoznat runtime: {runtime_name}")

    llama_path = str(install_state.get("llamaServerExe", "") or "")
    turbo_path = _resolve_turbo_path(home, install_state, install_report)
    runtime_choice = _read_runtime_choice(home)

    if normalized == "llama.cpp":
        current_turbo = str(install_state.get("turboServerExe", "") or "")
        if current_turbo:
            runtime_choice["lastTurboServerExe"] = current_turbo
        install_state["turboServerExe"] = ""
        install_state["selectedRuntime"] = "llama.cpp"
    else:
        if not turbo_path or not Path(turbo_path).is_file():
            return _result(
                "error",
                "select-runtime",
                "TurboQuant ne moze da se aktivira jer binar nije pronadjen ili nije startabilan.",
            )
        install_state["turboServerExe"] = turbo_path
        install_state["selectedRuntime"] = "turboquant"
        runtime_choice["lastTurboServerExe"] = turbo_path

    if llama_path:
        install_state["llamaServerExe"] = llama_path

    state_path.write_text(json.dumps(install_state, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_runtime_choice(home, runtime_choice)

    stop_result = run_linux_launcher("stop-server.sh")
    profile = str(install_state.get("profile", "balanced") or "balanced")
    start_result = run_linux_launcher("start-server.sh", profile)
    if start_result.get("status") != "ok":
        return start_result

    chosen_label = "TurboQuant" if normalized == "turboquant" else "llama.cpp"
    details_stdout = "\n".join(
        filter(
            None,
            [
                str((stop_result.get("details") or {}).get("stdout", "")),
                str((start_result.get("details") or {}).get("stdout", "")),
            ],
        )
    ).strip()
    return {
        "status": "ok",
        "action": "select-runtime",
        "summary": f"Aktiviran runtime: {chosen_label}",
        "details": {
            "returncode": 0,
            "stdout": details_stdout,
            "stderr": "",
        },
    }


def _resolve_turbo_path(home: Path, install_state: dict, install_report: dict) -> str:
    turbo_path = str(install_state.get("turboServerExe", "") or "")
    if turbo_path and Path(turbo_path).is_file():
        return turbo_path

    runtime_choice = _read_runtime_choice(home)
    turbo_path = str(runtime_choice.get("lastTurboServerExe", "") or "")
    if turbo_path and Path(turbo_path).is_file():
        return turbo_path

    components = install_report.get("components") or {}
    turbo_path = str(((components.get("turboQuantRuntime") or {}).get("path")) or "")
    if turbo_path and Path(turbo_path).is_file():
        return turbo_path
    return ""


def _runtime_choice_path(home: Path) -> Path:
    return home / "state" / RUNTIME_CHOICE_FILE


def _read_runtime_choice(home: Path) -> dict[str, object]:
    path = _runtime_choice_path(home)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _write_runtime_choice(home: Path, payload: dict[str, object]) -> None:
    path = _runtime_choice_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _result(status: str, action: str, summary: str) -> dict[str, object]:
    return {
        "status": status,
        "action": action,
        "summary": summary,
        "details": {
            "returncode": 1 if status != "ok" else 0,
            "stdout": "",
            "stderr": "" if status == "ok" else summary,
        },
    }
