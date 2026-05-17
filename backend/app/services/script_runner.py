from __future__ import annotations

import os
import subprocess
from pathlib import Path

from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.platform_config import get_target_platform


def get_linux_launcher_dir() -> Path:
    local_home = detect_local_qwen_home()
    installed = local_home / "launchers"
    fallback = Path(
        r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux"
    )
    if installed.is_dir():
        return installed
    return fallback


def get_windows_launcher_dir() -> Path:
    local_home = detect_local_qwen_home()
    installed = local_home / "launchers"
    fallback = Path(
        r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows"
    )
    if installed.is_dir():
        return installed
    return fallback


def resolve_linux_launcher_path(script_name: str) -> Path:
    installed = detect_local_qwen_home() / "launchers" / script_name
    if installed.is_file():
        return installed
    return Path(
        r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\linux"
    ) / script_name


def resolve_windows_launcher_path(script_name: str) -> Path:
    installed = detect_local_qwen_home() / "launchers" / script_name
    if installed.is_file():
        return installed
    return Path(
        r"C:\Users\AzdahaI9\Documents\Local Qwen 3.635Ba3B on home computer\launcher\windows"
    ) / script_name


def run_linux_launcher(
    script_name: str,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> dict[str, object]:
    script_path = resolve_linux_launcher_path(script_name)
    if not script_path.is_file():
        return build_result_payload(
            returncode=1,
            stdout="",
            stderr=f"Skripta nije pronadjena: {script_path}",
            action=script_name,
        )

    env = None
    if extra_env:
        env = dict(**extra_env)
        merged = dict(**__import__("os").environ)
        merged.update(env)
        env = merged

    completed = subprocess.run(
        ["bash", _to_bash_path(script_path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )
    return build_result_payload(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        action=script_name,
    )


def run_windows_launcher(
    script_name: str,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> dict[str, object]:
    script_path = resolve_windows_launcher_path(script_name)
    if not script_path.is_file():
        return build_result_payload(
            returncode=1,
            stdout="",
            stderr=f"Skripta nije pronadjena: {script_path}",
            action=script_name,
        )

    env = None
    if extra_env:
        merged = dict(os.environ)
        merged.update(extra_env)
        env = merged

    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )
    return build_result_payload(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        action=script_name,
    )


def run_launcher_by_platform(
    linux_script_name: str,
    windows_script_name: str,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> dict[str, object]:
    if get_target_platform() == "windows":
        return run_windows_launcher(windows_script_name, *args, extra_env=extra_env)
    return run_linux_launcher(linux_script_name, *args, extra_env=extra_env)


def build_result_payload(
    *,
    returncode: int,
    stdout: str,
    stderr: str,
    action: str,
) -> dict[str, object]:
    status = "ok" if returncode == 0 else "error"
    summary_source = stdout or stderr or "Komanda nije vratila izlaz."
    summary = summary_source.splitlines()[0]
    return {
        "status": status,
        "action": action,
        "summary": summary,
        "details": {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        },
    }


def _to_bash_path(path: Path) -> str:
    text = path.as_posix()
    if os.name != "nt":
        return text
    drive = path.drive.rstrip(":")
    if drive:
        return f"/{drive.lower()}{text[len(path.drive):]}"
    return text
