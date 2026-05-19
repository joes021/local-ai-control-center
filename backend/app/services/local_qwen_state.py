from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.platform_config import get_target_architecture, get_target_platform


def load_local_qwen_summary(home: Path | None = None) -> dict[str, str]:
    home = home or detect_local_qwen_home()
    install_state = read_json_file(home / "state" / "install-state.json")
    settings = read_json_file(home / "state" / "settings.json")
    version = _read_version(home / "version.json")
    return {
        "version": version or "unknown",
        "health": "ok" if install_state else "unknown",
        "activeModel": str(install_state.get("modelId", "unknown")),
        "profile": str(
            settings.get("profile")
            or install_state.get("profile")
            or "unknown"
        ),
        "runtime": load_runtime_summary(home),
    }


def build_status_payload(
    summary: dict[str, str],
    ui_port: int,
    *,
    host: str = "127.0.0.1",
    access_mode: str = "local-only",
) -> dict[str, str | int | bool | list[str]]:
    host_platform = get_target_platform()
    host_platform_label = {
        "windows": "Windows",
        "linux": "Linux",
    }.get(host_platform, host_platform.capitalize())
    host_architecture = get_target_architecture()
    host_architecture_label = {
        "arm64": "ARM64",
        "x64": "x64",
        "arm": "ARM",
    }.get(host_architecture, host_architecture)
    runtime = summary.get("runtime") or {}
    active_runtime = str(runtime.get("active", "unknown"))
    llama_available = bool(runtime.get("llamaAvailable"))
    turbo_available = bool(runtime.get("turboAvailable"))
    turbo_status = str(runtime.get("turboStatus", "unknown"))
    turbo_reason = str(runtime.get("turboReason", "") or "")
    active_binary = str(runtime.get("activeBinary", "") or "")
    active_binary_source = str(runtime.get("activeBinarySource", "") or "")
    runtime_live_status = str(runtime.get("runtimeLiveStatus", "unknown"))
    runtime_live_reason = str(runtime.get("runtimeLiveReason", "") or "")
    local_url = f"http://127.0.0.1:{ui_port}"
    tailscale_url = ""
    tailscale_ip = detect_tailscale_ip()
    if access_mode == "tailscale" and tailscale_ip:
        tailscale_url = f"http://{tailscale_ip}:{ui_port}"
    available_runtimes = []
    if llama_available:
        available_runtimes.append("llama.cpp")
    if turbo_available:
        available_runtimes.append("TurboQuant")
    return {
        "hostPlatform": host_platform,
        "hostPlatformLabel": host_platform_label,
        "hostArchitecture": host_architecture,
        "hostArchitectureLabel": host_architecture_label,
        "hostShellLabel": f"{host_platform_label} Desktop GUI Shell",
        "version": summary.get("version", "unknown"),
        "health": summary.get("health", "unknown"),
        "activeModel": summary.get("activeModel", "unknown"),
        "profile": summary.get("profile", "unknown"),
        "uiPort": ui_port,
        "uiUrl": local_url,
        "localUrl": local_url,
        "tailscaleUrl": tailscale_url,
        "accessMode": access_mode,
        "bindHost": host,
        "runtimeStatus": active_runtime,
        "runtimeSummary": _build_runtime_summary(
            active_runtime,
            llama_available=llama_available,
            turbo_available=turbo_available,
        ),
        "activeRuntimeLabel": _runtime_label(active_runtime),
        "availableRuntimes": available_runtimes,
        "llamaRuntimeAvailable": llama_available,
        "turboQuantRuntimeAvailable": turbo_available,
        "llamaCppStatus": "spreman" if llama_available else "nije dostupan",
        "turboQuantStatus": turbo_status,
        "turboQuantReason": turbo_reason,
        "activeRuntimeBinary": active_binary,
        "activeRuntimeBinarySource": active_binary_source,
        "runtimeLiveStatus": runtime_live_status,
        "runtimeLiveReason": runtime_live_reason,
    }


def _read_version(path: Path) -> str | None:
    payload = read_json_file(path)
    return payload.get("version")


def load_runtime_summary(home: Path) -> dict[str, object]:
    install_state = read_json_file(home / "state" / "install-state.json")
    install_report = read_json_file(home / "state" / "install-report.json")
    lifecycle = read_json_file(home / "state" / "server-lifecycle.json")
    components = install_report.get("components") or {}

    active_exe = str(install_state.get("llamaServerExe", "") or "")
    turbo_exe = str(install_state.get("turboServerExe", "") or "")
    turbo_report_path = str(((components.get("turboQuantRuntime") or {}).get("path")) or "")
    if turbo_exe:
        turbo_available = Path(turbo_exe).is_file()
    else:
        turbo_available = bool(((components.get("turboQuantRuntime") or {}).get("ok")))
    llama_available = bool(active_exe and Path(active_exe).is_file())
    if not llama_available:
        fallback = home / "apps" / "llama.cpp" / "build" / "bin" / "llama-server"
        llama_available = fallback.is_file()
    if not llama_available:
        llama_available = bool(((components.get("llamaCppRuntime") or {}).get("ok")))

    effective_server = turbo_exe if turbo_exe and Path(turbo_exe).is_file() else active_exe
    process_binary = detect_running_runtime_binary(
        llama_path=active_exe,
        turbo_path=turbo_exe,
    )
    active_binary = process_binary or effective_server
    active_binary_source = "process" if process_binary else "config"
    normalized = active_binary.replace("\\", "/").lower()
    active_runtime = "unknown"
    if "turboquant" in normalized:
        active_runtime = "turboquant"
    elif "llama.cpp" in normalized:
        active_runtime = "llama.cpp"

    turbo_status = "nije dostupan"
    turbo_reason = "TurboQuant runtime nije pronadjen."
    if active_runtime == "turboquant":
        turbo_status = "aktivan"
        if active_binary_source == "process":
            turbo_reason = "TurboQuant je aktivan i potvrđen kroz pokrenuti proces."
        else:
            turbo_reason = "TurboQuant je aktivan po konfiguraciji i deluje startabilno."
    elif turbo_exe and Path(turbo_exe).is_file():
        turbo_status = "spreman"
        turbo_reason = "TurboQuant je konfigurisan u install-state i deluje startabilno."
    elif turbo_report_path and Path(turbo_report_path).is_file():
        turbo_status = "dostupan ali nije aktiviran"
        turbo_reason = (
            "TurboQuant binar postoji, ali install-state jos ne pokazuje na njega. "
            "Potrebno je dopuniti runtime konfiguraciju ili ponovo izgraditi runtime."
        )
    elif turbo_available:
        turbo_status = "delimicno detektovan"
        turbo_reason = "TurboQuant je prijavljen u install report-u, ali binar nije potvrdjen kroz install-state."

    runtime_live_status, runtime_live_reason = detect_runtime_liveness(
        active_runtime=active_runtime,
        active_binary=active_binary,
        active_binary_source=active_binary_source,
        port=int(install_state.get("port", 8091) or 8091),
        lifecycle_state=str(lifecycle.get("state", "") or ""),
        lifecycle_reason=str(lifecycle.get("reason", "") or ""),
    )

    return {
        "active": active_runtime,
        "llamaAvailable": llama_available,
        "turboAvailable": turbo_available,
        "turboStatus": turbo_status,
        "turboReason": turbo_reason,
        "activeBinary": active_binary,
        "activeBinarySource": active_binary_source,
        "runtimeLiveStatus": runtime_live_status,
        "runtimeLiveReason": runtime_live_reason,
    }


def read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _build_runtime_summary(
    active_runtime: str,
    *,
    llama_available: bool,
    turbo_available: bool,
) -> str:
    active_label = {
        "llama.cpp": "Aktivan: llama.cpp",
        "turboquant": "Aktivan: TurboQuant",
        "unknown": "Aktivan: nepoznato",
    }.get(active_runtime, f"Aktivan: {active_runtime}")
    available_bits = []
    if llama_available:
        available_bits.append("llama.cpp dostupan")
    if turbo_available:
        available_bits.append("TurboQuant dostupan")
    if not available_bits:
        available_bits.append("nema potvrde o dostupnom runtime-u")
    return f"{active_label} | " + " | ".join(available_bits)


def _runtime_label(runtime_name: str) -> str:
    return {
        "llama.cpp": "llama.cpp",
        "turboquant": "TurboQuant",
        "unknown": "nepoznato",
    }.get(runtime_name, runtime_name)


def detect_running_runtime_binary(*, llama_path: str, turbo_path: str) -> str:
    if get_target_platform() == "windows":
        return _detect_running_runtime_binary_windows(
            llama_path=llama_path,
            turbo_path=turbo_path,
        )

    try:
        completed = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    normalized_turbo = turbo_path.replace("\\", "/").lower()
    normalized_llama = llama_path.replace("\\", "/").lower()
    for line in completed.stdout.splitlines():
        current = line.strip()
        lowered = current.replace("\\", "/").lower()
        if "llama-server" not in lowered:
            continue
        if normalized_turbo and normalized_turbo in lowered:
            return turbo_path
        if normalized_llama and normalized_llama in lowered:
            return llama_path
    return ""


def _detect_running_runtime_binary_windows(*, llama_path: str, turbo_path: str) -> str:
    command = (
        "$ErrorActionPreference='SilentlyContinue'; "
        "Get-CimInstance Win32_Process -Filter \"Name = 'llama-server.exe'\" "
        "| Select-Object -ExpandProperty ExecutablePath"
    )
    try:
        completed = subprocess.run(
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
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""

    normalized_turbo = turbo_path.replace("\\", "/").lower()
    normalized_llama = llama_path.replace("\\", "/").lower()
    for line in completed.stdout.splitlines():
        current = line.strip()
        lowered = current.replace("\\", "/").lower()
        if not lowered:
            continue
        if normalized_turbo and normalized_turbo == lowered:
            return turbo_path
        if normalized_llama and normalized_llama == lowered:
            return llama_path
    return ""


def detect_runtime_liveness(
    *,
    active_runtime: str,
    active_binary: str,
    active_binary_source: str,
    port: int,
    lifecycle_state: str,
    lifecycle_reason: str,
) -> tuple[str, str]:
    if not active_binary:
        return ("nije potvrđen", "Nema aktivnog binara za proveru.")

    health_status, health_reason = probe_runtime_health(port)
    if health_status == "ok":
        return ("potvrđen kroz health", health_reason)
    if active_binary_source == "process":
        if health_status == "loading":
            return ("pokretanje u toku", health_reason)
        return ("potvrđen kroz proces", "Proces za aktivni runtime je pronađen.")
    if active_runtime == "unknown":
        return ("nije potvrđen", "Runtime nije uspešno identifikovan.")
    if health_status == "loading":
        return ("pokretanje u toku", health_reason)
    if lifecycle_state == "active":
        return (
            "nije potvrđen",
            "Sacuvani lifecycle je tvrdio da je server aktivan, ali nisu pronadjeni ni health endpoint ni llama-server proces.",
        )
    if lifecycle_state == "starting":
        return (
            "pokretanje u toku",
            lifecycle_reason or "Server je ostao u starting stanju bez health endpoint-a i bez llama-server procesa.",
        )
    if lifecycle_state in {"inactive", "failed"} and lifecycle_reason:
        return ("nije potvrđen", lifecycle_reason)
    return ("nije potvrđen", health_reason or "Runtime je izabran po konfiguraciji, ali nije potvrđen kroz proces ili health.")


def probe_runtime_health(port: int) -> tuple[str, str]:
    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib_request.urlopen(url, timeout=2) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 503 and "Loading model" in body:
            return ("loading", "Runtime odgovara, ali model se još učitava.")
        return ("error", f"Health endpoint vratio HTTP {exc.code}.")
    except Exception:
        return ("offline", "Health endpoint nije dostupan.")

    if "error" in body and "Loading model" in body:
        return ("loading", "Runtime odgovara, ali model se još učitava.")
    return ("ok", "Runtime health endpoint odgovara.")


def detect_tailscale_ip() -> str:
    try:
        completed = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return ""
