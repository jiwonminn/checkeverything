"""Preliminary AI response trust analysis pipeline."""

import os

from google.genai import types

from backend.api_errors import is_recoverable_api_error
from backend.confidence import apply_confidence
from backend.claim_matcher import build_support_summary, match_claims_to_sources
from backend.demo_trust import demo_trust_report
from backend.demo_trust_screenshot import demo_trust_screenshot_report
from backend.gemini_client import generate_with_fallback, get_client
from backend.source_checker import (
    build_source_summary,
    check_sources,
    format_sources_for_prompt,
    merge_urls,
)
from backend.trust_models import (
    AnalyzeRequest,
    AnalyzeResponse,
    CategoryScore,
    ClaimAnalysis,
    CheckedSource,
    TrustAnalysisDraft,
    CATEGORY_KEYS,
    CATEGORY_WEIGHTS,
)
from backend.trust_weights import compute_overall_score, normalize_weights
from backend.trust_prompts import MAX_ANALYZE_CHARS, TRUST_ANALYSIS_INSTRUCTION


def _demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")


def _validate_request(request: AnalyzeRequest) -> None:
    text = request.text.strip()
    if not text:
        raise ValueError("text is required")
    if len(text) > MAX_ANALYZE_CHARS:
        raise ValueError(f"text exceeds maximum length of {MAX_ANALYZE_CHARS} characters")


def _format_analyze_input(request: AnalyzeRequest, sources: list[CheckedSource]) -> str:
    return (
        f"Source platform: {request.source}\n\n"
        f"Checked source metadata:\n{format_sources_for_prompt(sources)}\n\n"
        f"AI response:\n{request.text.strip()}"
    )


def _heuristic_source_quality_score(sources: list[CheckedSource]) -> int | None:
    if not sources:
        return None

    quality_scores = {
        "high": 90,
        "medium-high": 78,
        "medium": 65,
        "low-medium": 45,
        "low": 25,
    }
    reachable = [source for source in sources if source.reachable]
    if not reachable:
        return 20

    average = sum(quality_scores[source.source_quality] for source in reachable) / len(reachable)
    unreachable_penalty = (len(sources) - len(reachable)) * 10
    return max(0, min(100, round(average - unreachable_penalty)))


def _blend_source_quality(
    gemini_score: int,
    sources: list[CheckedSource],
) -> CategoryScore:
    heuristic = _heuristic_source_quality_score(sources)
    if heuristic is None:
        return CategoryScore(score=gemini_score, summary="")

    blended = round(0.6 * gemini_score + 0.4 * heuristic)
    summary_bits = []
    if sources:
        reachable = sum(1 for source in sources if source.reachable)
        summary_bits.append(f"{reachable}/{len(sources)} cited sources were reachable.")
    return CategoryScore(
        score=blended,
        summary=" ".join(summary_bits),
    )


def _blend_citation_accuracy(
    gemini_score: int,
    claims: list[ClaimAnalysis],
) -> CategoryScore:
    if not claims or not any(claim.support_label for claim in claims):
        return CategoryScore(score=gemini_score, summary="")

    label_scores = {
        "supported": 92,
        "weakly_supported": 68,
        "not_supported": 28,
        "unclear": 50,
        "source_unavailable": 35,
    }
    average = sum(label_scores.get(claim.support_label or "unclear", 50) for claim in claims) / len(claims)
    blended = round(0.5 * gemini_score + 0.5 * average)
    matched = sum(
        1 for claim in claims if claim.support_label in ("supported", "weakly_supported")
    )
    return CategoryScore(
        score=blended,
        summary=f"{matched}/{len(claims)} claims matched to supportive or partial source evidence.",
    )


def draft_to_response(
    draft: TrustAnalysisDraft,
    sources: list[CheckedSource],
    claims: list[ClaimAnalysis] | None = None,
    support_summary: str | None = None,
    weights: dict[str, float] | None = None,
) -> AnalyzeResponse:
    final_claims = claims or [
        apply_confidence(
            ClaimAnalysis(
                text=claim.text,
                status=claim.status,
                citations=claim.related_citations,
                note=claim.note,
            )
        )
        for claim in draft.claims
    ]

    source_quality = _blend_source_quality(draft.source_quality.score, sources)
    if draft.source_quality.summary:
        source_quality.summary = (
            f"{draft.source_quality.summary} {source_quality.summary}".strip()
        )

    citation_accuracy = _blend_citation_accuracy(draft.citation_accuracy.score, final_claims)
    if draft.citation_accuracy.summary:
        citation_accuracy.summary = (
            f"{draft.citation_accuracy.summary} {citation_accuracy.summary}".strip()
        )

    categories = {
        "claim_support": CategoryScore(
            score=draft.claim_support.score,
            summary=draft.claim_support.summary,
        ),
        "source_quality": source_quality,
        "citation_accuracy": citation_accuracy,
        "freshness": CategoryScore(
            score=draft.freshness.score,
            summary=draft.freshness.summary,
        ),
        "bias_context": CategoryScore(
            score=draft.bias_context.score,
            summary=draft.bias_context.summary,
        ),
    }
    return AnalyzeResponse(
        overall_score=compute_overall_score(categories, weights=weights),
        categories=categories,
        claims=final_claims,
        sources=sources,
        source_summary=build_source_summary(sources),
        headline=draft.headline,
        support_summary=support_summary or draft.support_summary,
    )


def _analyze_with_gemini(request: AnalyzeRequest, sources: list[CheckedSource]) -> AnalyzeResponse:
    client = get_client()
    response = generate_with_fallback(
        client,
        contents=_format_analyze_input(request, sources),
        config=types.GenerateContentConfig(
            system_instruction=TRUST_ANALYSIS_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=TrustAnalysisDraft,
            temperature=0.2,
        ),
    )
    draft = TrustAnalysisDraft.model_validate_json(response.text)
    active_weights = normalize_weights(request.weights)

    try:
        matched_claims = match_claims_to_sources(draft.claims, sources)
        support_summary = build_support_summary(matched_claims)
    except Exception:
        matched_claims = None
        support_summary = draft.support_summary

    return draft_to_response(
        draft,
        sources,
        claims=matched_claims,
        support_summary=support_summary,
        weights=active_weights,
    )


def _is_screenshot_demo_request(request: AnalyzeRequest) -> bool:
    text = request.text.lower()
    return (
        "vitamin d" in text
        or "vitamin" in text
        or request.source in ("google_ai_overview", "chatgpt")
        and len(request.urls) >= 1
    )


def analyze_response(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run preliminary trust analysis on an AI-generated response."""
    _validate_request(request)
    urls = merge_urls(request.urls, request.text)
    active_weights = normalize_weights(request.weights)

    if _demo_mode_enabled():
        if _is_screenshot_demo_request(request):
            return demo_trust_screenshot_report(request.urls, weights=active_weights)
        return demo_trust_report(request.text, urls, weights=active_weights)

    sources = check_sources(urls)

    try:
        return _analyze_with_gemini(request, sources)
    except Exception as exc:
        if is_recoverable_api_error(exc):
            if _is_screenshot_demo_request(request):
                return demo_trust_screenshot_report(urls, weights=active_weights)
            return demo_trust_report(request.text, urls, weights=active_weights)
        raise
