#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Run ./scripts/setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

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
export DEMO_MODE=true
export PORT

echo "=============================================="
echo " CheckEverything Screenshot Demo Environment"
echo "=============================================="
echo
echo "DEMO_MODE=true (no Gemini API calls for trust analysis)"
echo "Server: http://localhost:${PORT}"
echo
echo "1. Reload extension in chrome://extensions"
echo "2. Extension options → API URL → http://localhost:${PORT}"
echo
echo "Demo pages:"
echo "  Hub          http://localhost:${PORT}/demo"
echo "  ChatGPT mock http://localhost:${PORT}/demo/chatgpt"
echo "  Google mock  http://localhost:${PORT}/demo/google-overview"
echo "  Auto panel   http://localhost:${PORT}/demo/chatgpt?autopen=1"
echo
echo "Screenshot targets → docs/demo/"
echo "  chatgpt-badge.png"
echo "  google-ai-overview-badge.png"
echo "  claim-panel-statuses.png  (use autopen link)"
echo "  options-weights.png       (extension options)"
echo
echo "Press Ctrl+C to stop"
echo

if command -v open >/dev/null 2>&1; then
  open "http://localhost:${PORT}/demo" || true
fi

exec uvicorn backend.server:app --port "$PORT"
