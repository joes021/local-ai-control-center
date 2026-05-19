from __future__ import annotations

import json
import subprocess
from pathlib import Path

from backend.app.services.local_qwen_paths import detect_local_qwen_home, detect_local_qwen_repo_fallback


def resolve_windows_common_script() -> Path:
    install_root = detect_local_qwen_home()
    installed_candidates = [install_root / "launchers" / "local-ai-control-center-common.ps1"]
    for installed in installed_candidates:
        if installed.is_file():
            return installed

    repo_root = detect_local_qwen_repo_fallback() / "launcher" / "windows"
    repo_candidates = [repo_root / "local-ai-control-center-common.ps1"]
    for candidate in repo_candidates:
        if candidate.is_file():
            return candidate
    return repo_candidates[0]


def resolve_windows_common_repo_script() -> Path:
    repo_root = detect_local_qwen_repo_fallback() / "launcher" / "windows"
    return repo_root / "local-ai-control-center-common.ps1"


def invoke_windows_common_json(function_name: str, *args: str) -> dict[str, object]:
    script_path = resolve_windows_common_script()
    if not script_path.is_file():
        return {
            "status": "error",
            "action": function_name,
            "summary": f"Windows common skripta nije pronadjena: {script_path}",
            "details": {"returncode": 1, "stdout": "", "stderr": f"Missing: {script_path}"},
        }

    completed = _run_windows_common(script_path, function_name, *args)
    stderr = completed.stderr.strip()
    repo_script = resolve_windows_common_repo_script()
    if (
        completed.returncode != 0
        and "is not recognized as the name of a cmdlet, function" in stderr
        and repo_script != script_path
        and repo_script.is_file()
    ):
        completed = _run_windows_common(repo_script, function_name, *args)

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        return {
            "status": "error",
            "action": function_name,
            "summary": (stderr or stdout or f"{function_name} nije uspeo").splitlines()[0],
            "details": {"returncode": completed.returncode, "stdout": stdout, "stderr": stderr},
        }
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        payload = {"value": stdout}
    return {
        "status": "ok",
        "action": function_name,
        "summary": f"{function_name} OK",
        "details": {"returncode": 0, "stdout": stdout, "stderr": stderr},
        "payload": payload,
    }


def _powershell_single_quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_windows_common(script_path: Path, function_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    ps_args = " ".join(_powershell_single_quoted(arg) for arg in args)
    invocation = f"& {function_name}" + (f" {ps_args}" if ps_args else "")
    command = (
        f"$ErrorActionPreference='Stop'; "
        f". '{script_path}'; "
        f"$result = {invocation}; "
        f"if ($result -is [string]) {{ $result }} else {{ $result | ConvertTo-Json -Depth 20 -Compress }}"
    )
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
