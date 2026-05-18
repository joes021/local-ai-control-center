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
LEGACY_LAUNCHERS_DIR="$WORKSPACE_ROOT/launchers"
LEGACY_LAUNCHERS_PAYLOAD_DIR="$PAYLOAD_ROOT/legacy-launchers"
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

detect_healthy_runtime_port() {
  local port
  for port in 8091 8081 8080; do
    if curl --silent --fail "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
      printf '%s\n' "$port"
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
copy_dir_content "$LEGACY_LAUNCHERS_PAYLOAD_DIR" "$LEGACY_LAUNCHERS_DIR"
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
TURBO_BIN=""
for candidate in \
  "$APPS_DIR/llama.cpp-turboquant/build-cuda/bin/llama-server" \
  "$APPS_DIR/llama.cpp-turboquant/build-cuda/llama-server"
do
  if [ -x "$candidate" ]; then
    TURBO_BIN="$candidate"
    break
  fi
done
HEALTHY_RUNTIME_PORT="$(detect_healthy_runtime_port || true)"
WRAPPER_PATH="$(write_launcher_wrapper)"
write_desktop_entry "$WRAPPER_PATH"
STARTED_CONTROL_CENTER_URL=""

python3 - <<'PY' "$INSTALL_STATE_PATH" "$SETTINGS_PATH" "$WORKSPACE_ROOT" "$PROFILE" "$ACCESS_MODE" "$OPENCODE_WORKSPACE_DIR" "$LLAMA_BIN" "$TURBO_BIN" "$HEALTHY_RUNTIME_PORT"
import json, os, subprocess, sys
from pathlib import Path

install_state_path = Path(sys.argv[1])
settings_path = Path(sys.argv[2])
workspace_root = Path(sys.argv[3])
profile = sys.argv[4]
access_mode = sys.argv[5]
opencode_workspace = sys.argv[6]
llama_bin = sys.argv[7]
turbo_bin = sys.argv[8]
healthy_runtime_port = sys.argv[9].strip()

def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

existing_state = load_json(install_state_path)
existing_settings = load_json(settings_path)

def detect_process_runtime(port_hint: str) -> tuple[str, str]:
    try:
        completed = subprocess.run(["ps", "-ef"], capture_output=True, text=True, check=False)
    except OSError:
        return "", ""
    for line in completed.stdout.splitlines():
        if "llama-server" not in line:
            continue
        if port_hint and f"--port {port_hint}" not in line and f":{port_hint}" not in line:
            continue
        tokens = line.split()
        exe = next((token for token in tokens if token.endswith("llama-server")), "")
        model = ""
        for idx, token in enumerate(tokens[:-1]):
            if token == "-m":
                model = tokens[idx + 1]
                break
        if exe or model:
            return exe, model
    return "", ""

detected_exe, detected_model = detect_process_runtime(healthy_runtime_port)
models_dir = workspace_root / "models"
preferred_model = models_dir / "qwen36-35b-a3b-IQ2_M.gguf"

model_file = str(existing_state.get("modelFile") or "").strip()
if not model_file and detected_model:
    model_file = detected_model
if not model_file and preferred_model.is_file():
    model_file = str(preferred_model)
if not model_file and models_dir.is_dir():
    ggufs = sorted((path for path in models_dir.glob("*.gguf") if path.is_file()), key=lambda p: p.stat().st_size, reverse=True)
    if ggufs:
        model_file = str(ggufs[0])

model_id = str(existing_state.get("modelId") or "").strip()
if model_id in {"", "none"} and model_file:
    model_id = Path(model_file).name
if not model_id:
    model_id = "none"

runtime_port = int(existing_state.get("port") or 0) if str(existing_state.get("port") or "").isdigit() else 0
if healthy_runtime_port:
    runtime_port = int(healthy_runtime_port)
if runtime_port <= 0:
    runtime_port = 8091

llama_server_exe = str(existing_state.get("llamaServerExe") or "").strip()
if not llama_server_exe and detected_exe:
    llama_server_exe = detected_exe
if not llama_server_exe and llama_bin and Path(llama_bin).exists():
    llama_server_exe = llama_bin

turbo_server_exe = str(existing_state.get("turboServerExe") or "").strip()
if not turbo_server_exe and turbo_bin and Path(turbo_bin).exists():
    turbo_server_exe = turbo_bin

settings = {
    "edition": existing_settings.get("edition", "unified"),
    "profile": profile or str(existing_settings.get("profile", "balanced") or "balanced"),
    "accessMode": access_mode or str(existing_settings.get("accessMode", "local-only") or "local-only"),
    "llama": {
        "contextSize": int(existing_settings.get("llama", {}).get("contextSize", 262144) or 262144),
        "maxOutputTokens": int(existing_settings.get("llama", {}).get("maxOutputTokens", 8192) or 8192),
        "contextSizeCustomized": bool(existing_settings.get("llama", {}).get("contextSizeCustomized", False)),
        "maxOutputTokensCustomized": bool(existing_settings.get("llama", {}).get("maxOutputTokensCustomized", False)),
    },
    "opencode": {
        "buildSteps": int(existing_settings.get("opencode", {}).get("buildSteps", 120) or 120),
        "planSteps": int(existing_settings.get("opencode", {}).get("planSteps", 80) or 80),
        "generalSteps": int(existing_settings.get("opencode", {}).get("generalSteps", 100) or 100),
        "exploreSteps": int(existing_settings.get("opencode", {}).get("exploreSteps", 60) or 60),
        "workingDirectory": str(existing_settings.get("opencode", {}).get("workingDirectory", opencode_workspace) or opencode_workspace),
    },
    "threads": int(existing_settings.get("threads", 8) or 8),
    "gpuLayers": int(existing_settings.get("gpuLayers", 99) or 99),
    "batch": int(existing_settings.get("batch", 2048) or 2048),
    "ubatch": int(existing_settings.get("ubatch", 512) or 512),
    "temperature": float(existing_settings.get("temperature", 0.7) or 0.7),
    "topP": float(existing_settings.get("topP", 0.95) or 0.95),
    "minP": float(existing_settings.get("minP", 0.05) or 0.05),
    "topK": int(existing_settings.get("topK", 40) or 40),
}

install_state = {
    "edition": existing_state.get("edition", "unified"),
    "profile": profile or str(existing_state.get("profile", "balanced") or "balanced"),
    "modelId": model_id,
    "modelFile": model_file,
    "port": runtime_port,
    "llamaServerExe": llama_server_exe,
    "turboServerExe": turbo_server_exe,
    "threads": int(existing_state.get("threads", settings["threads"]) or settings["threads"]),
    "installRoot": str(workspace_root),
    "noMmap": bool(existing_state.get("noMmap", False)),
    "mlock": bool(existing_state.get("mlock", False)),
}

install_state_path.write_text(json.dumps(install_state, ensure_ascii=False, indent=2), encoding="utf-8")
settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
PY

cat > "$RUNTIME_CONFIG_PATH" <<EOF
{
  "accessMode": "$ACCESS_MODE"
}
EOF

if [ -x "$LEGACY_LAUNCHERS_DIR/start-server.sh" ] && [ -s "$INSTALL_STATE_PATH" ]; then
  MODEL_FILE="$(python3 - <<'PY' "$INSTALL_STATE_PATH"
import json, sys
print(json.loads(open(sys.argv[1], 'r', encoding='utf-8').read()).get('modelFile', ''))
PY
)"
  if [ -n "$MODEL_FILE" ] && [ ! -n "$HEALTHY_RUNTIME_PORT" ]; then
    bash "$LEGACY_LAUNCHERS_DIR/start-server.sh" "$PROFILE" >/dev/null 2>&1 || true
    HEALTHY_RUNTIME_PORT="$(detect_healthy_runtime_port || true)"
  fi
fi

if [ -n "$HEALTHY_RUNTIME_PORT" ]; then
  cat > "$STATE_DIR/server-lifecycle.json" <<EOF
{
  "state": "active",
  "profile": "$PROFILE",
  "stdout": "",
  "stderr": "",
  "reason": "Health endpoint returned OK.",
  "updatedAt": "$(date +%Y-%m-%dT%H:%M:%S)"
}
EOF
else
  rm -f "$STATE_DIR/server-lifecycle.json"
fi

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
    "turboQuantRuntime": { "ok": $( [ "$TURBO_STATUS" = "present" ] && echo true || echo false ), "status": "$TURBO_STATUS", "path": "$TURBO_BIN" }
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
