#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:3210}"
curl --silent --fail "${BASE_URL}/api/health" >/dev/null
