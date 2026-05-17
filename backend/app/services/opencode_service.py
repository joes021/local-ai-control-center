from __future__ import annotations

import json
import subprocess
from pathlib import Path

from backend.app.services.local_qwen_paths import detect_local_qwen_home, detect_local_qwen_repo_fallback
from backend.app.services.platform_config import get_target_platform
from backend.app.services.settings_service import load_settings_payload
from backend.app.services.windows_common_runner import invoke_windows_common_json, resolve_windows_common_script


def load_opencode_status_payload() -> dict[str, object]:
    if get_target_platform() != "windows":
        settings = load_settings_payload()
        return {
            "available": False,
            "configExists": False,
            "configPath": "",
            "configDir": "",
            "executablePath": "",
            "workingDirectory": str(settings.get("workingDirectory", "")),
            "buildSteps": int(settings.get("buildSteps", 0) or 0),
            "planSteps": int(settings.get("planSteps", 0) or 0),
            "generalSteps": int(settings.get("generalSteps", 0) or 0),
            "exploreSteps": int(settings.get("exploreSteps", 0) or 0),
            "securityMode": "strict",
            "capabilityMode": "confirm-commands",
            "profile": str(settings.get("profile", "balanced") or "balanced"),
            "auditRiskLevel": "",
            "auditSummary": "OpenCode parity backend je za sada aktivan samo na Windowsu.",
        }

    settings = load_settings_payload()
    available = _read_windows_common_scalar("Test-OpenCodeAvailable", default=False)
    config_path = str(_read_windows_common_scalar("Get-OpenCodeConfigPath", default="") or "")
    executable_path = ""
    if available:
        executable_path = str(_read_windows_common_scalar("Get-OpenCodeExecutable", default="") or "")

    agent_meta = _load_agent_meta()
    security_mode = str(agent_meta.get("securityMode", "strict") or "strict")
    capability_mode = str(agent_meta.get("capabilityMode", "confirm-commands") or "confirm-commands")
    working_directory = str(
        agent_meta.get("workingFolder")
        or settings.get("workingDirectory")
        or Path.home()
    )
    profile = str(agent_meta.get("profile") or settings.get("profile", "balanced") or "balanced")
    audit = agent_meta.get("audit") if isinstance(agent_meta.get("audit"), dict) else {}
    return {
        "available": bool(available),
        "configExists": bool(config_path) and Path(config_path).is_file(),
        "configPath": config_path,
        "configDir": str(Path(config_path).parent) if config_path else "",
        "executablePath": executable_path,
        "workingDirectory": working_directory,
        "buildSteps": int(settings.get("buildSteps", 0) or 0),
        "planSteps": int(settings.get("planSteps", 0) or 0),
        "generalSteps": int(settings.get("generalSteps", 0) or 0),
        "exploreSteps": int(settings.get("exploreSteps", 0) or 0),
        "securityMode": security_mode,
        "capabilityMode": capability_mode,
        "profile": profile,
        "auditRiskLevel": str(audit.get("riskLevel", "") or ""),
        "auditSummary": _summarize_audit(audit),
    }


def apply_opencode_settings(payload: dict[str, object]) -> dict[str, object]:
    if get_target_platform() != "windows":
        return _result("error", "apply-opencode-settings", "OpenCode settings parity je za sada dostupan samo na Windowsu.")

    profile = str(payload.get("profile", "balanced") or "balanced")
    working_directory = str(payload.get("workingDirectory", "") or "").strip()
    security_mode = str(payload.get("securityMode", "strict") or "strict")
    capability_mode = str(payload.get("capabilityMode", "confirm-commands") or "confirm-commands")
    settings = _load_windows_settings_json()
    llama = settings.setdefault("llama", {})
    opencode = settings.setdefault("opencode", {})
    settings["profile"] = profile
    llama["contextSize"] = int(payload.get("context", llama.get("contextSize", 262144)) or 262144)
    llama["maxOutputTokens"] = int(payload.get("outputTokens", llama.get("maxOutputTokens", 8192)) or 8192)
    llama["contextSizeCustomized"] = True
    llama["maxOutputTokensCustomized"] = True
    opencode["buildSteps"] = int(payload.get("buildSteps", opencode.get("buildSteps", 80)) or 80)
    opencode["planSteps"] = int(payload.get("planSteps", opencode.get("planSteps", 60)) or 60)
    opencode["generalSteps"] = int(payload.get("generalSteps", opencode.get("generalSteps", 70)) or 70)
    opencode["exploreSteps"] = int(payload.get("exploreSteps", opencode.get("exploreSteps", 40)) or 40)
    opencode["workingDirectory"] = working_directory or str(Path.home())

    state_path = _write_temp_settings(settings)
    try:
        save_result = _run_powershell_command(
            (
                "$ErrorActionPreference='Stop'; "
                f". '{resolve_windows_common_script()}'; "
                f"$settings = Get-Content -Raw '{state_path}' | ConvertFrom-Json; "
                "Save-Settings -Settings $settings; "
                "$configPath = Update-OpenCodeConfig; "
                "Write-Output \"Sacuvano.\"; "
                "Write-Output \"OpenCode config: $configPath\""
            )
        )
        if save_result.returncode != 0:
            return _result(
                "error",
                "apply-opencode-settings",
                save_result.stderr.strip() or save_result.stdout.strip() or "OpenCode settings nisu sacuvani.",
                save_result,
            )

        launch_agent_script = _resolve_windows_launcher_script("launch-agent.ps1")
        audit_result = _run_powershell_file(
            launch_agent_script,
            [
                "-SecurityMode",
                security_mode,
                "-CapabilityMode",
                capability_mode,
                "-WorkingFolder",
                opencode["workingDirectory"],
                "-Profile",
                profile,
                "-NoLaunch",
            ],
        )
        if audit_result.returncode != 0:
            return _result(
                "error",
                "apply-opencode-settings",
                audit_result.stderr.strip() or audit_result.stdout.strip() or "Agent/OpenCode metadata nisu sacuvani.",
                audit_result,
            )
        stdout = "\n".join(
            item for item in [save_result.stdout.strip(), audit_result.stdout.strip()] if item
        )
        return {
            "status": "ok",
            "action": "apply-opencode-settings",
            "summary": "OpenCode settings su sacuvani.",
            "details": {
                "returncode": 0,
                "stdout": stdout,
                "stderr": "",
            },
        }
    finally:
        try:
            state_path.unlink(missing_ok=True)
        except OSError:
            pass


def open_opencode(profile: str = "") -> dict[str, object]:
    if get_target_platform() != "windows":
        return _result("error", "open-opencode", "OpenCode launch parity je za sada dostupan samo na Windowsu.")

    script_path = _resolve_windows_launcher_script("start-opencode.ps1")
    args: list[str] = []
    if profile:
        args.extend(["-Profile", profile])
    completed = _run_powershell_file(script_path, args)
    if completed.returncode != 0:
        return _result(
            "error",
            "open-opencode",
            completed.stderr.strip() or completed.stdout.strip() or "OpenCode nije pokrenut.",
            completed,
        )
    return {
        "status": "ok",
        "action": "open-opencode",
        "summary": "OpenCode je pokrenut.",
        "details": {
            "returncode": 0,
            "stdout": completed.stdout.strip(),
            "stderr": "",
        },
    }


def _load_agent_meta() -> dict[str, object]:
    path = detect_local_qwen_home() / "state" / "agent-launch-settings.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_windows_settings_json() -> dict[str, object]:
    result = invoke_windows_common_json("Get-Settings")
    payload = result.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def _read_windows_common_scalar(function_name: str, default: object = "") -> object:
    result = invoke_windows_common_json(function_name)
    if result.get("status") != "ok":
        return default
    payload = result.get("payload")
    if isinstance(payload, dict) and "value" in payload:
        return payload["value"]
    return payload


def _summarize_audit(audit: dict[str, object]) -> str:
    if not audit:
        return "Nema sacuvanog OpenCode audit rezimea."
    risk = str(audit.get("riskLevel", "") or "").strip()
    reasons = audit.get("reasons")
    if isinstance(reasons, list) and reasons:
        first_reason = str(reasons[0] or "").strip()
    else:
        first_reason = ""
    if risk and first_reason:
        return f"{risk}: {first_reason}"
    if risk:
        return f"Risk level: {risk}"
    return "OpenCode audit je sacuvan bez dodatnih detalja."


def _resolve_windows_launcher_script(name: str) -> Path:
    installed = detect_local_qwen_home() / "launchers" / name
    if installed.is_file():
        return installed
    return detect_local_qwen_repo_fallback() / "launcher" / "windows" / name


def _write_temp_settings(payload: dict[str, object]) -> Path:
    path = detect_local_qwen_home() / "state" / "__control_center_next_opencode_settings_tmp.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _run_powershell_command(command: str) -> subprocess.CompletedProcess[str]:
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


def _run_powershell_file(script_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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
    )


def _result(
    status: str,
    action: str,
    summary: str,
    completed: subprocess.CompletedProcess[str] | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "action": action,
        "summary": summary,
        "details": {
            "returncode": completed.returncode if completed else (0 if status == "ok" else 1),
            "stdout": completed.stdout.strip() if completed else "",
            "stderr": completed.stderr.strip() if completed else ("" if status == "ok" else summary),
        },
    }
