# CheckEverything Chrome Extension

The CheckEverything Chrome extension detects AI-generated responses on **ChatGPT** and **Google AI Overview** and displays a trust score badge directly on the page.

## Current Version

- **ChatGPT** assistant responses
  - Code blocks → `/api/review` (5-agent code review)
  - Text answers → `/api/analyze` (preliminary credibility analysis)
- **Google Search AI Overview**
  - Detects AI Overview containers on `google.com/search`
  - Extracts overview text + cited links
  - Sends to `/api/analyze` with `source: google_ai_overview`
- Displays a **Trust Score** badge (click to analyze — never auto-runs)
- Shows detailed breakdown with claim-to-source evidence

> **Note:** Google AI Overview DOM changes frequently. Detection uses multiple fallback signals and fails safely if no overview is found.

## Install (Developer Mode)

1. Start the backend: `./scripts/run.sh`
2. Open Chrome → `chrome://extensions`
3. Enable **Developer mode**
4. Click **Load unpacked** → select the `extension/` folder
5. Open extension options → set API URL (default `http://localhost:8080`)

## Usage

### ChatGPT
1. Ask ChatGPT a question (with or without code)
2. Click **Trust Score** on the assistant response

### Google AI Overview
1. Search on Google until an **AI Overview** appears
2. Click **Trust Score** on the overview block
3. Panel subtitle: **Google AI Overview Trust Check**

## Configure for Cloud Run

Set API URL to your deployed Cloud Run endpoint in extension options.
