#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v zenity >/dev/null 2>&1; then
  zenity --info --title="Local AI Control Center Setup" --text="Pokrece se Linux installer za Local AI Control Center."
fi
exec bash "$SCRIPT_DIR/install.sh"
