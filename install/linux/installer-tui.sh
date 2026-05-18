#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_EXEC_SCRIPT="${LOCAL_QWEN_INSTALLER_TARGET_SCRIPT:-$SCRIPT_DIR/install.sh}"
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

pick_guided_model_tui() {
  local default_model_id="$1"
  local default_index=1
  local selection entry model_id label vram_label description download_file index

  while true; do
    echo
    echo "Izaberi preporuceni model za prvi bootstrap korak:"
    index=1
    for entry in "${RECOMMENDED_MODELS[@]}"; do
      IFS='|' read -r model_id label vram_label description download_file <<<"$entry"
      if [ "$model_id" = "$default_model_id" ]; then
        default_index="$index"
        echo "  $index. $label [$vram_label] (defaultModelId)"
      else
        echo "  $index. $label [$vram_label]"
      fi
      echo "     MODEL_ID: $model_id"
      echo "     $description"
      index=$((index + 1))
    done
    echo "  m. Prikazi jos modela"
    read -r -p "Izbor modela [$default_index]: " selection
    selection="${selection:-$default_index}"
    case "${selection,,}" in
      1|2|3)
        index=1
        for entry in "${RECOMMENDED_MODELS[@]}"; do
          IFS='|' read -r model_id label vram_label description download_file <<<"$entry"
          if [ "$index" = "$selection" ]; then
            printf '%s\n' "$model_id"
            return 0
          fi
          index=$((index + 1))
        done
        ;;
      m)
        echo "Prikazi jos modela: za sada installer vodi kroz 3 preporucena modela iz shared recommended-models.json payload-a. Sire model browse opcije dolaze u kasnijem model setup koraku."
        ;;
      *)
        echo "Izaberi 1, 2, 3 ili m." >&2
        ;;
    esac
  done
}

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
DEFAULT_MODEL_ID="$(load_default_model_id)"
mapfile -t RECOMMENDED_MODELS < <(load_recommended_models)
MODEL_ID="$(pick_guided_model_tui "$DEFAULT_MODEL_ID")"
MODEL_FILE="$(find_model_download_file "$MODEL_ID" || true)"

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

[ "$BUILD_RUNTIME_ANSWER" = "n" ] && SKIP_RUNTIME_BUILD=1
[ "$INSTALL_OPENCODE_ANSWER" = "n" ] && INSTALL_OPENCODE=0
[ "$INSTALL_TURBOQUANT_ANSWER" = "y" ] && INSTALL_TURBOQUANT=1

echo
echo "Izabrane vrednosti:"
echo "- Edition: $INSTALL_VARIANT"
echo "- Install root: $INSTALL_ROOT"
echo "- Access mode: $ACCESS_MODE"
echo "- Profil: $PROFILE"
echo "- Model: $MODEL_ID"
echo "- Model file: $MODEL_FILE"
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
SELECTED_MODEL_ID="$MODEL_ID" \
SELECTED_MODEL_FILE="$MODEL_FILE" \
SKIP_MODEL_DOWNLOAD="$SKIP_MODEL_DOWNLOAD" \
SKIP_RUNTIME_BUILD="$SKIP_RUNTIME_BUILD" \
INSTALL_OPENCODE="$INSTALL_OPENCODE" \
INSTALL_TURBOQUANT="$INSTALL_TURBOQUANT" \
bash "$INSTALL_EXEC_SCRIPT"
