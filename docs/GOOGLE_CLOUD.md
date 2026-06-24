# Google Cloud Deployment Guide

CheckEverything runs on **Google Cloud Run** with **Gemini API** (via Secret Manager), **Google ADK** (`USE_ADK=true` in production), and optional **Vertex AI**.

## Stack overview

```text
Developer machine                    Google Cloud
─────────────────                    ────────────
./scripts/deploy-cloudrun.sh  →      Cloud Build (cloudbuild.yaml)
                                     Artifact Registry (Docker image)
                                     Cloud Run (FastAPI + frontend + demo)
                                     Secret Manager (GEMINI_API_KEY)
                                     Gemini API / Vertex AI (inference)

Chrome extension  ──HTTPS──►  Cloud Run /api/analyze
Web UI              ──HTTPS──►  Cloud Run / + /static
```

## Prerequisites

- Google Cloud project with **billing enabled**
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey)
- Local `.env` with at least:

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=northamerica-northeast2   # or us-central1
```

## One-time setup

### 1. Enable APIs (usually automatic on first deploy)

Cloud Build, Cloud Run, Artifact Registry, and Secret Manager are used by `cloudbuild.yaml` and `deploy-cloudrun.sh`.

### 2. IAM for Cloud Build

Run once per project (included in deploy script unless skipped):

```bash
./scripts/setup-cloudrun-iam.sh
```

### 3. Store Gemini API key in Secret Manager

```bash
gcloud config set project YOUR_PROJECT_ID

# Create secret (skip if it already exists)
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Or add a new version to an existing secret
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add GEMINI_API_KEY --data-file=-
```

Cloud Run mounts this at deploy time via `cloudbuild.yaml`:

```yaml
--set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest
```

## Deploy

```bash
./scripts/deploy-cloudrun.sh
```

Output example:

```text
✓ Deployed: https://checkeverything-xxxxx-REGION.run.app
```

Verify:

```bash
curl https://YOUR-SERVICE-URL/health
```

Expected fields: `"status":"ok"`, `"google_technologies":{"gemini_api":true,"google_adk":true}`, `"model":"gemini-2.5-flash-lite"`.

Test analyze:

```bash
curl -X POST https://YOUR-SERVICE-URL/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Vitamin D supports bone health.","urls":[],"source":"chatgpt"}'
```

## Connect the Chrome extension

1. `chrome://extensions` → reload CheckEverything  
2. Extension **Options** → click **Cloud Run** preset (or paste your service URL)  
3. **Test connection** → **Save**  
4. Refresh ChatGPT or open `https://YOUR-SERVICE-URL/demo/chatgpt`

## Optional: Vertex AI instead of API key

In `.env` before deploy (or Cloud Run env vars):

```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

Remove or do not mount `GEMINI_API_KEY` when using Vertex with Application Default Credentials on Cloud Run (requires appropriate service account roles).

Local Vertex test:

```bash
gcloud auth application-default login
GOOGLE_GENAI_USE_VERTEXAI=true DEMO_MODE=false ./scripts/run.sh
```

## What runs in the container

| Component | Path / note |
| --- | --- |
| FastAPI API | `/api/analyze`, `/api/review`, `/health` |
| Web UI | `/` (trust + code review tabs) |
| Mock demos | `/demo`, `/demo/chatgpt`, `/demo/google-overview` |
| ADK trust graph | `USE_ADK=true` → `trust_extractor_agent` → `trust_matcher_agent` |
| Model | `GEMINI_MODEL=gemini-2.5-flash-lite` (configurable) |

## Troubleshooting

| Issue | Fix |
| --- | --- |
| Deploy fails on secret | Create `GEMINI_API_KEY` in Secret Manager; grant Cloud Run service account `secretAccessor` |
| `503` / analysis errors | Check Cloud Run logs; confirm secret is mounted and Gemini quota is available |
| Extension **Cannot reach API** | Extension options → correct Cloud Run URL (https, no trailing path); reload extension |
| CORS / fetch blocked | Extension uses host permissions for `*.run.app`; ensure URL matches deployed region |
| High latency cold start | Cloud Run min instances (optional, costs more) or accept first-request warmup |

## Files reference

| File | Purpose |
| --- | --- |
| `Dockerfile` | Python 3.12 image, uvicorn on `$PORT` |
| `cloudbuild.yaml` | Build → push → deploy to Cloud Run |
| `scripts/deploy-cloudrun.sh` | Wrapper with project/region from `.env` |
| `scripts/setup-cloudrun-iam.sh` | Cloud Build service account permissions |
| `.env.example` | Local and GCP env var template |

## Competition submission note

For the written summary, cite:

- **Gemini API** — structured trust analysis and claim matching  
- **Google ADK** — multi-agent trust + code review orchestration  
- **Cloud Run + Cloud Build + Secret Manager** — production deployment on Google Cloud  
- **Vertex AI** — optional enterprise path (same SDK)

See also [`SUBMISSION.md`](SUBMISSION.md) and the [Competition Submission](../README.md#competition-submission) section in the README.
