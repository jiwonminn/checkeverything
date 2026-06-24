#!/usr/bin/env bash
# Deploy checkeverything to Google Cloud Run
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PROJECT_ID="${GCP_PROJECT_ID:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${GCP_REGION:-${GOOGLE_CLOUD_LOCATION:-us-central1}}"
SERVICE="checkeverything"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GOOGLE_CLOUD_PROJECT in .env or GCP_PROJECT_ID in the environment."
  echo "Example .env line: GOOGLE_CLOUD_PROJECT=my-gcp-project"
  exit 1
fi

echo "→ Building and deploying to Cloud Run"
echo "  project: $PROJECT_ID"
echo "  region:  $REGION"
gcloud config set project "$PROJECT_ID"

if [[ "${SKIP_CLOUDRUN_IAM:-}" != "true" ]]; then
  echo "→ Ensuring Cloud Build IAM (run once per project; set SKIP_CLOUDRUN_IAM=true to skip)"
  SKIP_CLOUDRUN_IAM=true ./scripts/setup-cloudrun-iam.sh
fi

gcloud builds submit --config cloudbuild.yaml . --substitutions="_REGION=${REGION}"

URL=$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)')
echo ""
echo "✓ Deployed: $URL"
echo ""
echo "Next steps:"
echo "  1. Ensure Secret Manager has GEMINI_API_KEY (Cloud Run mounts it automatically)"
echo "  2. Extension options → API URL → $URL"
echo "  3. Test: curl $URL/health"
