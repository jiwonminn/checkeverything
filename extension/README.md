# checkeverything — Chrome Extension

Scores AI-generated code reviews on **ChatGPT** using the checkeverything multi-agent backend.

## Install (Developer Mode)

1. Start the backend: `./scripts/run.sh`
2. Open Chrome → `chrome://extensions`
3. Enable **Developer mode**
4. Click **Load unpacked** → select the `extension/` folder
5. Open extension options → set API URL (default `http://localhost:8080`)

## Usage

1. Ask ChatGPT to review a piece of code
2. Click **Review Score** on the assistant response
3. See overall score, per-agent breakdown, and verdict

## Configure for Cloud Run

Set API URL to your deployed Cloud Run endpoint in extension options.
