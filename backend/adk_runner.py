"""Run checkeverything through Google ADK (Parallel + Sequential multi-agent pattern)."""

import uuid

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from google.genai import errors as genai_errors

from adk_agents.checkeverything.agent import root_agent
from backend.models import ReviewReport


def _build_user_message(code: str, language: str, context: str) -> types.Content:
    text = f"""Review this {language} code submission.

Context: {context or "None provided."}

```
{code}
```
"""
    return types.Content(role="user", parts=[types.Part(text=text)])


def _extract_report(session) -> ReviewReport | None:
    state = session.state or {}
    final = state.get("final_report")
    if final is None:
        return None
    if isinstance(final, dict):
        return ReviewReport.model_validate(final)
    if isinstance(final, str):
        return ReviewReport.model_validate_json(final)
    return ReviewReport.model_validate(final)


def review_code_with_adk(code: str, language: str = "python", context: str = "") -> ReviewReport:
    """Execute the ADK root_agent: parallel specialists → coordinator."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="checkeverything",
        session_service=session_service,
        auto_create_session=True,
    )
    session_id = str(uuid.uuid4())
    user_id = "checkeverything_user"

    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=_build_user_message(code, language, context),
    ):
        if event.is_final_response() and event.author == "coordinator_agent":
            if event.content and event.content.parts:
                text = "".join(
                    p.text for p in event.content.parts if p.text and not p.thought
                )
                if text.strip():
                    return ReviewReport.model_validate_json(text)

    session = session_service.get_session_sync(
        app_name="checkeverything",
        user_id=user_id,
        session_id=session_id,
    )
    if session:
        report = _extract_report(session)
        if report:
            return report

    raise RuntimeError("ADK pipeline finished without a coordinator report.")
