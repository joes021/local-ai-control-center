#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Local AI Control Center Linux Installer TUI"
echo "Target root: ${INSTALL_ROOT:-$HOME/local-qwen-home}"
echo
exec bash "$SCRIPT_DIR/install.sh"
