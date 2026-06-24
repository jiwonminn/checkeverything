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

RUN_CODE=true
RUN_TRUST=true
FILTERED=()

for arg in "$@"; do
  case "$arg" in
    --code) RUN_TRUST=false ;;
    --trust) RUN_CODE=false ;;
    *) FILTERED+=("$arg") ;;
  esac
done

if [[ "$RUN_CODE" == true ]]; then
  if ((${#FILTERED[@]})); then
    python -m backend.evaluation "${FILTERED[@]}"
  else
    python -m backend.evaluation
  fi
  echo
fi

if [[ "$RUN_TRUST" == true ]]; then
  if ((${#FILTERED[@]})); then
    python -m backend.trust_evaluation "${FILTERED[@]}"
  else
    python -m backend.trust_evaluation
  fi
fi
