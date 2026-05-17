from __future__ import annotations

import os
import shutil
import subprocess

from backend.app.services.platform_config import get_target_platform


def choose_dialog_command(which_command=shutil.which) -> str | None:
    for candidate in ("zenity", "qarma", "kdialog"):
        if which_command(candidate):
            return candidate
    return None


def pick_file(*, title: str, file_filter_name: str | None = None, pattern: str | None = None) -> dict[str, object]:
    if get_target_platform() == "windows":
        return _run_windows_picker(
            title=title,
            directory=False,
            file_filter_name=file_filter_name,
            pattern=pattern,
        )

    command = choose_dialog_command()
    if not command:
        return {
            "status": "error",
            "summary": "Nije pronadjen sistemski file picker (zenity/qarma/kdialog).",
            "path": "",
        }
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return {
            "status": "error",
            "summary": "GUI picker nije dostupan bez aktivne desktop sesije.",
            "path": "",
        }

    args = _build_picker_args(command, title=title, directory=False, file_filter_name=file_filter_name, pattern=pattern)
    return _run_picker(command, args)


def pick_directory(*, title: str) -> dict[str, object]:
    if get_target_platform() == "windows":
        return _run_windows_picker(title=title, directory=True)

    command = choose_dialog_command()
    if not command:
        return {
            "status": "error",
            "summary": "Nije pronadjen sistemski folder picker (zenity/qarma/kdialog).",
            "path": "",
        }
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return {
            "status": "error",
            "summary": "GUI picker nije dostupan bez aktivne desktop sesije.",
            "path": "",
        }

    args = _build_picker_args(command, title=title, directory=True)
    return _run_picker(command, args)


def _build_picker_args(
    command: str,
    *,
    title: str,
    directory: bool,
    file_filter_name: str | None = None,
    pattern: str | None = None,
) -> list[str]:
    if command in {"zenity", "qarma"}:
        args = ["--file-selection", f"--title={title}"]
        if directory:
            args.append("--directory")
        if pattern and not directory:
            filter_name = file_filter_name or "Files"
            args.append(f"--file-filter={filter_name} | {pattern}")
        return args

    args = ["--getopenfilename" if not directory else "--getexistingdirectory", ".", title]
    return args


def _run_picker(command: str, args: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        [command, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    selected = completed.stdout.strip()
    if completed.returncode != 0 or not selected:
        return {
            "status": "cancelled",
            "summary": "Picker je zatvoren bez izbora.",
            "path": "",
        }
    return {
        "status": "ok",
        "summary": selected,
        "path": selected,
    }


def _run_windows_picker(
    *,
    title: str,
    directory: bool,
    file_filter_name: str | None = None,
    pattern: str | None = None,
) -> dict[str, object]:
    script = _build_windows_picker_script(
        title=title,
        directory=directory,
        file_filter_name=file_filter_name,
        pattern=pattern,
    )
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    selected = completed.stdout.strip()
    if completed.returncode != 0:
        return {
            "status": "error",
            "summary": (completed.stderr.strip() or "Windows picker nije uspeo."),
            "path": "",
        }
    if not selected:
        return {
            "status": "cancelled",
            "summary": "Picker je zatvoren bez izbora.",
            "path": "",
        }
    return {
        "status": "ok",
        "summary": selected,
        "path": selected,
    }


def _ps_single_quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _build_windows_picker_script(
    *,
    title: str,
    directory: bool,
    file_filter_name: str | None = None,
    pattern: str | None = None,
) -> str:
    if directory:
        return (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
            f"$dialog.Description = {_ps_single_quoted(title)}; "
            "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
            "$dialog.SelectedPath }"
        )

    filter_name = file_filter_name or "Files"
    filter_pattern = pattern or "*.*"
    return (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dialog = New-Object System.Windows.Forms.OpenFileDialog; "
        f"$dialog.Title = {_ps_single_quoted(title)}; "
        f"$dialog.Filter = {_ps_single_quoted(f'{filter_name}|{filter_pattern}')}; "
        "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
        "$dialog.FileName }"
    )
