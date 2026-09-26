#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="${MSAIE_LOG_DIR:-$ROOT_DIR/.logs}"
PID_FILE="$LOG_DIR/msaie-local.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No MSAIE PID file found at $PID_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" >/dev/null 2>&1; then
  kill "$PID"
  echo "Stopped MSAIE (PID $PID)."
else
  echo "MSAIE process $PID is no longer running."
fi

rm -f "$PID_FILE"
