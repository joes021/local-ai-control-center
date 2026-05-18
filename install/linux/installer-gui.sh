#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install.sh"
TUI_SCRIPT="$SCRIPT_DIR/installer-tui.sh"
TARGET_ARCH="$(cat "$SCRIPT_DIR/../../.target-architecture" 2>/dev/null || uname -m)"

has_desktop_session() {
  [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ] || [ "${XDG_SESSION_TYPE:-}" = "x11" ] || [ "${XDG_SESSION_TYPE:-}" = "wayland" ]
}

pick_terminal() {
  local candidate
  for candidate in x-terminal-emulator gnome-terminal konsole xfce4-terminal mate-terminal tilix kitty alacritty xterm; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

launch_script_in_terminal() {
  local runner_script="$1"
  local terminal_bin
  terminal_bin="$(pick_terminal || true)"
  if [ -z "$terminal_bin" ]; then
    return 1
  fi

  case "$terminal_bin" in
    gnome-terminal|tilix|xfce4-terminal|mate-terminal)
      "$terminal_bin" -- bash "$runner_script"
      ;;
    *)
      "$terminal_bin" -e bash "$runner_script"
      ;;
  esac
}

if ! has_desktop_session || ! command -v zenity >/dev/null 2>&1; then
  exec bash "$TUI_SCRIPT"
fi

INSTALL_VARIANT="$(zenity --list \
  --radiolist \
  --title="Local AI Control Center Setup" \
  --text="Izaberi izdanje instalacije" \
  --column="Pick" --column="Edition" --column="Opis" \
  TRUE Unified "Classic full stack + Control Center Next web shell" \
  FALSE Classic "Samo legacy Classic Full control center"
)"

if [ -z "${INSTALL_VARIANT:-}" ]; then
  exit 1
fi

INSTALL_ROOT="$(zenity --entry \
  --title="Local AI Control Center Setup" \
  --text="Install root" \
  --entry-text="${HOME}/local-qwen-home")"

if [ -z "${INSTALL_ROOT:-}" ]; then
  exit 1
fi

ACCESS_MODE="$(zenity --list \
  --radiolist \
  --title="Access mode" \
  --text="Izaberi Access mode za Control Center" \
  --column="Pick" --column="Mode" --column="Opis" \
  TRUE local-only "Samo lokalni pristup" \
  FALSE tailscale "Omoguci pristup preko tailscale mreze"
)"

if [ -z "${ACCESS_MODE:-}" ]; then
  exit 1
fi

PROFILE="$(
  zenity --list \
    --radiolist \
    --title="Local AI Control Center Setup" \
    --text="Izaberi profil" \
    --column="Pick" --column="Profil" --column="Opis" \
    TRUE balanced "Najbolji balans za vecinu masina" \
    FALSE speed "Brzi i laksi rad" \
    FALSE video "Veci kvalitet na jacim masinama"
)"

if [ -z "${PROFILE:-}" ]; then
  exit 1
fi

DOWNLOAD_MODEL_ANSWER=1
if ! zenity --question \
  --title="Model download" \
  --text="Preuzmi preporuceni model odmah?"; then
  DOWNLOAD_MODEL_ANSWER=0
fi

INSTALL_OPENCODE_ANSWER=1
if ! zenity --question \
  --title="OpenCode" \
  --text="Instaliraj OpenCode ako nije vec prisutan?"; then
  INSTALL_OPENCODE_ANSWER=0
fi

BUILD_RUNTIME_ANSWER=1
if ! zenity --question \
  --title="llama.cpp runtime" \
  --text="Build-uj llama.cpp runtime odmah?"; then
  BUILD_RUNTIME_ANSWER=0
fi

INSTALL_TURBOQUANT_ANSWER=1
if [ "$TARGET_ARCH" = "arm64" ] || [ "$TARGET_ARCH" = "aarch64" ]; then
  zenity --warning \
    --title="TurboQuant" \
    --text="TurboQuant opcija nije dostupna na arm64 Ubuntu instalaciji."
  INSTALL_TURBOQUANT_ANSWER=0
else
  if ! zenity --question \
    --title="TurboQuant" \
    --text="Instaliraj i build-uj TurboQuant runtime ako je podrzan?"; then
    INSTALL_TURBOQUANT_ANSWER=0
  fi
fi

RUNNER_SCRIPT="$(mktemp)"
cat > "$RUNNER_SCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export INSTALL_ROOT=$(printf '%q' "$INSTALL_ROOT")
export INSTALL_VARIANT=$(printf '%q' "${INSTALL_VARIANT,,}")
export ACCESS_MODE=$(printf '%q' "$ACCESS_MODE")
export PROFILE=$(printf '%q' "$PROFILE")
export SKIP_MODEL_DOWNLOAD=$([ "$DOWNLOAD_MODEL_ANSWER" -eq 1 ] && echo 0 || echo 1)
export INSTALL_OPENCODE=$([ "$INSTALL_OPENCODE_ANSWER" -eq 1 ] && echo 1 || echo 0)
export SKIP_RUNTIME_BUILD=$([ "$BUILD_RUNTIME_ANSWER" -eq 1 ] && echo 0 || echo 1)
export INSTALL_TURBOQUANT=$([ "$INSTALL_TURBOQUANT_ANSWER" -eq 1 ] && echo 1 || echo 0)
bash $(printf '%q' "$INSTALL_SCRIPT")
exit_code=\$?
echo
if [ "\$exit_code" -eq 0 ]; then
  echo "Installation complete."
else
  echo "Installation failed with exit code \$exit_code."
fi
echo
read -r -p "Press Enter to close..." _
exit "\$exit_code"
EOF
chmod +x "$RUNNER_SCRIPT"

if launch_script_in_terminal "$RUNNER_SCRIPT"; then
  exit 0
fi

exec bash "$TUI_SCRIPT"
