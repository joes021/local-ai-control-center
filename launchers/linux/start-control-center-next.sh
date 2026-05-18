#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
VENV_DIR="$ROOT/.venv"
LOCAL_QWEN_HOME_ROOT="${LOCAL_QWEN_HOME:-$ROOT}"
STATE_DIR="$LOCAL_QWEN_HOME_ROOT/state"

LOCAL_HOST="127.0.0.1"
read_runtime_access_mode() {
  "$VENV_DIR/bin/python" - <<'PY' "$STATE_DIR"
import sys
from pathlib import Path
from backend.app.services.runtime_config_service import load_runtime_config

print(load_runtime_config(state_dir=Path(sys.argv[1]))["accessMode"])
PY
}

ACCESS_MODE="${CONTROL_CENTER_NEXT_ACCESS_MODE:-}"
if [ -z "$ACCESS_MODE" ] && [ -x "$VENV_DIR/bin/python" ]; then
  ACCESS_MODE="$(read_runtime_access_mode 2>/dev/null || true)"
fi
ACCESS_MODE="${ACCESS_MODE:-local-only}"
BIND_HOST="${CONTROL_CENTER_NEXT_BIND_HOST:-}"
if [ -z "$BIND_HOST" ]; then
  if [ "$ACCESS_MODE" = "tailscale" ]; then
    BIND_HOST="0.0.0.0"
  else
    BIND_HOST="$LOCAL_HOST"
  fi
fi
START_PORT="${CONTROL_CENTER_NEXT_START_PORT:-3210}"
END_PORT="${CONTROL_CENTER_NEXT_END_PORT:-3299}"
HEALTH_PATH="/api/health"
STATE_FILE="$STATE_DIR/runtime-state.json"
UNIT_NAME="${CONTROL_CENTER_NEXT_UNIT_NAME:-control-center-next}"
SKIP_OPEN="${CONTROL_CENTER_NEXT_SKIP_OPEN:-0}"

mkdir -p "$STATE_DIR"

select_port() {
  "$VENV_DIR/bin/python" - <<'PY' "$START_PORT" "$END_PORT"
from backend.app.port_selection import select_first_free_port
import sys
print(select_first_free_port(int(sys.argv[1]), int(sys.argv[2])))
PY
}

ensure_frontend_build() {
  if [ -f "$FRONTEND_DIR/dist/index.html" ]; then
    return 0
  fi
  echo "Frontend build nije pronadjen. Pokrecem npm run build..."
  (cd "$FRONTEND_DIR" && npm install && npm run build)
}

health_url_for_port() {
  local port="$1"
  printf 'http://%s:%s%s\n' "$LOCAL_HOST" "$port" "$HEALTH_PATH"
}

app_url_for_port() {
  local port="$1"
  printf 'http://%s:%s/\n' "$LOCAL_HOST" "$port"
}

wait_for_health() {
  local url="$1"
  for _ in $(seq 1 30); do
    if curl --silent --fail "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

can_open_browser() {
  if [ "$SKIP_OPEN" = "1" ]; then
    return 1
  fi
  if ! command -v xdg-open >/dev/null 2>&1; then
    return 1
  fi
  [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ] || [ "${XDG_SESSION_TYPE:-}" = "x11" ] || [ "${XDG_SESSION_TYPE:-}" = "wayland" ]
}

read_state_field() {
  local field="$1"
  if [ ! -f "$STATE_FILE" ]; then
    return 1
  fi
  python3 - <<'PY' "$STATE_FILE" "$field"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
field = sys.argv[2]

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)

value = data.get(field)
if value is None:
    raise SystemExit(1)
print(value)
PY
}

reuse_existing_backend() {
  local existing_port
  if ! existing_port="$(read_state_field "port")"; then
    return 1
  fi

  local existing_url
  existing_url="$(app_url_for_port "$existing_port")"
  local existing_health
  existing_health="$(health_url_for_port "$existing_port")"

  if ! curl --silent --fail "$existing_health" >/dev/null 2>&1; then
    return 1
  fi

  echo "Postojeci backend je vec aktivan na: ${existing_url}"
  if can_open_browser; then
    xdg-open "$existing_url" >/dev/null 2>&1 || true
  else
    echo "Automatsko otvaranje browsera nije dostupno u ovom Linux session-u. Otvori rucno: ${existing_url}"
  fi
  return 0
}

start_backend_with_systemd() {
  local port="$1"
  systemctl --user stop "$UNIT_NAME" >/dev/null 2>&1 || true
  systemctl --user reset-failed "$UNIT_NAME" >/dev/null 2>&1 || true
  systemd-run --user --unit "$UNIT_NAME" --same-dir --collect \
    --setenv="CONTROL_CENTER_NEXT_UI_PORT=$port" \
    --setenv="CONTROL_CENTER_NEXT_ACCESS_MODE=$ACCESS_MODE" \
    --setenv="CONTROL_CENTER_NEXT_HOST=$BIND_HOST" \
    --setenv="CONTROL_CENTER_NEXT_FRONTEND_DIST=$FRONTEND_DIR/dist" \
    "$VENV_DIR/bin/python" -m uvicorn backend.app.main:app --host "$BIND_HOST" --port "$port" >/tmp/control-center-next-launch.log
}

start_backend_with_nohup() {
  local port="$1"
  CONTROL_CENTER_NEXT_UI_PORT="$port" \
  CONTROL_CENTER_NEXT_ACCESS_MODE="$ACCESS_MODE" \
  CONTROL_CENTER_NEXT_HOST="$BIND_HOST" \
  CONTROL_CENTER_NEXT_FRONTEND_DIST="$FRONTEND_DIR/dist" \
  nohup setsid "$VENV_DIR/bin/python" -m uvicorn backend.app.main:app --host "$BIND_HOST" --port "$port" >/tmp/control-center-next.log 2>&1 < /dev/null &
  echo "$!"
}

start_backend() {
  local port="$1"
  local method="nohup"
  local pid=""

  if command -v systemd-run >/dev/null 2>&1 && systemctl --user is-active default.target >/dev/null 2>&1; then
    start_backend_with_systemd "$port"
    method="systemd"
  else
    pid="$(start_backend_with_nohup "$port")"
  fi

  if [ "$method" = "systemd" ]; then
    printf '{\n  "port": %s,\n  "unit": "%s",\n  "method": "systemd"\n}\n' "$port" "$UNIT_NAME" > "$STATE_FILE"
  else
    printf '{\n  "port": %s,\n  "pid": %s,\n  "method": "nohup"\n}\n' "$port" "$pid" > "$STATE_FILE"
  fi
}

cd "$ROOT"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install -q -r "$BACKEND_DIR/requirements.txt"
fi

ensure_frontend_build
if reuse_existing_backend; then
  exit 0
fi

SELECTED_PORT="$(select_port)"
CONTROL_CENTER_NEXT_UI_PORT="$SELECTED_PORT"
export CONTROL_CENTER_NEXT_UI_PORT

URL="$(app_url_for_port "$SELECTED_PORT")"
HEALTH_URL="$(health_url_for_port "$SELECTED_PORT")"

echo "Starting Local AI Control Center backend on ${BIND_HOST}."
echo "Preferred port range: ${START_PORT}-${END_PORT}"
echo "Selected port: ${SELECTED_PORT}"
echo "Health check endpoint: ${HEALTH_URL}"

start_backend "$SELECTED_PORT"

if ! wait_for_health "$HEALTH_URL"; then
  echo "Backend nije postao healthy na vreme."
  echo "Otvori rucno: ${URL}"
  exit 1
fi

if can_open_browser; then
  xdg-open "$URL" >/dev/null 2>&1 || true
else
  echo "Automatsko otvaranje browsera nije dostupno u ovom Linux session-u. Otvori rucno: ${URL}"
fi

echo "Control Center Next je dostupan na: ${URL}"
