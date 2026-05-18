from __future__ import annotations

import subprocess
from pathlib import Path

from backend.app.config import get_config
from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.local_qwen_state import (
    detect_tailscale_ip,
    load_local_qwen_summary,
    probe_runtime_health,
    read_json_file,
)
from backend.app.services.platform_config import get_target_platform
from backend.app.services.script_runner import (
    run_launcher_by_platform,
    run_linux_launcher,
    run_windows_launcher,
)


def load_server_status(*, local_qwen_home: Path | None = None) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    summary = load_local_qwen_summary(home)
    install_state = read_json_file(home / "state" / "install-state.json")
    lifecycle = read_json_file(home / "state" / "server-lifecycle.json")
    runtime = summary.get("runtime") or {}

    port = int(install_state.get("port", 8091) or 8091)
    health_status, health_reason = probe_runtime_health(port)
    lifecycle_state = str(lifecycle.get("state", "") or "unknown")
    status = _effective_server_status(lifecycle_state, health_status)
    health = _normalize_health(health_status)
    local_web_url = f"http://127.0.0.1:{port}/"
    health_url = f"http://127.0.0.1:{port}/health"
    pid = detect_server_pid(port)

    payload: dict[str, object] = {
        "status": status,
        "lifecycleState": lifecycle_state,
        "port": port,
        "health": health,
        "healthReason": health_reason,
        "pid": pid,
        "profile": summary.get("profile", "unknown"),
        "activeModel": summary.get("activeModel", "unknown"),
        "activeRuntime": runtime.get("active", "unknown"),
        "activeRuntimeLabel": _runtime_label(str(runtime.get("active", "unknown"))),
        "runtimeLiveStatus": runtime.get("runtimeLiveStatus", "unknown"),
        "runtimeLiveReason": runtime.get("runtimeLiveReason", ""),
        "lastReason": str(lifecycle.get("reason", "") or health_reason),
        "updatedAt": str(lifecycle.get("updatedAt", "") or ""),
        "healthUrl": health_url,
        "webUrl": local_web_url,
        "localWebUrl": local_web_url,
    }
    payload.update(_build_warning_summary(status=status, health=health, health_reason=health_reason, lifecycle_reason=payload["lastReason"], pid=pid))

    config = get_config()
    if config.access_mode == "tailscale":
        tailscale_ip = detect_tailscale_ip()
        payload["tailscaleWebUrl"] = (
            f"http://{tailscale_ip}:{port}/" if tailscale_ip else ""
        )
    else:
        payload["tailscaleWebUrl"] = ""

    return payload


def start_server(*, local_qwen_home: Path | None = None) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    settings = read_json_file(home / "state" / "settings.json")
    install_state = read_json_file(home / "state" / "install-state.json")
    profile = str(settings.get("profile") or install_state.get("profile") or "balanced")

    if get_target_platform() == "windows":
        return run_windows_launcher(
            "start-server.ps1",
            "-Profile",
            profile,
            "-WaitSeconds",
            "90",
        )
    return run_linux_launcher("start-server.sh", profile)


def stop_server() -> dict[str, object]:
    return run_launcher_by_platform("stop-server.sh", "stop-server.ps1")


def open_server_web(*, local_qwen_home: Path | None = None) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    install_state = read_json_file(home / "state" / "install-state.json")
    port = int(install_state.get("port", 8091) or 8091)
    url = f"http://127.0.0.1:{port}/"

    if get_target_platform() != "windows":
        opener = _detect_linux_url_opener()
        if not opener:
            return {
                "status": "error",
                "action": "open-server-web",
                "summary": "Nije pronadjen Linux URL opener (xdg-open / gio / sensible-browser).",
                "details": {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": "Nije pronadjen Linux URL opener (xdg-open / gio / sensible-browser).",
                    "url": url,
                },
            }
        completed = subprocess.run(
            [*opener, url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        status = "ok" if completed.returncode == 0 else "error"
        summary = (
            f"Otvoren llama.cpp web: {url}"
            if completed.returncode == 0
            else (
                completed.stderr.strip()
                or completed.stdout.strip()
                or "Otvaranje llama.cpp web-a nije uspelo."
            )
        )
        return {
            "status": status,
            "action": "open-server-web",
            "summary": summary,
            "details": {
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "url": url,
            },
        }

    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"Start-Process '{url}'",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    status = "ok" if completed.returncode == 0 else "error"
    summary = (
        f"Otvoren llama.cpp web: {url}"
        if completed.returncode == 0
        else (
            completed.stderr.strip()
            or completed.stdout.strip()
            or "Otvaranje llama.cpp web-a nije uspelo."
        )
    )
    return {
        "status": status,
        "action": "open-server-web",
        "summary": summary,
        "details": {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "url": url,
        },
    }


def _detect_linux_url_opener() -> list[str]:
    for candidate in (["xdg-open"], ["gio", "open"], ["sensible-browser"]):
        try:
            completed = subprocess.run(
                [candidate[0], "--help"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError:
            continue
        if completed.returncode in {0, 1}:
            return candidate
    return []


def detect_server_pid(port: int) -> int | None:
    if get_target_platform() == "windows":
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                (
                    "$target='--port "
                    + str(port)
                    + "'; "
                    "(Get-CimInstance Win32_Process -Filter \"Name = 'llama-server.exe'\") "
                    + "| Where-Object { $_.CommandLine -like ('*' + $target + '*') } "
                    + "| Select-Object -First 1 -ExpandProperty ProcessId"
                ),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            return None
        text = completed.stdout.strip()
        return int(text) if text.isdigit() else None

    completed = subprocess.run(
        ["ps", "-eo", "pid,args"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        return None
    port_token = f"--port {port}"
    for line in completed.stdout.splitlines():
        candidate = line.strip()
        if "llama-server" not in candidate or port_token not in candidate:
            continue
        parts = candidate.split(None, 1)
        if parts and parts[0].isdigit():
            return int(parts[0])
    return None


def _effective_server_status(lifecycle_state: str, health_status: str) -> str:
    if health_status == "ok":
        return "active"
    if health_status == "loading":
        return "starting"
    if lifecycle_state in {"active", "starting", "inactive", "timeout", "failed"}:
        return lifecycle_state
    return "unknown"


def _normalize_health(health_status: str) -> str:
    if health_status == "ok":
        return "ok"
    if health_status == "loading":
        return "loading"
    return "offline"


def _runtime_label(runtime_name: str) -> str:
    return {
        "llama.cpp": "llama.cpp",
        "turboquant": "TurboQuant",
        "unknown": "nepoznato",
    }.get(runtime_name, runtime_name)


def _build_warning_summary(
    *,
    status: str,
    health: str,
    health_reason: str,
    lifecycle_reason: object,
    pid: int | None,
) -> dict[str, object]:
    lifecycle_text = str(lifecycle_reason or "").strip()
    health_text = str(health_reason or "").strip()

    if status in {"failed", "timeout"}:
        return {
            "hasWarning": True,
            "warningSeverity": "error",
            "warningSummary": lifecycle_text or health_text or "Server nije uspesno podignut.",
        }

    if health != "ok":
        base = health_text or lifecycle_text or "Server health nije potvrdjen."
        if status == "active" and pid is None:
            if health_text:
                base = health_text
            else:
                base = lifecycle_text or "Lifecycle tvrdi da je server aktivan, ali proces nije pronadjen."
        return {
            "hasWarning": True,
            "warningSeverity": "warning",
            "warningSummary": base,
        }

    return {
        "hasWarning": False,
        "warningSeverity": "",
        "warningSummary": "",
    }
