#!/usr/bin/env bash
set -euo pipefail

get_local_ai_control_center_root() {
  if [ -n "${LOCAL_AI_CONTROL_CENTER_HOME:-}" ]; then
    printf '%s\n' "$LOCAL_AI_CONTROL_CENTER_HOME"
    return 0
  fi

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
