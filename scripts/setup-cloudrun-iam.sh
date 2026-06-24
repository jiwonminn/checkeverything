#!/usr/bin/env bash
# One-time IAM setup for Cloud Build → Cloud Run deploy on new GCP projects.
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

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GOOGLE_CLOUD_PROJECT in .env first."
  exit 1
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "→ Configuring IAM for Cloud Build deploy"
echo "  project:        $PROJECT_ID"
echo "  project number: $PROJECT_NUMBER"
echo "  region:         $REGION"

gcloud services enable artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
  --project="$PROJECT_ID" >/dev/null

gcloud artifacts repositories describe checkeverything --location="$REGION" --project="$PROJECT_ID" \
  >/dev/null 2>&1 || \
gcloud artifacts repositories create checkeverything \
  --repository-format=docker \
  --location="$REGION" \
  --project="$PROJECT_ID" \
  --description="CheckEverything container images"

bind_role() {
  local member="$1"
  local role="$2"
  echo "  + $role → $member"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="$member" \
    --role="$role" \
    --quiet >/dev/null
}

for sa in "$CLOUDBUILD_SA" "$COMPUTE_SA"; do
  bind_role "serviceAccount:${sa}" "roles/artifactregistry.writer"
  bind_role "serviceAccount:${sa}" "roles/logging.logWriter"
  bind_role "serviceAccount:${sa}" "roles/storage.admin"
  bind_role "serviceAccount:${sa}" "roles/run.admin"
  bind_role "serviceAccount:${sa}" "roles/iam.serviceAccountUser"
  bind_role "serviceAccount:${sa}" "roles/secretmanager.secretAccessor"
done

echo ""
echo "✓ Cloud Build IAM ready. Run ./scripts/deploy-cloudrun.sh"
