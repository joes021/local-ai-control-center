#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="${INSTALL_ROOT:-$HOME/local-qwen-home}"
SKIP_DEPENDENCIES="${SKIP_DEPENDENCIES:-0}"
SKIP_OPENCODE_INSTALL="${SKIP_OPENCODE_INSTALL:-0}"
SKIP_LLAMA_SETUP="${SKIP_LLAMA_SETUP:-0}"
SKIP_TURBOQUANT="${SKIP_TURBOQUANT:-0}"
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
    sudo apt-get install -y git curl python3 python3-venv python3-pip nodejs npm
  fi
}

ensure_opencode() {
  if [ "$SKIP_OPENCODE_INSTALL" = "1" ]; then
    return 1
  fi
  if command -v opencode >/dev/null 2>&1; then
    return 0
  fi
  npm install -g opencode-ai >/dev/null 2>&1 || true
  command -v opencode >/dev/null 2>&1
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
  [ -d "$target" ]
}

ensure_turboquant() {
  if [ "$SKIP_TURBOQUANT" = "1" ]; then
    printf 'skipped'
    return 0
  fi
  if [ "$TARGET_ARCH" = "arm64" ] || [ "$HOST_ARCH" = "aarch64" ]; then
    printf 'unsupported'
    return 0
  fi
  if [ -d "$APPS_DIR/llama.cpp-turboquant" ]; then
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
copy_if_exists "$PAYLOAD_ROOT/release-notes.txt" "$APP_ROOT/release-notes.txt"

if ensure_opencode; then
  OPENCODE_OK=true
  OPENCODE_PATH="$(command -v opencode)"
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
  "profile": "balanced",
  "context": 262144,
  "outputTokens": 8192,
  "accessMode": "local-only"
}
EOF

cat > "$RUNTIME_CONFIG_PATH" <<EOF
{
  "accessMode": "local-only"
}
EOF

cat > "$INSTALL_REPORT_PATH" <<EOF
{
  "installRoot": "$WORKSPACE_ROOT",
  "appRoot": "$APP_ROOT",
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
echo "Control Center: OK"
echo "llama.cpp: $LLAMA_OK"
echo "OpenCode: $OPENCODE_OK"
echo "TurboQuant: $TURBO_STATUS"
echo "Install root: $WORKSPACE_ROOT"
echo "Launcher: $WRAPPER_PATH"

if [ "$LLAMA_OK" != "true" ] || [ "$OPENCODE_OK" != "true" ]; then
  echo "Obavezne komponente nisu spremne." >&2
  exit 1
fi
