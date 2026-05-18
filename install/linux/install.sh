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
  if [ "$SKIP_LLAMA_SETUP" = "1" ]; then
    return 1
  fi
  local target="$APPS_DIR/llama.cpp"
  if [ -x "$target/build/bin/llama-server" ]; then
    return 0
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

cat > "$INSTALL_STATE_PATH" <<EOF
{
  "edition": "$INSTALL_VARIANT",
  "profile": "balanced",
  "modelId": "${SKIP_MODEL_DOWNLOAD:+none}",
  "modelFile": "",
  "port": 8091,
  "llamaServerExe": "$( [ -e "$LLAMA_BIN" ] && printf '%s' "$LLAMA_BIN" )",
  "turboServerExe": ""
}
EOF

cat > "$SETTINGS_PATH" <<EOF
{
  "edition": "$INSTALL_VARIANT",
  "profile": "$PROFILE",
  "context": 262144,
  "outputTokens": 8192,
  "accessMode": "$ACCESS_MODE"
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

echo "Install report:"
echo "Edition: $INSTALL_VARIANT"
echo "Control Center: OK"
echo "llama.cpp: $LLAMA_OK"
echo "OpenCode: $OPENCODE_OK"
echo "TurboQuant: $TURBO_STATUS"
echo "Access mode: $ACCESS_MODE"
echo "Install root: $WORKSPACE_ROOT"
echo "Launcher: $WRAPPER_PATH"

if [ "$LLAMA_OK" != "true" ] || [ "$OPENCODE_OK" != "true" ]; then
  echo "Obavezne komponente nisu spremne." >&2
  exit 1
fi
