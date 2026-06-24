"""Coordinator agent that synthesizes sub-agent findings into one actionable report."""

import json

from google.genai import types

from backend.gemini_client import generate_with_fallback, get_client
from backend.models import AgentFindingReport, ReviewReport
from backend.prompts import COORDINATOR_INSTRUCTION


def run_coordinator(
    code: str,
    language: str,
    context: str,
    agent_reports: list[AgentFindingReport],
) -> ReviewReport:
    client = get_client()
    reports_json = json.dumps([r.model_dump() for r in agent_reports], indent=2)

    user_content = f"""Synthesize a final code review report.

Language: {language}
Submitter context: {context or "None provided."}

Code under review:
```
{code}
```

Sub-agent reports:
{reports_json}
"""
    response = generate_with_fallback(
        client,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=COORDINATOR_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ReviewReport,
            temperature=0.3,
        ),
    )
    return ReviewReport.model_validate_json(response.text)
