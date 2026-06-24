#!/usr/bin/env bash
# Local development: offline demo responses, no API keys required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Virtual environment not found. Run ./scripts/setup.sh first."
  exit 1
fi

export DEMO_MODE=true
export USE_ADK=false
export GOOGLE_GENAI_USE_VERTEXAI=false
export RELOAD="${RELOAD:-true}"
# Leave PORT unset so run.sh can auto-pick 8080, 8081, … if busy

echo "→ Dev mode: DEMO_MODE=true (trust + code review work offline)"
echo "→ Server URL printed below (usually http://localhost:8080)"
echo ""

exec ./scripts/run.sh
