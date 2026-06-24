"""Preliminary AI response trust analysis pipeline."""

import os

from google.genai import errors as genai_errors
from google.genai import types

from backend.demo_trust import demo_trust_report
from backend.gemini_client import generate_with_fallback, get_client
from backend.trust_models import (
    AnalyzeRequest,
    AnalyzeResponse,
    CategoryScore,
    ClaimAnalysis,
    TrustAnalysisDraft,
    CATEGORY_KEYS,
    CATEGORY_WEIGHTS,
)
from backend.trust_prompts import MAX_ANALYZE_CHARS, TRUST_ANALYSIS_INSTRUCTION


def _demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")


def _is_recoverable_api_error(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.APIError):
        msg = str(exc)
        return (
            "429" in msg
            or "503" in msg
            or "RESOURCE_EXHAUSTED" in msg
            or "UNAVAILABLE" in msg
            or "NOT_FOUND" in msg
        )
    if isinstance(exc, RuntimeError):
        msg = str(exc)
        return "GEMINI_API_KEY" in msg or "GOOGLE_CLOUD_PROJECT" in msg
    return False


def _validate_request(request: AnalyzeRequest) -> None:
    text = request.text.strip()
    if not text:
        raise ValueError("text is required")
    if len(text) > MAX_ANALYZE_CHARS:
        raise ValueError(f"text exceeds maximum length of {MAX_ANALYZE_CHARS} characters")


def _format_analyze_input(request: AnalyzeRequest) -> str:
    urls_block = "\n".join(f"- {url}" for url in request.urls) if request.urls else "(none provided)"
    return (
        f"Source platform: {request.source}\n\n"
        f"Cited URLs:\n{urls_block}\n\n"
        f"AI response:\n{request.text.strip()}"
    )


def compute_overall_score(categories: dict[str, CategoryScore]) -> int:
    total = sum(categories[key].score * CATEGORY_WEIGHTS[key] for key in CATEGORY_KEYS)
    return max(0, min(100, round(total)))


def draft_to_response(draft: TrustAnalysisDraft) -> AnalyzeResponse:
    categories = {
        "claim_support": CategoryScore(
            score=draft.claim_support.score,
            summary=draft.claim_support.summary,
        ),
        "source_quality": CategoryScore(
            score=draft.source_quality.score,
            summary=draft.source_quality.summary,
        ),
        "citation_accuracy": CategoryScore(
            score=draft.citation_accuracy.score,
            summary=draft.citation_accuracy.summary,
        ),
        "freshness": CategoryScore(
            score=draft.freshness.score,
            summary=draft.freshness.summary,
        ),
        "bias_context": CategoryScore(
            score=draft.bias_context.score,
            summary=draft.bias_context.summary,
        ),
    }
    claims = [
        ClaimAnalysis(
            text=claim.text,
            status=claim.status,
            citations=claim.related_citations,
            note=claim.note,
        )
        for claim in draft.claims
    ]
    return AnalyzeResponse(
        overall_score=compute_overall_score(categories),
        categories=categories,
        claims=claims,
        headline=draft.headline,
        support_summary=draft.support_summary,
    )


def _analyze_with_gemini(request: AnalyzeRequest) -> AnalyzeResponse:
    client = get_client()
    response = generate_with_fallback(
        client,
        contents=_format_analyze_input(request),
        config=types.GenerateContentConfig(
            system_instruction=TRUST_ANALYSIS_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=TrustAnalysisDraft,
            temperature=0.2,
        ),
    )
    draft = TrustAnalysisDraft.model_validate_json(response.text)
    return draft_to_response(draft)


def analyze_response(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run preliminary trust analysis on an AI-generated response."""
    _validate_request(request)

    if _demo_mode_enabled():
        return demo_trust_report(request.text, request.urls)

    try:
        return _analyze_with_gemini(request)
    except Exception as exc:
        if _is_recoverable_api_error(exc):
            return demo_trust_report(request.text, request.urls)
        raise
