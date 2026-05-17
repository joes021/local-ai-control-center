#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
ENTRY_NAME="${CONTROL_CENTER_NEXT_ENTRY_NAME:-local-qwen-control-center-next.desktop}"
ENTRY_PATH="$DESKTOP_DIR/$ENTRY_NAME"
PRIMARY_ENTRY_NAME="${CONTROL_CENTER_NEXT_PRIMARY_ENTRY_NAME:-local-qwen-control-center.desktop}"
PRIMARY_ENTRY_PATH="$DESKTOP_DIR/$PRIMARY_ENTRY_NAME"
BACKUP_SUFFIX="${CONTROL_CENTER_NEXT_BACKUP_SUFFIX:-.tui-backup}"
REPLACE_PRIMARY="${CONTROL_CENTER_NEXT_REPLACE_PRIMARY:-1}"
ICON_PATH="${CONTROL_CENTER_NEXT_ICON_PATH:-}"

mkdir -p "$DESKTOP_DIR"

cat >"$ENTRY_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Local AI Control Center
Comment=Pokreni novi Local Qwen web control centar
Exec=$ROOT/launchers/linux/start-control-center-next.sh
Terminal=false
Categories=Development;Utility;
StartupNotify=true
EOF

if [ -n "$ICON_PATH" ]; then
  printf 'Icon=%s\n' "$ICON_PATH" >>"$ENTRY_PATH"
fi

chmod +x "$ENTRY_PATH"

if [ "$REPLACE_PRIMARY" = "1" ]; then
  if [ -f "$PRIMARY_ENTRY_PATH" ] && [ "$PRIMARY_ENTRY_PATH" != "$ENTRY_PATH" ]; then
    cp "$PRIMARY_ENTRY_PATH" "$PRIMARY_ENTRY_PATH$BACKUP_SUFFIX"
  fi
  cp "$ENTRY_PATH" "$PRIMARY_ENTRY_PATH"
  chmod +x "$PRIMARY_ENTRY_PATH"
  echo "Primary desktop entry: $PRIMARY_ENTRY_PATH"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo "Desktop entry: $ENTRY_PATH"
