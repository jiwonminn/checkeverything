# Demo Video Script (15–25 seconds)

**Recommended for competition judging:** use local mock pages — not live ChatGPT or Google Search. DOM changes and regional AI Overview availability make live sites unreliable.

## Setup (stable path)

```bash
./scripts/setup.sh
./scripts/demo-screenshots.sh
```

1. Chrome → `chrome://extensions` → **Load unpacked** → `extension/` folder
2. Extension **options** → API URL → `http://localhost:8080` (match the port printed by the script)
3. Open `http://localhost:8080/demo`

## Shot list (mock pages)

| # | Time | Action | What viewers should see |
| --- | --- | --- | --- |
| 1 | 0–3s | Open **ChatGPT mock** (`/demo/chatgpt`) | Trust Score badge on vitamin D answer |
| 2 | 3–8s | Click **Trust Score** | 75% score, category table, source summary |
| 3 | 8–14s | Scroll panel | Colored claims: Supported, Weakly supported, Not supported, Source unavailable |
| 4 | 14–18s | Open **Google AI Overview mock** | Badge on search-style overview block |
| 5 | 18–22s | Optional: **Extension options** | API URL + trust score weights |
| 6 | 22–25s | Optional: web UI `localhost:8080` → **AI Answer** tab | Same analysis without extension |

## Voiceover (optional)

> “CheckEverything overlays a Trust Score on AI answers, fetches cited sources, and shows which claims are actually supported — powered by Gemini and Google ADK.”

## Live API segment (optional, needs API key)

```bash
cp .env.example .env   # add GEMINI_API_KEY
DEMO_MODE=false ./scripts/run.sh
```

Repeat the mock-page flow. Response `pipeline` field will be `"gemini"` instead of `"demo"`.

## Export

- GIF: `docs/demo/trust-score-demo.gif` (720p, 15–25s)
- Or host on YouTube/Loom and link from README

## Screenshots (in `docs/demo/`)

| File | Capture |
| --- | --- |
| `chatgpt-badge.png` | ChatGPT mock, badge visible, panel closed |
| `google-ai-overview-badge.png` | Google mock with badge |
| `claim-panel-statuses.png` | Panel open — scores, sources, colored claims |
| `options-weights.png` | Extension options with weight fields |

Verify: `./scripts/check-demo-assets.sh`

## Troubleshooting

| Issue | Fix |
| --- | --- |
| Badge missing on mock page | Reload extension; confirm API URL matches server port |
| `Cannot reach API` error | Start `./scripts/demo-screenshots.sh` or `./scripts/dev.sh` |
| Wrong port | Use `PORT=8080 ./scripts/demo-screenshots.sh` so extension default matches |
| Live ChatGPT has no badge | Use mock pages for demo; live DOM changes frequently |
