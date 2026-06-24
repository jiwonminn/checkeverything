# CheckEverything

**CheckEverything is a Chrome extension that overlays a Trust Score on AI-generated answers and shows which claims are supported, weakly supported, unsupported, or linked to unavailable sources.**

A browser extension that checks AI-generated answers by **extracting claims, checking cited sources, matching claims to source text, and showing a transparent Trust Score** — powered by Google Gemini.

Also includes a multi-agent **code review** mode for ChatGPT code responses and a web UI for PR diffs.

> **Competition submission:** See [`docs/SUBMISSION.md`](docs/SUBMISSION.md) for the one-page summary (problem, architecture, Google technology, demo flow, future work).

## Demo

<p align="center">
  <img src="docs/demo/chatgpt-badge.png" alt="Trust Score badge on ChatGPT" width="45%" />
  <img src="docs/demo/google-ai-overview-badge.png" alt="Trust Score badge on Google AI Overview" width="45%" />
</p>

<p align="center">
  <img src="docs/demo/claim-panel-statuses.png" alt="Claim panel with colored support statuses" width="45%" />
  <img src="docs/demo/options-weights.png" alt="Configurable trust score weights" width="45%" />
</p>

> **Note:** Demo screenshots live in `docs/demo/`. To recapture them, follow [`docs/demo/DEMO_SCRIPT.md`](docs/demo/DEMO_SCRIPT.md) and run `./scripts/check-demo-assets.sh` to verify.

| In 10 seconds | What CheckEverything shows |
| --- | --- |
| Trust Score badge | Overlays on ChatGPT + Google AI Overview |
| Source checks | Reachable? Official domain? |
| Claim evidence | ✓ Supported · ~ Weakly supported · High/Medium/Low confidence |
| Your priorities | Adjustable category weights in extension options |

Optional demo GIF: `docs/demo/trust-score-demo.gif`

```bash
./scripts/demo-screenshots.sh   # recommended for judges — local mock pages, offline
./scripts/check-demo-assets.sh  # verify screenshots exist
```

**Video demo (reliable path):** `./scripts/demo-screenshots.sh` → open `http://localhost:8080/demo` → reload extension → click **Trust Score** on mock ChatGPT. Avoid live ChatGPT/Google for judging — DOM and regional AI Overview vary. Full script: [`docs/demo/DEMO_SCRIPT.md`](docs/demo/DEMO_SCRIPT.md).

## Problem

AI answers often sound confident, but users cannot easily tell whether claims are supported by real sources, citations actually prove what the AI says, information is outdated, or important context is missing.

**Who this helps:** students verifying AI study answers, developers sanity-checking AI Overview summaries, and anyone who needs to see *which claims are backed* before trusting an answer.

## Solution

CheckEverything overlays a **Trust Score** badge on AI responses. Click it to see category scores, checked sources, and claim-level evidence — not just a single number.

Example:

```text
Trust Score: 78%
```

When users click the badge, they can see a detailed breakdown:

| Category | Purpose |
| --- | --- |
| **Claim Support** | Checks whether the main claims are supported by evidence |
| **Source Quality** | Evaluates whether cited sources are reliable |
| **Citation Accuracy** | Checks whether citations actually prove the claims |
| **Freshness** | Flags information that may be outdated |
| **Bias / Missing Context** | Identifies one-sided or incomplete explanations |

## Current Status

**Trust checker (live):** Chrome extension on ChatGPT + Google AI Overview with trust badge, source checks, claim-to-source matching, and configurable score weights.

**Code review (also included):** 5-agent review for code snippets and PR diffs via web UI and ChatGPT code responses.

## Architecture

```mermaid
flowchart TB
  subgraph browser [Chrome Extension]
    CS[Content Script]
    Badge[Trust Score Badge]
    Panel[Detail Panel]
  end

  subgraph platforms [Platforms]
    GPT[ChatGPT]
    GAI[Google AI Overview]
  end

  subgraph api [FastAPI Backend]
    Analyze["/api/analyze"]
    Review["/api/review"]
  end

  subgraph pipeline [Trust Pipeline]
    Claims[Claim Extraction]
    Sources[URL Fetch + Classify]
    Match[Claim-Source Matching]
    Score[Weighted Trust Score]
  end

  subgraph adk_trust [ADK Trust Graph when USE_ADK=true]
    Extract[trust_extractor_agent]
    Matcher[trust_matcher_agent]
  end

  GPT --> CS
  GAI --> CS
  CS --> Badge
  Badge -->|click| Panel
  CS -->|text + urls + weights| Analyze
  CS -->|code| Review
  Analyze --> Claims --> Sources --> Match --> Score
  Analyze -.->|USE_ADK=true| Extract --> Matcher --> Score
  Score --> Panel
```

### Architecture decisions

| Choice | Why |
| --- | --- |
| **Click-to-analyze badge** | No background API calls on every AI page; user controls when to run analysis |
| **Server-side URL fetch** | Citations are checked against real page excerpts, not just link text in the AI answer |
| **Two Gemini calls (trust)** | Call 1: extract claims + category scores. Call 2: match claims to source excerpts. With `USE_ADK=true`, both steps run as ADK `SequentialAgent` (`trust_extractor_agent` → `trust_matcher_agent`) |
| **Heuristic score blending** | Source quality and citation accuracy combine Gemini judgment with reachability and support-label signals |
| **ADK where orchestration helps** | Trust pipeline uses ADK `SequentialAgent` (extract → match) when `USE_ADK=true`; code review uses ADK `ParallelAgent` + coordinator |
| **Demo fallbacks** | `DEMO_MODE` and quota-aware fallbacks keep demos working without API keys or when external sites block fetches |

## Limitations

- **Preliminary analysis, not fact-checking** — scores are credibility signals based on claim structure, source metadata, and excerpt matching.
- **Source extraction** — some sites block requests, require JavaScript, or return incomplete page text.
- **Google AI Overview DOM** — layout changes frequently; detection uses fallback heuristics and may miss some overviews.
- **Claim matching** — compares against fetched excerpts (up to ~8k chars), not full document verification.
- **English-first** — optimized for English AI responses; other languages may vary in quality.

## Current Implementation: 5-Agent Code Review

The current version uses a multi-agent review system to analyze code. Five specialist agents review the submission in parallel, and a coordinator agent synthesizes the final result.

| Agent | Focus |
| --- | --- |
| **Security** | Injection, secrets, unsafe patterns |
| **Correctness** | Bugs, logic errors, edge cases |
| **Readability** | Naming, structure, documentation |
| **Performance** | Inefficiencies, anti-patterns |
| **Test Coverage** | Missing tests, testability |
| **Coordinator** | Synthesizes verdict, score, and action items |

## Google Technology

| Tech | Usage | Why |
| --- | --- | --- |
| **Gemini API** | Structured JSON for trust analysis, claim matching, and all code-review agents | `response_schema` gives reliable scores and findings; fallback model chain handles 429s |
| **Google ADK** | `SequentialAgent` trust graph (extract → match); `ParallelAgent` + coordinator for code review | Native multi-agent orchestration for both primary trust and secondary review paths |
| **Vertex AI** | Optional `GOOGLE_GENAI_USE_VERTEXAI` deployment | Same SDK for GCP projects; no API key in the container |
| **Cloud Run** | `./scripts/deploy-cloudrun.sh` + `Dockerfile` | Single HTTPS endpoint for extension + web UI |
| **Chrome Extension APIs** | MV3 content scripts, `chrome.storage.sync`, service worker proxy | Overlay on ChatGPT/Google without CORS issues on third-party pages |

### Local dev (no API key)

```bash
./scripts/setup.sh
./scripts/dev.sh   # offline demo mode — no Gemini key required
```

Open the printed URL. Use **Load sample** → **Run 5-Agent Review** (code) or **Check Trust Score** (AI Answer tab).

### Live API

```bash
./scripts/setup.sh
cp .env.example .env   # add GEMINI_API_KEY or Vertex credentials
./scripts/run.sh
```

Open the printed URL, then select:

```text
Load sample → Run 5-Agent Review
```

The web UI supports **rotating code samples** (per language), **adjustable agent weights** (code review), and **trust score weights** (AI Answer tab).

### PR Diff Review

Switch to the **PR Diff** tab, then paste `git diff` output or upload a `.diff` file. The system reviews only the changed lines.

### Chrome Extension

```bash
./scripts/run.sh
# Chrome → chrome://extensions → Load unpacked → extension/
```

The extension detects ChatGPT assistant responses and **Google AI Overview** blocks on search pages. Click **Trust Score** to analyze — claim evidence, source checks, and adjustable weights in extension options.

See `extension/README.md`.

### ADK Interactive UI

```bash
adk web adk_agents
```

### Evaluation Harness

```bash
./scripts/eval.sh              # code review + trust eval (offline demo mode)
./scripts/eval.sh --code       # code review only
./scripts/eval.sh --trust      # trust claim-matching eval only
./scripts/eval.sh --live       # live Gemini API for both harnesses
```

### Deploy to Cloud Run

```bash
GCP_PROJECT_ID=your-project ./scripts/deploy-cloudrun.sh
```

## API

### Current Code Review API

**POST** `/api/review` — full review  
**POST** `/api/review/stream` — SSE progress per agent  
**POST** `/api/parse-diff` — preview diff extraction

```json
{
  "submission_type": "diff",
  "diff": "diff --git a/foo.py...",
  "context": "PR #42"
}
```

### Trust Analysis API

**POST** `/api/analyze` — trust and credibility analysis for AI responses (live; used by the extension and web UI)

Optional `weights` object (percentages, normalized server-side if they do not sum to 100):

```json
{
  "text": "AI response text...",
  "urls": ["https://example.com/article"],
  "source": "google_ai_overview",
  "weights": {
    "claim_support": 35,
    "source_quality": 25,
    "citation_accuracy": 25,
    "bias_context": 10,
    "freshness": 5
  }
}
```

Returns claim-level breakdown with category scores. This is a **credibility signal**, not full factual verification.

Example response shape:

```json
{
  "overall_score": 78,
  "categories": {
    "claim_support": {
      "score": 70,
      "summary": "Most claims are supported, but one claim needs stronger evidence."
    },
    "source_quality": {
      "score": 85,
      "summary": "Sources appear mostly reliable."
    },
    "citation_accuracy": {
      "score": 65,
      "summary": "Some citations do not clearly prove the related claims."
    },
    "freshness": {
      "score": 90,
      "summary": "Information appears recent enough for the topic."
    },
    "bias_context": {
      "score": 75,
      "summary": "The answer is mostly balanced but could include more context."
    }
  },
  "claims": [
    {
      "text": "Example factual claim from the AI response.",
      "status": "weakly_supported",
      "matched_source": "https://example.com/article",
      "support_label": "weakly_supported",
      "confidence_level": "medium",
      "confidence_note": "Source is related but does not fully prove the claim.",
      "evidence_note": "The source discusses the topic but does not clearly prove the full claim."
    }
  ],
  "sources": [
    {
      "url": "https://example.com/article",
      "domain": "example.com",
      "reachable": true,
      "title": "Article title",
      "source_quality": "medium",
      "notes": "Reachable source, but authority level is unclear."
    }
  ],
  "source_summary": {
    "sources_checked": 1,
    "reachable_count": 1,
    "primary_official_count": 0,
    "issues": []
  }
}
```

## Product Roadmap

### Shipped (v1)

- Trust Score Chrome extension (ChatGPT + Google AI Overview)
- Claim extraction, source fetch, claim-to-source matching (`/api/analyze`)
- **Google ADK trust pipeline** (`trust_extractor_agent` → `trust_matcher_agent`) when `USE_ADK=true`
- **Trust eval harness** (`eval/trust_samples.json`, `./scripts/eval.sh --trust`)
- Configurable trust score weights (extension + web UI)
- 5-agent code review with Google ADK + Gemini
- Streaming review UI, PR diff upload, Cloud Run deploy path
- Local mock demo pages for reliable judging (`/demo/chatgpt`, `/demo/google-overview`)
- Concurrent citation fetching so blocked sources do not serialize the full trust check

### Next

- Expand trust eval samples beyond vitamin D scenario
- Gemini, Claude, Perplexity adapters
- Analysis history dashboard
- Stronger source fetching (paywalls, topic-specific authority lists)

## Project Structure

```text
├── adk_agents/checkeverything/   # Google ADK trust + code-review graphs
├── backend/                      # API, orchestrator, evaluation
├── extension/                    # Chrome extension
├── eval/                         # Labeled samples (code review + trust)
├── frontend/                     # Streaming web UI + diff upload
├── examples/                     # vulnerable_auth.py, sample_pr.diff
├── Dockerfile                    # Cloud Run container
├── cloudbuild.yaml
└── scripts/                      # setup, run, test, eval, deploy
```

## About

**Jiwon Min** is a student at **York University** building tools at the intersection of AI and software quality. CheckEverything started as a way to make AI answers more transparent — not just a single score, but which claims are backed by sources and which are not.

This repo is a solo project: a **Chrome extension** for Trust Scores on ChatGPT and Google AI Overview, plus a **web app** for multi-agent code review (Google ADK + Gemini). If you’re reviewing the project, start with `./scripts/dev.sh` — it runs fully offline with demo samples.

## License

MIT
