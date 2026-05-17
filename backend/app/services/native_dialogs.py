from __future__ import annotations

import os
import shutil
import subprocess


def choose_dialog_command(which_command=shutil.which) -> str | None:
    for candidate in ("zenity", "qarma", "kdialog"):
        if which_command(candidate):
            return candidate
    return None


def pick_file(*, title: str, file_filter_name: str | None = None, pattern: str | None = None) -> dict[str, object]:
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
