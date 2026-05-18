#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install.sh"
TUI_SCRIPT="$SCRIPT_DIR/installer-tui.sh"
TARGET_ARCH="$(cat "$SCRIPT_DIR/../../.target-architecture" 2>/dev/null || uname -m)"
RECOMMENDED_MODELS_PATH="$SCRIPT_DIR/../shared/recommended-models.json"

fallback_default_model_id() {
  printf '%s\n' "gemma-4-e4b-it-q4-0"
}

fallback_recommended_models() {
  cat <<'EOF'
gemma-4-e4b-it-q4-0|Gemma 4 E4B Instruct Q4_0|6 GB|Najbezbedniji podrazumevani izbor za slabije GPU konfiguracije i brz prvi start instalera.|gemma-4-E4B-it-Q4_0.gguf
qwen3.6-35b-a3b-ud-iq2-xxs|Qwen3.6 35B A3B UD IQ2_XXS|12 GB|Balansiran Qwen izbor za korisnike koji hoce veci model uz umeren VRAM budzet.|Qwen3.6-35B-A3B-UD-IQ2_XXS.gguf
qwen3.6-35b-a3b-mtp-ud-q4-k-xl|Qwen3.6 35B A3B MTP UD Q4_K_XL|24 GB|High-end preporuceni profil za sisteme koji ciljaju zakljucanu MTP varijantu i imaju 24 GB VRAM klase.|Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf
EOF
}

load_default_model_id() {
  if command -v python3 >/dev/null 2>&1 && [ -f "$RECOMMENDED_MODELS_PATH" ]; then
    python3 - <<'PY' "$RECOMMENDED_MODELS_PATH" 2>/dev/null || fallback_default_model_id
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("defaultModelId") or "gemma-4-e4b-it-q4-0")
PY
    return 0
  fi
  fallback_default_model_id
}

load_recommended_models() {
  if command -v python3 >/dev/null 2>&1 && [ -f "$RECOMMENDED_MODELS_PATH" ]; then
    python3 - <<'PY' "$RECOMMENDED_MODELS_PATH" 2>/dev/null || fallback_recommended_models
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for entry in payload.get("recommended", [])[:3]:
    print("|".join([
        str(entry.get("modelId", "")),
        str(entry.get("label", "")),
        str(entry.get("vramClass", {}).get("label", "")),
        str(entry.get("description", "")),
        str(entry.get("downloadFile", "")),
    ]))
PY
    return 0
  fi
  fallback_recommended_models
}

find_model_download_file() {
  local target_model_id="$1"
  local entry model_id label vram_label description download_file
  for entry in "${RECOMMENDED_MODELS[@]}"; do
    IFS='|' read -r model_id label vram_label description download_file <<<"$entry"
    if [ "$model_id" = "$target_model_id" ]; then
      printf '%s\n' "$download_file"
      return 0
    fi
  done
  return 1
}

pick_guided_model_gui() {
  local default_model_id="$1"
  local entry model_id label vram_label description download_file selected rows selection

  while true; do
    rows=()
    for entry in "${RECOMMENDED_MODELS[@]}"; do
      IFS='|' read -r model_id label vram_label description download_file <<<"$entry"
      selected=FALSE
      if [ "$model_id" = "$default_model_id" ]; then
        selected=TRUE
      fi
      rows+=("$selected" "$model_id" "$label" "$vram_label" "$description")
    done

    selection="$(zenity --list \
      --radiolist \
      --title="Model selection" \
      --text="Izaberi preporuceni model za prvi bootstrap korak" \
      --column="Pick" --column="MODEL_ID" --column="Model" --column="VRAM" --column="Opis" \
      "${rows[@]}" \
      --extra-button="Prikazi jos modela")"

    if [ -z "${selection:-}" ]; then
      return 1
    fi

    if [ "$selection" = "Prikazi jos modela" ]; then
      zenity --info \
        --title="Prikazi jos modela" \
        --text="Za sada installer vodi kroz 3 preporucena modela iz shared recommended-models.json payload-a. Sire model browse opcije dolaze u kasnijem model setup koraku."
      continue
    fi

    printf '%s\n' "$selection"
    return 0
  done
}

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
  --entry-text="${HOME}/local-ai-control-center")"

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

DEFAULT_MODEL_ID="$(load_default_model_id)"
mapfile -t RECOMMENDED_MODELS < <(load_recommended_models)
MODEL_ID="$(pick_guided_model_gui "$DEFAULT_MODEL_ID")"
if [ -z "${MODEL_ID:-}" ]; then
  exit 1
fi
MODEL_FILE="$(find_model_download_file "$MODEL_ID" || true)"

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
export SELECTED_MODEL_ID=$(printf '%q' "$MODEL_ID")
export SELECTED_MODEL_FILE=$(printf '%q' "$MODEL_FILE")
export SKIP_MODEL_DOWNLOAD=0
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

zenity --info \
  --title="Pokretanje instalacije" \
  --text="Sistemski terminal nije pronadjen. Instalacija se nastavlja u ovom terminalu bez dodatnog tekstualnog wizarda." || true

exec bash "$RUNNER_SCRIPT"
