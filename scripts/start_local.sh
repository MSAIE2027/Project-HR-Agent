#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_TRANSPORT_OVERRIDE="${MSAIE_MCP_TRANSPORT:-}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi
if [[ -n "$MCP_TRANSPORT_OVERRIDE" ]]; then
  export MSAIE_MCP_TRANSPORT="$MCP_TRANSPORT_OVERRIDE"
fi

HOST="${MSAIE_HOST:-127.0.0.1}"
PORT="${MSAIE_PORT:-8000}"
BROWSER_HOST="${MSAIE_BROWSER_HOST:-127.0.0.1}"
LOG_DIR="${MSAIE_LOG_DIR:-$ROOT_DIR/.logs}"
LOG_FILE="$LOG_DIR/msaie-local.log"
PID_FILE="$LOG_DIR/msaie-local.pid"
DETACH=0
OPEN_BROWSER=1

usage() {
  cat <<'EOF'
Usage: scripts/start_local.sh [--detach] [--no-browser]

Starts the local FastAPI app, waits for /health/ready, opens the browser, and streams
backend logs. The default local MCP transport is in-process; set
MSAIE_MCP_TRANSPORT=stdio when you explicitly want the MCP subprocess boundary.

Environment overrides: MSAIE_HOST, MSAIE_PORT, MSAIE_BROWSER_HOST,
MSAIE_LOG_DIR, MSAIE_PYTHON, MSAIE_MCP_TRANSPORT,
MSAIE_STARTUP_TIMEOUT_SECONDS. OpenRouter defaults are
MSAIE_LLM_BASE_URL=https://openrouter.ai/api/v1 and
MSAIE_LLM_FALLBACK_MODEL=openrouter/free, after the pinned Qwen, Nemotron Lightning,
and Gemma models. Set MSAIE_LLM_API_KEY (or legacy
OPENROUTER_API_KEY) in .env.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --detach) DETACH=1 ;;
    --no-browser) OPEN_BROWSER=0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [[ -z "${MSAIE_LLM_API_KEY:-${OPENROUTER_API_KEY:-}}" ]]; then
  echo "OpenRouter response generation is required. Set MSAIE_LLM_API_KEY (or legacy OPENROUTER_API_KEY) in .env." >&2
  exit 1
fi

if [[ -n "${MSAIE_PYTHON:-}" ]]; then
  PYTHON_BIN="$MSAIE_PYTHON"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "Python 3 was not found. Create .venv and install requirements.txt first." >&2
  exit 1
fi

if ! "$PYTHON_BIN" -c 'import fastapi, uvicorn' >/dev/null 2>&1; then
  echo "FastAPI/Uvicorn are not installed for $PYTHON_BIN." >&2
  echo "Run: $PYTHON_BIN -m pip install -r $ROOT_DIR/requirements.txt" >&2
  exit 1
fi

mkdir -p "$LOG_DIR"

URL="http://${BROWSER_HOST}:${PORT}/"
HEALTH_URL="http://${BROWSER_HOST}:${PORT}/health/ready"
APP_MARKER="MSAIE HR Agent"

if command -v curl >/dev/null 2>&1 && curl --fail --silent --show-error "$HEALTH_URL" >/dev/null 2>&1; then
  running_page="$(curl --fail --silent --show-error "$URL" || true)"
  if ! grep -q "$APP_MARKER" <<<"$running_page"; then
    echo "Port $PORT is serving a different or older application." >&2
    echo "Use MSAIE_PORT=8001 scripts/start_local.sh or stop the process using port $PORT." >&2
    exit 1
  fi
  echo "Current MSAIE build is already running at $URL"
  if [[ "$OPEN_BROWSER" == "1" ]]; then
    if command -v open >/dev/null 2>&1; then open "$URL"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 & fi
  fi
  exit 0
fi

export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export MSAIE_MCP_TRANSPORT="${MSAIE_MCP_TRANSPORT:-inprocess}"

echo "Starting MSAIE from $ROOT_DIR"
echo "MCP transport: $MSAIE_MCP_TRANSPORT"
echo "Log file: $LOG_FILE"

if [[ "$DETACH" == "1" ]]; then
  nohup bash -c 'cd "$1" && exec "$2" -m uvicorn app.main:app --host "$3" --port "$4"' \
    _ "$ROOT_DIR" "$PYTHON_BIN" "$HOST" "$PORT" >>"$LOG_FILE" 2>&1 < /dev/null &
else
  (
    cd "$ROOT_DIR"
    exec "$PYTHON_BIN" -m uvicorn app.main:app --host "$HOST" --port "$PORT"
  ) >>"$LOG_FILE" 2>&1 &
fi
APP_PID=$!
printf '%s\n' "$APP_PID" >"$PID_FILE"
if [[ "$DETACH" == "1" ]]; then
  disown "$APP_PID" 2>/dev/null || true
fi

cleanup() {
  if [[ "$DETACH" == "0" ]] && kill -0 "$APP_PID" >/dev/null 2>&1; then
    echo
    echo "Stopping MSAIE (PID $APP_PID)..."
    kill "$APP_PID" >/dev/null 2>&1 || true
    wait "$APP_PID" >/dev/null 2>&1 || true
  fi
  if [[ "$DETACH" == "0" ]]; then
    rm -f "$PID_FILE"
  fi
}
trap cleanup EXIT INT TERM

STARTUP_TIMEOUT_SECONDS="${MSAIE_STARTUP_TIMEOUT_SECONDS:-180}"
if ! [[ "$STARTUP_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]]; then
  echo "MSAIE_STARTUP_TIMEOUT_SECONDS must be a positive integer." >&2
  exit 2
fi
MAX_STARTUP_ATTEMPTS=$((STARTUP_TIMEOUT_SECONDS * 2))

ready=0
for ((attempt = 1; attempt <= MAX_STARTUP_ATTEMPTS; attempt++)); do
  if command -v curl >/dev/null 2>&1 && curl --fail --silent --show-error "$HEALTH_URL" >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! kill -0 "$APP_PID" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if [[ "$ready" != "1" ]]; then
  echo "MSAIE did not become healthy at $HEALTH_URL" >&2
  tail -n 80 "$LOG_FILE" >&2 || true
  exit 1
fi

echo "MSAIE is ready at $URL"
echo "Health: $HEALTH_URL"
echo "Press Ctrl-C to stop the local service."

if [[ "$OPEN_BROWSER" == "1" ]]; then
  if command -v open >/dev/null 2>&1; then
    open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
  else
    echo "Open $URL in a browser."
  fi
fi

if [[ "$DETACH" == "1" ]]; then
  echo "Detached. Stop it with: scripts/stop_local.sh"
  trap - EXIT INT TERM
  exit 0
fi

tail -n 40 -f "$LOG_FILE"
