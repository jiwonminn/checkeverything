"""Run trust analysis through Google ADK (extract → match sequential graph)."""

import uuid

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from adk_agents.checkeverything.trust_agent import trust_root_agent
from backend.analyze import draft_to_response
from backend.claim_matcher import apply_matching_draft, build_support_summary
from backend.source_checker import format_sources_for_prompt
from backend.trust_models import AnalyzeRequest, AnalyzeResponse, CheckedSource, ClaimMatchingDraft, TrustAnalysisDraft


def _build_user_message(request: AnalyzeRequest, sources: list[CheckedSource]) -> types.Content:
    text = (
        f"Source platform: {request.source}\n\n"
        f"Checked source metadata:\n{format_sources_for_prompt(sources)}\n\n"
        f"AI response:\n{request.text.strip()}"
    )
    return types.Content(role="user", parts=[types.Part(text=text)])


def _parse_state_value(value, model_cls):
    if value is None:
        return None
    if isinstance(value, dict):
        return model_cls.model_validate(value)
    if isinstance(value, str):
        return model_cls.model_validate_json(value)
    return model_cls.model_validate(value)


def _extract_trust_results(session) -> tuple[TrustAnalysisDraft, ClaimMatchingDraft] | None:
    state = session.state or {}
    draft = _parse_state_value(state.get("trust_draft"), TrustAnalysisDraft)
    matches = _parse_state_value(state.get("claim_matches"), ClaimMatchingDraft)
    if draft and matches:
        return draft, matches
    return None


def analyze_with_adk(request: AnalyzeRequest, sources: list[CheckedSource]) -> AnalyzeResponse:
    """Execute the ADK trust graph: extractor agent → matcher agent."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=trust_root_agent,
        app_name="checkeverything_trust",
        session_service=session_service,
        auto_create_session=True,
    )
    session_id = str(uuid.uuid4())
    user_id = "checkeverything_trust_user"

    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=_build_user_message(request, sources),
    ):
        if event.is_final_response() and event.author == "trust_matcher_agent":
            if event.content and event.content.parts:
                text = "".join(
                    p.text for p in event.content.parts if p.text and not p.thought
                )
                if text.strip():
                    matching = ClaimMatchingDraft.model_validate_json(text)
                    session = session_service.get_session_sync(
                        app_name="checkeverything_trust",
                        user_id=user_id,
                        session_id=session_id,
                    )
                    draft = None
                    if session:
                        draft = _parse_state_value(session.state.get("trust_draft"), TrustAnalysisDraft)
                    if draft:
                        matched_claims = apply_matching_draft(draft.claims, matching, sources)
                        support_summary = build_support_summary(matched_claims)
                        return draft_to_response(
                            draft,
                            sources,
                            claims=matched_claims,
                            support_summary=support_summary,
                        )

    session = session_service.get_session_sync(
        app_name="checkeverything_trust",
        user_id=user_id,
        session_id=session_id,
    )
    if session:
        extracted = _extract_trust_results(session)
        if extracted:
            draft, matching = extracted
            matched_claims = apply_matching_draft(draft.claims, matching, sources)
            support_summary = build_support_summary(matched_claims)
            return draft_to_response(
                draft,
                sources,
                claims=matched_claims,
                support_summary=support_summary,
            )

    raise RuntimeError("ADK trust pipeline finished without extractor and matcher outputs.")
