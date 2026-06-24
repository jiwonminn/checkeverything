#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source .venv/bin/activate

export DEMO_MODE=true
export USE_ADK=false

echo "→ Unit + API tests (demo mode, no live Gemini required)"
pytest tests/ -v --tb=short
