from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from backend.app.services.local_qwen_paths import detect_local_qwen_home
from backend.app.services.platform_config import get_target_platform
from backend.app.services.script_runner import (
    build_result_payload,
    resolve_linux_launcher_path,
    resolve_windows_launcher_path,
)

_UPDATE_LOCK = threading.Lock()


def check_updates() -> dict[str, object]:
    info = load_update_release_info()
    current_version = str(info.get("currentVersion") or "unknown")
    latest_version = str(info.get("latestVersion") or "unknown")
    release_url = str(info.get("releaseUrl") or "")

    if info.get("aheadOfPublicRelease"):
        stdout = (
            f"Lokalna instalacija je novija od javnog latest release-a: "
            f"v{current_version} > v{latest_version}"
        )
    elif info.get("updateAvailable"):
        stdout = f"Dostupna je novija verzija: v{latest_version}"
    else:
        stdout = f"Instalacija je vec na latest verziji: v{current_version}"

    if release_url:
        stdout = f"{stdout}\nRelease URL: {release_url}"

    return build_result_payload(
        returncode=0,
        stdout=stdout,
        stderr="",
        action="check-updates",
    )


def read_update_progress(local_qwen_home: Path | None = None) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    progress_path = _progress_path(home)
    if not progress_path.is_file():
        try:
            info = load_update_release_info()
            return _default_progress_payload(
                currentVersion=str(info.get("currentVersion") or ""),
                latestVersion=str(info.get("latestVersion") or ""),
                releaseUrl=str(info.get("releaseUrl") or ""),
                message="Nema aktivnog update toka.",
            )
        except Exception:  # noqa: BLE001
            return _default_progress_payload()

    try:
        payload = json.loads(progress_path.read_text(encoding="utf-8-sig"))
        return _normalize_progress_payload(payload, home)
    except (OSError, json.JSONDecodeError):
        return _default_progress_payload(
            status="error",
            isActive=False,
            message="Update progress fajl nije mogao da se procita.",
        )


def start_install_update_job(local_qwen_home: Path | None = None) -> dict[str, object]:
    home = local_qwen_home or detect_local_qwen_home()
    info = load_update_release_info()

    if info.get("aheadOfPublicRelease"):
        return build_result_payload(
            returncode=0,
            stdout=(
                f"Lokalna instalacija je novija od javnog latest release-a: "
                f"v{info.get('currentVersion', 'unknown')} > v{info.get('latestVersion', 'unknown')}"
            ),
            stderr="",
            action="install-update",
        )

    if not info.get("updateAvailable"):
        return build_result_payload(
            returncode=0,
            stdout=(
                f"Instalacija je vec na latest verziji: "
                f"v{info.get('currentVersion', 'unknown')}"
            ),
            stderr="",
            action="install-update",
        )

    current = read_update_progress(home)
    if current.get("isActive"):
        return {
            "status": "accepted",
            "action": "install-update",
            "actionId": str(current.get("actionId") or "update-job-active"),
            "summary": str(current.get("message") or "Update je vec u toku."),
            "details": {
                "returncode": 0,
                "stdout": json.dumps(current, ensure_ascii=False),
                "stderr": "",
            },
        }

    action_id = f"update-{uuid.uuid4().hex[:12]}"
    progress = _build_progress_payload(
        action_id=action_id,
        status="accepted",
        is_active=True,
        current_version=str(info.get("currentVersion") or "unknown"),
        latest_version=str(info.get("latestVersion") or "unknown"),
        release_url=str(info.get("releaseUrl") or ""),
        message=(
            "Update je pokrenut. Posle preuzimanja installer ce se automatski pokrenuti."
        ),
        phase="queued",
    )
    _write_progress(home, progress)

    _spawn_install_update_job(home, info, action_id)

    return {
        "status": "accepted",
        "action": "install-update",
        "actionId": action_id,
        "summary": progress.get(
            "message",
            "Update je pokrenut u pozadini.",
        ),
        "details": {
            "returncode": 0,
            "stdout": json.dumps(progress, ensure_ascii=False),
            "stderr": "",
        },
    }


def load_update_release_info() -> dict[str, Any]:
    try:
        if get_target_platform() == "windows":
            script_path = resolve_windows_launcher_path("check-updates.ps1")
            command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-Json",
            ]
        else:
            script_path = resolve_linux_launcher_path("check-updates.sh")
            command = ["bash", str(script_path), "--json"]

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip()
                or completed.stdout.strip()
                or "Check updates nije uspeo."
            )

        return json.loads(completed.stdout.strip())
    except Exception:
        return _load_release_info_fallback()


def _spawn_install_update_job(home: Path, info: dict[str, Any], action_id: str) -> str:
    with _UPDATE_LOCK:
        worker = threading.Thread(
            target=_run_install_update_job,
            args=(home, info, action_id),
            daemon=True,
        )
        worker.start()
        return action_id


def _run_install_update_job(home: Path, info: dict[str, Any], action_id: str) -> None:
    platform_name = get_target_platform()
    current_version = str(info.get("currentVersion") or "unknown")
    latest_version = str(info.get("latestVersion") or "unknown")
    release_url = str(info.get("releaseUrl") or "")
    target_path = _resolve_target_path(home, latest_version, platform_name)
    try:
        download_url = _resolve_download_url(info, platform_name)

        _write_progress(
            home,
            _build_progress_payload(
                action_id=action_id,
                status="downloading",
                is_active=True,
                current_version=current_version,
                latest_version=latest_version,
                release_url=release_url,
                target_path=str(target_path),
                message=f"Preuzimam update installer u: {target_path}",
                phase="download",
            ),
        )

        _download_with_progress(download_url, target_path, home, action_id, current_version, latest_version, release_url)

        _write_progress(
            home,
            _build_progress_payload(
                action_id=action_id,
                status="launching-installer",
                is_active=True,
                current_version=current_version,
                latest_version=latest_version,
                release_url=release_url,
                target_path=str(target_path),
                percent=100.0,
                downloaded_gib=_file_size_gib(target_path),
                total_gib=_file_size_gib(target_path),
                message="Pokretanje installera...",
                phase="launch",
            ),
        )

        _launch_installer(platform_name, target_path, home)

        _write_progress(
            home,
            _build_progress_payload(
                action_id=action_id,
                status="completed",
                is_active=False,
                current_version=current_version,
                latest_version=latest_version,
                release_url=release_url,
                target_path=str(target_path),
                percent=100.0,
                downloaded_gib=_file_size_gib(target_path),
                total_gib=_file_size_gib(target_path),
                message="Installer je pokrenut. Update treba da nastavi automatski.",
                phase="completed",
            ),
        )
    except Exception as exc:  # noqa: BLE001
        _write_progress(
            home,
            _build_progress_payload(
                action_id=action_id,
                status="error",
                is_active=False,
                current_version=current_version,
                latest_version=latest_version,
                release_url=release_url,
                target_path=str(target_path),
                message=_build_update_error_message(exc, target_path),
                phase="error",
            ),
        )


def _download_with_progress(
    download_url: str,
    target_path: Path,
    home: Path,
    action_id: str,
    current_version: str,
    latest_version: str,
    release_url: str,
) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()

    request = Request(
        download_url,
        headers={
            "User-Agent": "LocalQwen-ControlCenterNext/1.0",
            "Accept": "*/*",
        },
    )

    with urlopen(request, timeout=60) as response, target_path.open("wb") as handle:
        total_bytes = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        started_at = time.time()
        last_tick = started_at
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            handle.write(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_tick >= 0.25 or (total_bytes and downloaded >= total_bytes):
                elapsed = max(now - started_at, 0.001)
                speed_mbps = downloaded / elapsed / (1024 * 1024)
                remaining = max(total_bytes - downloaded, 0)
                eta_seconds = int(remaining / max(downloaded / elapsed, 1)) if total_bytes else None
                percent = (downloaded / total_bytes * 100.0) if total_bytes else None
                _write_progress(
                    home,
                    _build_progress_payload(
                        action_id=action_id,
                        status="downloading",
                        is_active=True,
                        current_version=current_version,
                        latest_version=latest_version,
                        release_url=release_url,
                        target_path=str(target_path),
                        percent=percent,
                        downloaded_gib=_bytes_to_gib(downloaded),
                        total_gib=_bytes_to_gib(total_bytes) if total_bytes else None,
                        speed_mbps=speed_mbps,
                        eta_seconds=eta_seconds,
                        message=f"Preuzimam installer u: {target_path}",
                        phase="download",
                    ),
                )
                last_tick = now


def _launch_installer(platform_name: str, target_path: Path, home: Path) -> None:
    if platform_name == "windows":
        subprocess.Popen(  # noqa: S603
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"Start-Process -FilePath '{target_path}'"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    os.chmod(target_path, 0o755)
    env = dict(os.environ)
    env["INSTALL_ROOT"] = str(home)
    env["SKIP_MODEL_DOWNLOAD"] = "1"
    env["SKIP_RUNTIME_BUILD"] = "1"
    env["LOCAL_QWEN_SKIP_PACKAGE_INSTALL"] = "1"
    env["LOCAL_QWEN_SKIP_SOURCE_CLONE"] = "1"
    env["LOCAL_QWEN_SKIP_OPENCODE_INSTALL"] = "1"
    subprocess.Popen(  # noqa: S603
        [str(target_path), "--cli-install"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


def _resolve_download_url(info: dict[str, Any], platform_name: str) -> str:
    if platform_name == "windows":
        url = str(info.get("windowsInstallerUrl") or "").strip()
    else:
        url = str(info.get("linuxInstallerUrl") or "").strip()
    if not url:
        raise RuntimeError("Nije pronadjen installer URL za update.")
    return url


def _resolve_target_path(home: Path, latest_version: str, platform_name: str) -> Path:
    if platform_name == "windows":
        target_dir = Path(os.environ.get("TEMP", str(Path.home() / "AppData" / "Local" / "Temp"))) / "LocalQwenUpdate"
        safe_version = latest_version or "latest"
        return target_dir / f"Local-Qwen-Setup-{safe_version}.exe"
    target_dir = Path.home() / "Downloads"
    return target_dir / f"Local-Qwen-Setup-{latest_version}.run"


def _progress_path(home: Path) -> Path:
    return home / "state" / "update-progress.json"


def _write_progress(home: Path, payload: dict[str, Any]) -> None:
    path = _progress_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _default_progress_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "actionId": "",
        "status": "idle",
        "phase": "idle",
        "isActive": False,
        "currentVersion": "",
        "latestVersion": "",
        "releaseUrl": "",
        "targetPath": "",
        "percent": None,
        "downloadedGiB": None,
        "totalGiB": None,
        "speedMBps": None,
        "etaSeconds": None,
        "message": "Nema aktivnog update toka.",
        "updatedAt": _now_iso(),
    }
    payload.update(overrides)
    return payload


def _normalize_progress_payload(payload: dict[str, Any], home: Path) -> dict[str, Any]:
    normalized = _default_progress_payload(**payload)
    if (
        not normalized.get("currentVersion")
        or not normalized.get("latestVersion")
        or not normalized.get("releaseUrl")
    ):
        try:
            info = load_update_release_info()
            normalized["currentVersion"] = normalized.get("currentVersion") or str(
                info.get("currentVersion") or ""
            )
            normalized["latestVersion"] = normalized.get("latestVersion") or str(
                info.get("latestVersion") or ""
            )
            normalized["releaseUrl"] = normalized.get("releaseUrl") or str(
                info.get("releaseUrl") or ""
            )
        except Exception:
            pass

    if normalized.get("status") == "error":
        raw_message = str(normalized.get("message") or "")
        target_path = str(normalized.get("targetPath") or "")
        if not target_path:
            guessed = _extract_path_from_message(raw_message)
            if guessed:
                target_path = guessed
                normalized["targetPath"] = guessed
        if target_path:
            normalized["message"] = _build_update_error_message(
                RuntimeError(raw_message),
                Path(target_path),
            )
    return normalized


def _build_progress_payload(
    *,
    action_id: str,
    status: str,
    is_active: bool,
    message: str,
    phase: str,
    current_version: str = "",
    latest_version: str = "",
    release_url: str = "",
    target_path: str = "",
    percent: float | None = None,
    downloaded_gib: float | None = None,
    total_gib: float | None = None,
    speed_mbps: float | None = None,
    eta_seconds: int | None = None,
) -> dict[str, Any]:
    return _default_progress_payload(
        actionId=action_id,
        status=status,
        phase=phase,
        isActive=is_active,
        currentVersion=current_version,
        latestVersion=latest_version,
        releaseUrl=release_url,
        targetPath=target_path,
        percent=percent,
        downloadedGiB=downloaded_gib,
        totalGiB=total_gib,
        speedMBps=speed_mbps,
        etaSeconds=eta_seconds,
        message=message,
    )


def _bytes_to_gib(value: int) -> float:
    return value / (1024 ** 3)


def _file_size_gib(path: Path) -> float:
    return _bytes_to_gib(path.stat().st_size)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_update_error_message(exc: Exception, target_path: Path) -> str:
    message = str(exc) or "Update nije uspeo."
    lowered = message.lower()
    if "access is denied" in lowered or "permission denied" in lowered or "winerror 5" in lowered:
        return (
            f"Windows nije dozvolio pristup installer fajlu: {target_path}. "
            "Najverovatnije je prethodni installer jos otvoren ili je fajl zakljucan. "
            "Zatvori stari installer ako postoji i pokreni Install update ponovo."
        )
    return message


def _extract_path_from_message(message: str) -> str:
    match = re.search(r"([A-Za-z]:\\\\[^']+\.exe)", message)
    if match:
        return match.group(1).replace("\\\\", "\\")
    return ""


def _load_release_info_fallback() -> dict[str, Any]:
    home = detect_local_qwen_home()
    current_version = _read_current_version(home)
    latest_version, release_url = _resolve_latest_release_without_api()
    update_available = (
        bool(current_version)
        and bool(latest_version)
        and _compare_versions(latest_version, current_version) > 0
    )
    latest_tag = f"v{latest_version}" if latest_version else ""
    repo = "https://github.com/joes021/Local-Qwen-3.635Ba3B-on-home-computer"
    return {
        "currentVersion": current_version or "unknown",
        "latestVersion": latest_version or "unknown",
        "latestTag": latest_tag,
        "updateAvailable": update_available,
        "aheadOfPublicRelease": False,
        "versionRelation": "equal" if not update_available and current_version == latest_version else ("older" if update_available else "unknown"),
        "releaseUrl": release_url or f"{repo}/releases/latest",
        "windowsInstallerUrl": f"{repo}/releases/latest/download/Local-Qwen-Setup-latest.exe",
        "linuxInstallerUrl": f"{repo}/releases/latest/download/Local-Qwen-Setup-latest.run",
    }


def _read_current_version(home: Path) -> str:
    version_path = home / "version.json"
    if not version_path.is_file():
        return ""
    try:
        payload = json.loads(version_path.read_text(encoding="utf-8-sig"))
        return str(payload.get("version") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def _resolve_latest_release_without_api() -> tuple[str, str]:
    request = Request(
        "https://github.com/joes021/Local-Qwen-3.635Ba3B-on-home-computer/releases/latest",
        headers={"User-Agent": "LocalQwen-ControlCenterNext/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        final_url = response.geturl()
    match = re.search(r"/tag/v([0-9][^/?#]*)", final_url)
    version = match.group(1) if match else ""
    return version, final_url


def _compare_versions(left: str, right: str) -> int:
    def parse(value: str) -> list[int]:
        return [int(part) for part in re.findall(r"\d+", value)]

    left_parts = parse(left)
    right_parts = parse(right)
    length = max(len(left_parts), len(right_parts))
    left_parts.extend([0] * (length - len(left_parts)))
    right_parts.extend([0] * (length - len(right_parts)))
    if left_parts > right_parts:
        return 1
    if left_parts < right_parts:
        return -1
    return 0
