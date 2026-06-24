# CheckEverything Chrome Extension

The CheckEverything Chrome extension detects AI-generated responses in ChatGPT and displays a trust score badge directly on the page.

## Current Version

- Detects ChatGPT assistant responses
- **Code responses** (with code blocks) → `/api/review` (5-agent code review)
- **Text responses** (no code blocks) → `/api/analyze` (preliminary credibility analysis)
- Displays a **Trust Score** badge with mode-specific subtitle
- Shows detailed breakdown panel for both modes

> **Note:** Trust analysis is preliminary — it assesses claim structure, citations, and language. Full source verification is planned.

## Planned Direction

- Detect general AI responses automatically
- Extract factual claims and citations
- Score claim support, source quality, citation accuracy, freshness, and missing context
- Support ChatGPT and Google AI results

## Install (Developer Mode)

1. Start the backend: `./scripts/run.sh`
2. Open Chrome → `chrome://extensions`
3. Enable **Developer mode**
4. Click **Load unpacked** → select the `extension/` folder
5. Open extension options → set API URL (default `http://localhost:8080`)

## Usage

1. Ask ChatGPT a question (with or without code)
2. Click **Trust Score** on the assistant response
3. Wait for **Analyzing response…** to complete
4. Click **View Details** to reopen the breakdown panel

Routing:
- Responses with code blocks → code review mode (`/api/review`)
- General text responses → preliminary trust mode (`/api/analyze`)

## Configure for Cloud Run

Set API URL to your deployed Cloud Run endpoint in extension options.
