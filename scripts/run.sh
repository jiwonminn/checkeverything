#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Virtual environment not found. Run ./scripts/setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if [[ ! -f .env ]]; then
  echo "Missing .env file. Copy .env.example to .env and add GEMINI_API_KEY."
  exit 1
fi

pick_port() {
  local start="${1:-8080}"
  local port="$start"
  while lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; do
    port=$((port + 1))
    if [[ "$port" -gt $((start + 20)) ]]; then
      echo "No free port found near $start" >&2
      exit 1
    fi
  done
  echo "$port"
}

PORT="${PORT:-$(pick_port 8080)}"
echo "→ Starting checkeverything at http://localhost:${PORT}"
if [[ "${DEMO_MODE:-}" == "true" ]]; then
  echo "  DEMO_MODE=true — offline demo responses (no API keys required)"
else
  echo "  Google ADK multi-agent pipeline enabled (USE_ADK=${USE_ADK:-true})"
fi
echo "  Set RELOAD=true for development auto-reload"
echo "  Press Ctrl+C to stop"

if [[ "${RELOAD:-false}" == "true" ]]; then
  uvicorn backend.server:app --reload --port "$PORT"
else
  uvicorn backend.server:app --port "$PORT"
fi
