#!/usr/bin/env bash
# Deploy checkeverything to Google Cloud Run
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="checkeverything"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GCP_PROJECT_ID environment variable."
  echo "Example: GCP_PROJECT_ID=my-project ./scripts/deploy-cloudrun.sh"
  exit 1
fi

echo "→ Building and deploying to Cloud Run (project: $PROJECT_ID)"
gcloud config set project "$PROJECT_ID"

gcloud builds submit --config cloudbuild.yaml .

URL=$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)')
echo ""
echo "✓ Deployed: $URL"
echo "  Set GEMINI_API_KEY secret: gcloud secrets create GEMINI_API_KEY --data-file=-"
