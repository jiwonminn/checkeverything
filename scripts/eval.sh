#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
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
