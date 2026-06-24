# Demo Video Script (15–25 seconds)

Use this flow for a GIF or short screen recording. Keep mouse movement smooth and pause 2–3 seconds on the claim panel.

## Setup

```bash
./scripts/run.sh
# Chrome → chrome://extensions → reload CheckEverything
```

## Suggested demo prompts

Use factual questions **with citations** so claim-to-source matching looks strong. Avoid controversial or breaking-news topics for stable screenshots.

### ChatGPT

Ask one of:

```text
What are the main health benefits of vitamin D? Include sources.
```

```text
What are the latest risks of using AI-generated medical advice? Include sources.
```

### Google Search (AI Overview)

Try searches likely to show an AI Overview:

```text
benefits of vitamin D
```

```text
how does intermittent fasting work
```

## Shot list

| # | Time | Action | What viewers should see |
| --- | --- | --- | --- |
| 1 | 0–3s | Open ChatGPT response with citations | Trust Score badge on the answer |
| 2 | 3–6s | Click **Trust Score** | Overall score + source summary |
| 3 | 6–10s | Scroll the panel | Colored claims + High/Medium/Low confidence labels |
| 4 | 10–14s | Open Google search with AI Overview | AI Overview block with Trust Score badge |
| 5 | 14–18s | Click **Trust Score** on Google | Google AI Overview Trust Check panel |
| 6 | 18–22s | Optional: open extension Options | Custom trust score weights |

## Voiceover (optional)

> “CheckEverything overlays a Trust Score on AI answers, checks cited sources, and shows which claims are actually supported.”

## Export

- GIF: `docs/demo/trust-score-demo.gif` (720p, 15–25s)
- Or link a YouTube/Loom URL in the README Demo section

## Screenshots (save to `docs/demo/`)

| File | Capture |
| --- | --- |
| `chatgpt-badge.png` | ChatGPT answer with Trust Score badge (panel closed) |
| `google-ai-overview-badge.png` | Google AI Overview with badge |
| `claim-panel-statuses.png` | Panel open — scores, sources, colored claims, confidence labels |
| `options-weights.png` | Extension options with weight fields |

Verify: `./scripts/check-demo-assets.sh`

```bash
git add docs/demo/*.png
git commit -m "docs: add demo screenshots"
git push
```
