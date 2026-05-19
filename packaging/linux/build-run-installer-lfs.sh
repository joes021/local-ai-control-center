#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERSION="${1:-$(python3 - <<'PY' "$REPO_ROOT/version.json"
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
)}"
TARGET_ARCH="${2:-all}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/dist/linux}"

find_support_repo_root() {
  local env_override sibling
  env_override="${LOCAL_AI_CONTROL_CENTER_SUPPORT_REPO:-}"
  sibling="$(cd "$REPO_ROOT/.." && pwd)/Local Qwen 3.635Ba3B on home computer"

  for candidate in "$env_override" "$sibling"; do
    if [ -n "$candidate" ] && [ -f "$candidate/config/profiles/defaults.json" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

SUPPORT_REPO="$(find_support_repo_root || true)"
if [ -z "$SUPPORT_REPO" ]; then
  echo "Stable support repo nije pronadjen. Postavi LOCAL_AI_CONTROL_CENTER_SUPPORT_REPO." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

build_one() {
  local arch="$1"
  local stage_dir payload_dir payload_tar output_file
  stage_dir="$(mktemp -d)"
  payload_dir="$stage_dir/payload"
  payload_tar="$stage_dir/payload.tar.gz"
  output_file="$OUTPUT_DIR/Local-AI-Control-Center-Setup-linux-${arch}-${VERSION}.run"

  cleanup() {
    rm -rf "$stage_dir"
  }
  trap cleanup RETURN

  mkdir -p "$payload_dir"
  cp "$REPO_ROOT/version.json" "$payload_dir/"
  cp "$REPO_ROOT/README.md" "$payload_dir/"
  cp "$REPO_ROOT/release-notes.txt" "$payload_dir/"
  mkdir -p \
    "$payload_dir/backend" \
    "$payload_dir/frontend" \
    "$payload_dir/launchers" \
    "$payload_dir/legacy-launchers" \
    "$payload_dir/install" \
    "$payload_dir/config" \
    "$payload_dir/assets" \
    "$payload_dir/scripts" \
    "$payload_dir/docs"

  cp -R "$REPO_ROOT/backend/." "$payload_dir/backend/"
  cp -R "$REPO_ROOT/frontend/dist" "$payload_dir/frontend/"
  cp -R "$REPO_ROOT/launchers/." "$payload_dir/launchers/"
  cp -R "$SUPPORT_REPO/launcher/linux/." "$payload_dir/legacy-launchers/"
  cp -R "$REPO_ROOT/install/linux" "$payload_dir/install/"
  cp -R "$REPO_ROOT/install/shared" "$payload_dir/install/"
  cp -R "$SUPPORT_REPO/config/profiles" "$payload_dir/config/"
  cp -R "$SUPPORT_REPO/assets/icons" "$payload_dir/assets/"
  cp -R "$SUPPORT_REPO/scripts/." "$payload_dir/scripts/"
  cp "$REPO_ROOT/run_control_center_next.py" "$payload_dir/"
  printf '%s\n' "$arch" > "$payload_dir/.target-architecture"
  find "$payload_dir" -type f -name "*.sh" -print0 | while IFS= read -r -d '' file; do
    python3 - <<'PY' "$file"
from pathlib import Path
import sys

path = Path(sys.argv[1])
data = path.read_bytes()
normalized = data.replace(b"\r\n", b"\n")
if normalized != data:
    path.write_bytes(normalized)
PY
  done

  cat > "$payload_dir/install.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "${1:-}" = "--tui" ]; then
  shift
  exec bash "$SCRIPT_DIR/install/linux/installer-tui.sh" "$@"
fi
if [ "${1:-}" = "--cli-install" ]; then
  shift
  exec bash "$SCRIPT_DIR/install/linux/install.sh" "$@"
fi
if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ] || [ "${XDG_SESSION_TYPE:-}" = "x11" ] || [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
  if [ -f "$SCRIPT_DIR/install/linux/installer-gui.sh" ]; then
    exec bash "$SCRIPT_DIR/install/linux/installer-gui.sh" "$@"
  fi
fi
exec bash "$SCRIPT_DIR/install/linux/installer-tui.sh" "$@"
EOF
  chmod +x "$payload_dir/install.sh"
  find "$payload_dir" -type f \( -name "*.sh" -o -name "*.run" \) -exec chmod +x {} \;
  tar -C "$payload_dir" -czf "$payload_tar" .

  cat > "$output_file" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

SELF_PATH="$(readlink -f "$0" 2>/dev/null || realpath "$0")"
WORK_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

ARCHIVE_LINE="$(awk '/^__ARCHIVE_BELOW__$/ { print NR + 1; exit }' "$SELF_PATH")"
tail -n +"$ARCHIVE_LINE" "$SELF_PATH" | tar -xz -C "$WORK_DIR"
exec bash "$WORK_DIR/install.sh" "$@"
exit 0
__ARCHIVE_BELOW__
EOF
  cat "$payload_tar" >> "$output_file"
  chmod +x "$output_file"
  printf '%s\n' "$output_file"
}

case "$TARGET_ARCH" in
  all)
    build_one "x86_64"
    build_one "arm64"
    ;;
  x86_64|arm64)
    build_one "$TARGET_ARCH"
    ;;
  *)
    echo "Nepodrzana target arhitektura: $TARGET_ARCH" >&2
    exit 1
    ;;
esac
