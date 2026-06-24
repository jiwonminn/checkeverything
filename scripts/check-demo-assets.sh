#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO_DIR="$ROOT/docs/demo"

REQUIRED=(
  chatgpt-badge.png
  google-ai-overview-badge.png
  claim-panel-statuses.png
  options-weights.png
)

OPTIONAL=(
  trust-score-demo.gif
)

echo "CheckEverything demo assets"
echo "Directory: $DEMO_DIR"
echo

missing=0
for file in "${REQUIRED[@]}"; do
  if [[ -f "$DEMO_DIR/$file" ]]; then
    echo "  ✓ $file"
  else
    echo "  ✗ $file (missing)"
    missing=$((missing + 1))
  fi
done

for file in "${OPTIONAL[@]}"; do
  if [[ -f "$DEMO_DIR/$file" ]]; then
    echo "  ✓ $file (optional)"
  else
    echo "  · $file (optional, not added yet)"
  fi
done

echo
if [[ $missing -eq 0 ]]; then
  echo "All required demo screenshots are present."
else
  echo "$missing required screenshot(s) missing."
  echo "See docs/demo/DEMO_SCRIPT.md for capture instructions."
  exit 1
fi
