# CheckEverything — Competition Submission Summary

**Jiwon Min · York University · Solo project**

## Problem

AI assistants (ChatGPT, Google AI Overview) answer questions with confident prose and citations, but users cannot easily tell:

- which factual claims are actually supported by cited sources
- whether a citation is reachable, authoritative, or even relevant
- when an answer overstates what the evidence supports

This matters for **students** checking study material, **developers** evaluating AI-generated health or policy summaries, and **anyone** deciding whether to trust an answer before acting on it.

CheckEverything targets that gap with a **transparent Trust Score** and **claim-level evidence** — not a black-box verdict.

## Architecture decisions

| Decision | Rationale |
| --- | --- |
| **Chrome extension overlay** | Meets users where AI answers already appear; click-to-analyze avoids auto-running on every page load |
| **Two-stage trust pipeline** | Stage 1: extract claims + category scores. Stage 2: match claims to source excerpts. Implemented as direct Gemini calls or **Google ADK `SequentialAgent`** when `USE_ADK=true` |
| **Heuristic blending** | Gemini scores for source quality and citation accuracy are blended with server-side signals (reachability, domain authority, support labels) so scores reflect both LLM judgment and observable evidence |
| **Source fetch before LLM** | URLs are fetched server-side (title, excerpt, quality tier) so Gemini reasons over real page text, not just link labels |
| **Demo fallbacks** | `DEMO_MODE` and quota-aware fallbacks keep demos and judging reliable when API keys or external sites fail |
| **5-agent code review (ADK)** | Secondary product: Google ADK `ParallelAgent` runs five specialists, then a coordinator synthesizes a developer-actionable report |
| **FastAPI + static frontend** | Single deployable service (local, Cloud Run) shared by extension, web UI, and mock demo pages |

## Google technology used (and why)

| Technology | Role | Why this choice |
| --- | --- | --- |
| **Gemini API** | Structured JSON for trust analysis, claim matching, and all code-review agents | Native `response_schema` for reliable category scores, claims, and findings; model fallback chain handles rate limits |
| **Google ADK** | Trust `SequentialAgent` (extract → match) + code review `ParallelAgent` + coordinator | Multi-agent orchestration for both primary trust and secondary review paths |
| **Vertex AI** | Optional enterprise deployment | Same `google-genai` client; switch via env for GCP projects without exposing API keys |
| **Cloud Run** | Production backend (`Dockerfile`, `cloudbuild.yaml`) | Stateless FastAPI container; extension points to one HTTPS endpoint |
| **Chrome Extension (MV3)** | Content scripts on ChatGPT + Google Search | `chrome.storage.sync` for API URL and weights; service worker proxies requests to avoid CORS on AI sites |

## What works today

1. **Trust checker (primary)** — Chrome extension on ChatGPT and Google AI Overview; web UI **AI Answer** tab; `/api/analyze`
2. **Code review (secondary)** — 5-agent ADK/Gemini review; streaming web UI; PR diff upload; `/api/review`
3. **Reliable demo** — Local mock pages at `/demo/chatgpt` and `/demo/google-overview` with offline canned analysis (no live ChatGPT/Google login required)
4. **Eval harnesses** — `./scripts/eval.sh --trust` measures claim-support recall on labeled samples

## Recommended demo flow (judges / video)

```bash
./scripts/setup.sh
./scripts/demo-screenshots.sh
# Chrome → chrome://extensions → Load unpacked → extension/
# Extension options → API URL → http://localhost:8080
# Open http://localhost:8080/demo → ChatGPT mock → click Trust Score
```

Use **local mock pages** for the video — not live ChatGPT or Google Search — to avoid DOM changes and regional AI Overview availability.

For **live Gemini** (optional segment): set `GEMINI_API_KEY` in `.env`, run `./scripts/run.sh`, repeat the same mock flow or use the web UI **AI Answer** tab.

## Evaluation alignment

| Criterion | How CheckEverything addresses it |
| --- | --- |
| **Technical depth (35%)** | Multi-stage trust pipeline, concurrent source fetching, claim-to-excerpt matching, weighted scoring, ADK trust + code review graphs, 57+ unit tests, trust eval harness |
| **Google technology (20%)** | Gemini structured output throughout; ADK trust + code review graphs; Vertex + Cloud Run; Chrome extension |
| **Demo reliability (25%)** | Offline demo mode, mock pages, screenshot assets, graceful API fallbacks, `pipeline` field exposes demo vs live |
| **Real-world applicability (10%)** | Actionable claim list with support labels; adjustable category weights; clear limitations (preliminary, not fact-checking) |
| **Clarity (10%)** | README architecture diagram, this summary, demo script, structured panel UI |

## What I would improve with more time

1. **More trust eval samples** — Expand `eval/trust_samples.json` beyond the vitamin D scenario
2. **Caching + latency** — Cache fetched sources; parallelize safe Gemini steps
3. **More platforms** — Gemini app, Perplexity, Claude via shared content-script adapters
4. **History dashboard** — Save past analyses for students and researchers
5. **Stronger source fetching** — Readability extraction, paywall detection, official-domain allowlists per topic

## Repository

- **GitHub:** [github.com/jiwonminn/checkeverything](https://github.com/jiwonminn/checkeverything)
- **All commits:** within the official competition window (from June 17, 2026)

## Video demo checklist

- [ ] Show Trust Score badge on mock ChatGPT answer
- [ ] Open panel — overall score, categories, sources, colored claims
- [ ] Show Google AI Overview mock (optional 5s)
- [ ] Mention: Gemini + Google ADK + Cloud Run + Chrome extension
- [ ] 15–25 seconds total; see [`docs/demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md)
