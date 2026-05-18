#!/usr/bin/env bash
set -euo pipefail

get_local_qwen_root() {
  if [ -n "${LOCAL_QWEN_HOME:-}" ]; then
    printf '%s\n' "$LOCAL_QWEN_HOME"
    return 0
  fi

  if [ -d "$HOME/local-ai-control-center" ]; then
    printf '%s\n' "$HOME/local-ai-control-center"
    return 0
  fi

  printf '%s\n' "$HOME/local-qwen-home"
}
