#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_EXEC_SCRIPT="${LOCAL_QWEN_INSTALLER_TARGET_SCRIPT:-$SCRIPT_DIR/install.sh}"
TARGET_ARCH="$(cat "$SCRIPT_DIR/../../.target-architecture" 2>/dev/null || uname -m)"

prompt_with_default() {
  local label="$1"
  local default_value="$2"
  local result
  read -r -p "$label [$default_value]: " result
  if [ -z "$result" ]; then
    result="$default_value"
  fi
  printf '%s' "$result"
}

pick_yes_no() {
  local label="$1"
  local default_value="$2"
  local result
  while true; do
    read -r -p "$label ($default_value): " result
    result="${result,,}"
    if [ -z "$result" ]; then
      result="$default_value"
    fi
    case "$result" in
      y|yes) printf 'y'; return 0 ;;
      n|no) printf 'n'; return 0 ;;
      *) echo "Odgovori sa y ili n." >&2 ;;
    esac
  done
}

echo
echo "Local AI Control Center Linux Installer"
echo "Wizard mode: next, next, finish"
echo "Edition options: Classic | Unified"
echo

INSTALL_VARIANT="$(prompt_with_default 'Edition (Classic/Unified)' 'Unified')"
INSTALL_VARIANT="${INSTALL_VARIANT,,}"
if [ "$INSTALL_VARIANT" != "classic" ] && [ "$INSTALL_VARIANT" != "unified" ]; then
  echo "Edition mora biti Classic ili Unified." >&2
  exit 1
fi

INSTALL_ROOT="$(prompt_with_default 'Install root' "$HOME/local-qwen-home")"
ACCESS_MODE="$(prompt_with_default 'Access mode (local-only/tailscale)' 'local-only')"
PROFILE="$(prompt_with_default 'Profil (balanced/speed/video)' 'balanced')"

DOWNLOAD_MODEL_ANSWER="$(pick_yes_no 'Download model now? y/n' 'y')"
INSTALL_OPENCODE_ANSWER="$(pick_yes_no 'Install OpenCode? y/n' 'y')"
BUILD_RUNTIME_ANSWER="$(pick_yes_no 'Build llama.cpp runtime now? y/n' 'y')"

INSTALL_TURBOQUANT_ANSWER="n"
if [ "$TARGET_ARCH" = "arm64" ] || [ "$TARGET_ARCH" = "aarch64" ]; then
  echo "TurboQuant opcija je onemogucena na arm64 Ubuntu instalaciji."
else
  INSTALL_TURBOQUANT_ANSWER="$(pick_yes_no 'Install TurboQuant? y/n' 'y')"
fi

SKIP_MODEL_DOWNLOAD=0
SKIP_RUNTIME_BUILD=0
INSTALL_OPENCODE=1
INSTALL_TURBOQUANT=0

[ "$DOWNLOAD_MODEL_ANSWER" = "n" ] && SKIP_MODEL_DOWNLOAD=1
[ "$BUILD_RUNTIME_ANSWER" = "n" ] && SKIP_RUNTIME_BUILD=1
[ "$INSTALL_OPENCODE_ANSWER" = "n" ] && INSTALL_OPENCODE=0
[ "$INSTALL_TURBOQUANT_ANSWER" = "y" ] && INSTALL_TURBOQUANT=1

echo
echo "Izabrane vrednosti:"
echo "- Edition: $INSTALL_VARIANT"
echo "- Install root: $INSTALL_ROOT"
echo "- Access mode: $ACCESS_MODE"
echo "- Profil: $PROFILE"
echo "- Download model: $DOWNLOAD_MODEL_ANSWER"
echo "- Install OpenCode: $INSTALL_OPENCODE_ANSWER"
echo "- Build runtime: $BUILD_RUNTIME_ANSWER"
echo "- Install TurboQuant: $INSTALL_TURBOQUANT_ANSWER"
echo

CONFIRM_INSTALL="$(pick_yes_no 'Potvrdi instalaciju? y/n' 'y')"
if [ "$CONFIRM_INSTALL" = "n" ]; then
  echo "Instalacija je otkazana."
  exit 1
fi

INSTALL_ROOT="$INSTALL_ROOT" \
INSTALL_VARIANT="$INSTALL_VARIANT" \
ACCESS_MODE="$ACCESS_MODE" \
PROFILE="$PROFILE" \
SKIP_MODEL_DOWNLOAD="$SKIP_MODEL_DOWNLOAD" \
SKIP_RUNTIME_BUILD="$SKIP_RUNTIME_BUILD" \
INSTALL_OPENCODE="$INSTALL_OPENCODE" \
INSTALL_TURBOQUANT="$INSTALL_TURBOQUANT" \
bash "$INSTALL_EXEC_SCRIPT"
