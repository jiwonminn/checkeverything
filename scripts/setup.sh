#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "→ Creating virtual environment..."
python3 -m venv .venv

echo "→ Activating venv and installing dependencies..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  echo "→ Creating .env from template..."
  cp .env.example .env
  echo ""
  echo "⚠️  Add your Gemini API key to .env before running reviews."
  echo "   Get one at: https://aistudio.google.com/apikey"
  echo "   Valid keys usually start with: AIza"
else
  echo "→ .env already exists"
fi

echo ""
echo "✓ Setup complete."
echo "  Local testing:  ./scripts/dev.sh"
echo "  Run tests:      ./scripts/test.sh"
echo "  Live API mode:  copy .env.example → .env and set GEMINI_API_KEY or Vertex credentials"
