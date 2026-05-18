#!/usr/bin/env bash
set -euo pipefail

# Unified installer overlay for legacy Local Qwen 3.635Ba3B on home computer core.
# The installer keeps the local-qwen legacy runtime assumptions while deploying control-center-next.
INSTALL_ROOT="${INSTALL_ROOT:-$HOME/local-qwen-home}"
INSTALL_VARIANT="${INSTALL_VARIANT:-unified}"
ACCESS_MODE="${ACCESS_MODE:-local-only}"
PROFILE="${PROFILE:-balanced}"
SKIP_DEPENDENCIES="${SKIP_DEPENDENCIES:-0}"
INSTALL_OPENCODE="${INSTALL_OPENCODE:-1}"
SKIP_LLAMA_SETUP="${SKIP_LLAMA_SETUP:-0}"
INSTALL_TURBOQUANT="${INSTALL_TURBOQUANT:-1}"
SKIP_MODEL_DOWNLOAD="${SKIP_MODEL_DOWNLOAD:-1}"

PAYLOAD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORKSPACE_ROOT="$INSTALL_ROOT"
APP_ROOT="$WORKSPACE_ROOT/control-center-next"
STATE_DIR="$WORKSPACE_ROOT/state"
APPS_DIR="$WORKSPACE_ROOT/apps"
BIN_DIR="$WORKSPACE_ROOT/bin"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
INSTALL_STATE_PATH="$STATE_DIR/install-state.json"
INSTALL_REPORT_PATH="$STATE_DIR/install-report.json"
SETTINGS_PATH="$STATE_DIR/settings.json"
RUNTIME_CONFIG_PATH="$STATE_DIR/runtime-config.json"
OPENCODE_WORKSPACE_DIR="$WORKSPACE_ROOT/opencode-workspace"
TARGET_ARCH="$(cat "$PAYLOAD_ROOT/.target-architecture" 2>/dev/null || echo "unknown")"
HOST_ARCH="$(uname -m)"

if [ "$TARGET_ARCH" = "aarch64" ]; then
  TARGET_ARCH="arm64"
fi
if [ "$HOST_ARCH" = "aarch64" ]; then
  HOST_ARCH="arm64"
fi

ensure_dir() {
  mkdir -p "$1"
}

copy_if_exists() {
  local source="$1"
  local target="$2"
  if [ -e "$source" ]; then
    mkdir -p "$(dirname "$target")"
    cp -R "$source" "$target"
  fi
}

copy_dir_content() {
  local source="$1"
  local target="$2"
  if [ -d "$source" ]; then
    mkdir -p "$target"
    cp -R "$source"/. "$target"/
  fi
}

write_json() {
  local path="$1"
  local payload="$2"
  mkdir -p "$(dirname "$path")"
  printf '%s\n' "$payload" > "$path"
}

ensure_packages() {
  if [ "$SKIP_DEPENDENCIES" = "1" ]; then
    return
  fi
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y git curl python3 python3-venv python3-pip nodejs npm cmake ninja-build build-essential pkg-config
  fi
}

resolve_opencode_path() {
  local candidate prefix
  if candidate="$(command -v opencode 2>/dev/null)"; then
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  fi

  prefix="$(npm config get prefix 2>/dev/null || true)"
  for candidate in \
    "$prefix/bin/opencode" \
    "$HOME/.local/bin/opencode" \
    "$HOME/.npm-global/bin/opencode" \
    "/usr/local/bin/opencode" \
    "/usr/bin/opencode"
  do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

ensure_opencode() {
  if [ "$INSTALL_OPENCODE" != "1" ]; then
    return 1
  fi
  if resolve_opencode_path >/dev/null 2>&1; then
    return 0
  fi
  npm install -g opencode-ai >/dev/null 2>&1 || true
  resolve_opencode_path >/dev/null 2>&1
}

ensure_llama() {
  local target="$APPS_DIR/llama.cpp"
  if [ -x "$target/build/bin/llama-server" ]; then
    return 0
  fi
  if [ "$SKIP_LLAMA_SETUP" = "1" ]; then
    return 1
  fi
  if [ ! -d "$target" ]; then
    git clone https://github.com/ggml-org/llama.cpp.git "$target" >/dev/null 2>&1 || return 1
  fi
  if [ ! -x "$target/build/bin/llama-server" ] && command -v cmake >/dev/null 2>&1; then
    local generator="Unix Makefiles"
    if command -v ninja >/dev/null 2>&1; then
      generator="Ninja"
    fi
    local cuda_flag="OFF"
    if command -v nvcc >/dev/null 2>&1; then
      cuda_flag="ON"
    fi
    cmake -G "$generator" -S "$target" -B "$target/build" "-DGGML_CUDA=$cuda_flag" >/dev/null 2>&1 || return 1
    cmake --build "$target/build" -j >/dev/null 2>&1 || return 1
  fi
  [ -x "$target/build/bin/llama-server" ]
}

ensure_turboquant() {
  if [ "$INSTALL_TURBOQUANT" != "1" ]; then
    printf 'skipped'
    return 0
  fi
  if [ "$TARGET_ARCH" = "arm64" ] || [ "$HOST_ARCH" = "aarch64" ]; then
    printf 'unsupported'
    return 0
  fi
  local target="$APPS_DIR/llama.cpp-turboquant"
  if [ ! -d "$target" ]; then
    git clone https://github.com/TheTom/llama-cpp-turboquant.git "$target" >/dev/null 2>&1 || {
      printf 'not-installed'
      return 0
    }
  fi
  if command -v cmake >/dev/null 2>&1 && command -v nvcc >/dev/null 2>&1; then
    local generator="Unix Makefiles"
    if command -v ninja >/dev/null 2>&1; then
      generator="Ninja"
    fi
    cmake -G "$generator" -S "$target" -B "$target/build-cuda" -DGGML_CUDA=ON >/dev/null 2>&1 || true
    cmake --build "$target/build-cuda" -j >/dev/null 2>&1 || true
  fi
  if [ -x "$target/build-cuda/bin/llama-server" ] || [ -x "$target/build-cuda/llama-server" ]; then
    printf 'present'
    return 0
  fi
  printf 'not-installed'
}

write_launcher_wrapper() {
  local path="$BIN_DIR/launch-local-ai-control-center.sh"
  cat > "$path" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export LOCAL_QWEN_HOME="$WORKSPACE_ROOT"
exec bash "$APP_ROOT/launchers/linux/start-control-center-next.sh" "\$@"
EOF
  chmod +x "$path"
  printf '%s\n' "$path"
}

patch_legacy_linux_launchers() {
  local launchers_dir="$WORKSPACE_ROOT/launchers"
  local configure_script="$launchers_dir/configure-settings.sh"
  if [ ! -d "$launchers_dir" ]; then
    return 0
  fi
  find "$launchers_dir" -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
  if [ -f "$configure_script" ]; then
    python3 - <<'PY' "$configure_script"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = '"baseURL": "http://127.0.0.1:8091/v1",'
new = '"baseURL": f"http://127.0.0.1:{state[\\"port\\"]}/v1",'
if old in text:
    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
PY
  fi
}

wait_for_control_center_health() {
  local url="$1"
  local attempts="${2:-30}"
  local delay_seconds="${3:-1}"
  local i
  for i in $(seq 1 "$attempts"); do
    if curl --silent --fail "$url/api/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay_seconds"
  done
  return 1
}

read_runtime_port() {
  if [ ! -f "$STATE_DIR/runtime-state.json" ]; then
    return 1
  fi
  python3 - <<'PY' "$STATE_DIR/runtime-state.json"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)

port = data.get("port")
if port is None:
    raise SystemExit(1)
print(port)
PY
}

stop_existing_control_center_service() {
  systemctl --user stop control-center-next >/dev/null 2>&1 || true
  systemctl --user reset-failed control-center-next >/dev/null 2>&1 || true
  pkill -f 'uvicorn backend.app.main:app' >/dev/null 2>&1 || true
  pkill -f 'start-control-center-next.sh' >/dev/null 2>&1 || true
  pkill -f 'launch-local-ai-control-center.sh' >/dev/null 2>&1 || true
}

start_control_center_service() {
  local wrapper_path="$1"
  local runtime_port="3210"
  local local_url=""
  if [ ! -x "$wrapper_path" ]; then
    return 1
  fi
  stop_existing_control_center_service
  CONTROL_CENTER_NEXT_ACCESS_MODE="$ACCESS_MODE" \
  CONTROL_CENTER_NEXT_SKIP_OPEN=1 \
  "$wrapper_path" >/dev/null 2>&1 || true
  runtime_port="$(read_runtime_port || printf '3210')"
  local_url="http://127.0.0.1:${runtime_port}"
  if wait_for_control_center_health "$local_url" 45 1; then
    printf '%s\n' "$local_url"
    return 0
  fi
  return 1
}

write_desktop_entry() {
  local wrapper="$1"
  mkdir -p "$DESKTOP_DIR"
  cat > "$DESKTOP_DIR/local-ai-control-center.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Local AI Control Center
Exec=$wrapper
Terminal=false
Categories=Utility;Development;
EOF
  chmod +x "$DESKTOP_DIR/local-ai-control-center.desktop"
}

ensure_dir "$WORKSPACE_ROOT"
ensure_dir "$STATE_DIR"
ensure_dir "$APPS_DIR"
ensure_dir "$BIN_DIR"
ensure_dir "$OPENCODE_WORKSPACE_DIR"

ensure_packages

copy_dir_content "$PAYLOAD_ROOT/backend" "$APP_ROOT/backend"
copy_dir_content "$PAYLOAD_ROOT/frontend" "$APP_ROOT/frontend"
copy_dir_content "$PAYLOAD_ROOT/launchers" "$APP_ROOT/launchers"
copy_dir_content "$PAYLOAD_ROOT/install" "$APP_ROOT/install"
copy_dir_content "$PAYLOAD_ROOT/config" "$APP_ROOT/config"
copy_dir_content "$PAYLOAD_ROOT/scripts" "$APP_ROOT/scripts"
copy_dir_content "$PAYLOAD_ROOT/assets" "$APP_ROOT/assets"
copy_if_exists "$PAYLOAD_ROOT/run_control_center_next.py" "$APP_ROOT/run_control_center_next.py"
copy_if_exists "$PAYLOAD_ROOT/README.md" "$APP_ROOT/README.md"
copy_if_exists "$PAYLOAD_ROOT/version.json" "$APP_ROOT/version.json"
copy_if_exists "$PAYLOAD_ROOT/version.json" "$WORKSPACE_ROOT/version.json"
copy_if_exists "$PAYLOAD_ROOT/release-notes.txt" "$APP_ROOT/release-notes.txt"
copy_if_exists "$PAYLOAD_ROOT/release-notes.txt" "$WORKSPACE_ROOT/release-notes.txt"
find "$APP_ROOT/launchers" "$APP_ROOT/install" "$BIN_DIR" -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
patch_legacy_linux_launchers

if ensure_opencode; then
  OPENCODE_OK=true
  OPENCODE_PATH="$(resolve_opencode_path || true)"
else
  OPENCODE_OK=false
  OPENCODE_PATH=""
fi

if ensure_llama; then
  LLAMA_OK=true
else
  LLAMA_OK=false
fi

TURBO_STATUS="$(ensure_turboquant)"
LLAMA_BIN="$APPS_DIR/llama.cpp/build/bin/llama-server"
WRAPPER_PATH="$(write_launcher_wrapper)"
write_desktop_entry "$WRAPPER_PATH"
STARTED_CONTROL_CENTER_URL=""

cat > "$INSTALL_STATE_PATH" <<EOF
{
  "edition": "$INSTALL_VARIANT",
  "profile": "$PROFILE",
  "modelId": "none",
  "modelFile": "",
  "port": 8091,
  "llamaServerExe": "$( [ -e "$LLAMA_BIN" ] && printf '%s' "$LLAMA_BIN" )",
  "turboServerExe": "",
  "threads": 8,
  "installRoot": "$WORKSPACE_ROOT",
  "noMmap": false,
  "mlock": false
}
EOF

cat > "$SETTINGS_PATH" <<EOF
{
  "edition": "$INSTALL_VARIANT",
  "profile": "$PROFILE",
  "accessMode": "$ACCESS_MODE",
  "llama": {
    "contextSize": 262144,
    "maxOutputTokens": 8192,
    "contextSizeCustomized": false,
    "maxOutputTokensCustomized": false
  },
  "opencode": {
    "buildSteps": 120,
    "planSteps": 80,
    "generalSteps": 100,
    "exploreSteps": 60,
    "workingDirectory": "$OPENCODE_WORKSPACE_DIR"
  },
  "threads": 8,
  "gpuLayers": 99,
  "batch": 2048,
  "ubatch": 512,
  "temperature": 0.7,
  "topP": 0.95,
  "minP": 0.05,
  "topK": 40
}
EOF

cat > "$RUNTIME_CONFIG_PATH" <<EOF
{
  "accessMode": "$ACCESS_MODE"
}
EOF

cat > "$INSTALL_REPORT_PATH" <<EOF
{
  "installRoot": "$WORKSPACE_ROOT",
  "appRoot": "$APP_ROOT",
  "edition": "$INSTALL_VARIANT",
  "launchWrapper": "$WRAPPER_PATH",
  "localUrl": "http://127.0.0.1:3210",
  "targetArchitecture": "$TARGET_ARCH",
  "hostArchitecture": "$HOST_ARCH",
  "components": {
    "controlCenter": { "ok": true, "path": "$APP_ROOT" },
    "llamaCppRuntime": { "ok": $LLAMA_OK, "path": "$( [ -e "$LLAMA_BIN" ] && printf '%s' "$LLAMA_BIN" )" },
    "openCode": { "ok": $OPENCODE_OK, "path": "$OPENCODE_PATH" },
    "turboQuantRuntime": { "ok": false, "status": "$TURBO_STATUS", "path": "" }
  }
}
EOF

if STARTED_CONTROL_CENTER_URL="$(start_control_center_service "$WRAPPER_PATH")"; then
  python3 - <<'PY' "$INSTALL_REPORT_PATH" "$STARTED_CONTROL_CENTER_URL"
import json, sys
path, local_url = sys.argv[1:3]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
data["controlCenterStarted"] = True
data["localUrl"] = local_url
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PY
else
  python3 - <<'PY' "$INSTALL_REPORT_PATH"
import json, sys
path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
data["controlCenterStarted"] = False
data["startWarning"] = "Control Center nije automatski potvrden kroz health check posle instalacije."
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PY
fi

echo "Install report:"
echo "Edition: $INSTALL_VARIANT"
echo "Control Center: OK"
echo "llama.cpp: $LLAMA_OK"
echo "OpenCode: $OPENCODE_OK"
echo "TurboQuant: $TURBO_STATUS"
echo "Access mode: $ACCESS_MODE"
echo "Install root: $WORKSPACE_ROOT"
echo "Launcher: $WRAPPER_PATH"
if [ -n "$STARTED_CONTROL_CENTER_URL" ]; then
  echo "Control Center URL: $STARTED_CONTROL_CENTER_URL"
else
  echo "Control Center URL: start nije potvrdjen automatski"
fi

if [ "$LLAMA_OK" != "true" ] || [ "$OPENCODE_OK" != "true" ]; then
  echo "Obavezne komponente nisu spremne." >&2
  exit 1
fi
