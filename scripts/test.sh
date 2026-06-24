#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source .venv/bin/activate

if [[ "${CHECKEVERYTHING_LIVE_TEST:-}" != "true" ]]; then
  export DEMO_MODE=true
fi

echo "→ Testing configuration..."
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('GEMINI_API_KEY', '')
vertex = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', '').lower() in ('1','true','yes')
demo = os.getenv('DEMO_MODE', '').lower() in ('1','true','yes')
adk = os.getenv('USE_ADK', 'true').lower() in ('1','true','yes')
print('  USE_ADK:', adk)
print('  DEMO_MODE:', demo)
print('  Vertex AI:', vertex)
if demo:
    print('  API: skipped (demo mode)')
elif vertex:
  print('  API: Vertex AI project', os.getenv('GOOGLE_CLOUD_PROJECT','(not set)'))
elif key and key != 'your_api_key_here':
  print('  API: Gemini API key loaded')
else:
  print('  API: no credentials — will use demo fallback on errors')
"

echo ""
if [[ "${CHECKEVERYTHING_LIVE_TEST:-}" == "true" ]]; then
  echo "→ Running live review (ADK → Gemini fallback → demo if quota exhausted)..."
else
  echo "→ Running local smoke review (demo mode; set CHECKEVERYTHING_LIVE_TEST=true for live API)..."
fi
python cli.py examples/vulnerable_auth.py --context "Setup test"
