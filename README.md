# checkeverything

**5-agent automated code review — Google ADK + Gemini**

checkeverything automates first-pass code review using five Google Gemini specialists and a coordinating agent — built on **Google ADK**, **Gemini API**, and optional **Vertex AI**.

## Five Specialist Agents + Coordinator

| Agent | Focus |
|-------|--------|
| **Security** | Injection, secrets, unsafe patterns |
| **Correctness** | Bugs, logic errors, edge cases |
| **Readability** | Naming, structure, documentation |
| **Performance** | Inefficiencies, anti-patterns |
| **Test Coverage** | Missing tests, testability |
| **Coordinator** | Synthesizes → verdict, score, action items |

## Google Technology

| Tech | Usage |
|------|--------|
| **Google ADK** | `ParallelAgent` (5 specialists) → `SequentialAgent` → Coordinator |
| **Gemini API** | Structured JSON output per agent |
| **Vertex AI** | Optional enterprise path |
| **Cloud Run** | One-command deploy (`./scripts/deploy-cloudrun.sh`) |

## Quick Start

```bash
./scripts/setup.sh
cp .env.example .env   # add GEMINI_API_KEY
./scripts/run.sh
```

Open the printed URL → **Load sample** → **Run 5-Agent Review**

### PR Diff Review

Switch to **PR Diff** tab → paste `git diff` output or upload `.diff` file → review only changed lines.

### Chrome Extension (ChatGPT)

```bash
./scripts/run.sh
# Chrome → chrome://extensions → Load unpacked → extension/
```

Click **Trust Score** on any ChatGPT code review response. See `extension/README.md`.

### ADK Interactive UI

```bash
adk web adk_agents
```

### Evaluation Harness

```bash
./scripts/eval.sh          # offline demo mode
./scripts/eval.sh --live   # live Gemini API
```

### Deploy to Cloud Run

```bash
GCP_PROJECT_ID=your-project ./scripts/deploy-cloudrun.sh
```

## API

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

## Project Structure

```
├── adk_agents/checkeverything/   # Google ADK 5-agent graph
├── backend/                 # API, orchestrator, evaluation
├── extension/               # Chrome extension for ChatGPT
├── eval/                    # Labeled samples for recall metrics
├── frontend/                # Streaming web UI + diff upload
├── examples/                # vulnerable_auth.py, sample_pr.diff
├── Dockerfile               # Cloud Run container
├── cloudbuild.yaml
└── scripts/                 # setup, run, test, eval, deploy
```

## About

Solo project by **Jiwon Min** (York University). Built to explore multi-agent code review with Google ADK — five specialists in parallel, one coordinator, deployable to Cloud Run.

## License

MIT
