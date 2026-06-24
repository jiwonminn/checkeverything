"""Offline demo trust analysis when API quota is unavailable."""

import re

from backend.confidence import apply_confidence
from backend.trust_weights import compute_overall_score
from backend.claim_matcher import build_support_summary
from backend.source_checker import build_source_summary, classify_domain, parse_domain
from backend.trust_models import AnalyzeResponse, CategoryScore, ClaimAnalysis, CheckedSource


def _demo_sources(urls: list[str]) -> list[CheckedSource]:
    sources: list[CheckedSource] = []
    for url in urls:
        domain = parse_domain(url)
        quality, notes = classify_domain(domain, reachable=True)
        sources.append(
            CheckedSource(
                url=url,
                domain=domain or "unknown",
                reachable=True,
                status_code=200,
                title="Demo source title",
                meta_description="Demo source description for offline analysis.",
                page_text="Demo source excerpt. Live page content was not fetched.",
                source_quality=quality,
                notes=f"Demo metadata only — live fetch not performed. {notes}",
            )
        )
    return sources


def _extract_claims_from_text(text: str, urls: list[str]) -> list[str]:
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", text.strip())
        if len(s.split()) >= 6
    ]
    if not sentences:
        return [text.strip()[:240]] if text.strip() else []
    return sentences[:4]


def _support_for_claim(sentence: str, has_urls: bool) -> tuple[str, str, str]:
    lower = sentence.lower()
    hedged = any(word in lower for word in ("may", "might", "could", "some", "generally", "often"))
    numeric = bool(re.search(r"\d", sentence))
    if not has_urls:
        return "unclear", "source_unavailable", "No citations were provided to verify this statement."
    if hedged:
        return "weakly_supported", "weakly_supported", (
            "Wording is cautious, but cited sources were not fully matched to this exact claim in demo mode."
        )
    if numeric:
        return "weakly_supported", "weakly_supported", (
            "Contains specific figures — verify against the cited source's original data."
        )
    return "strongly_supported", "supported", "Demo mode: claim appears consistent with the type of sources cited."


def demo_trust_report(
    text: str,
    urls: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> AnalyzeResponse:
    """Return a plausible preliminary trust report for demos and API fallbacks."""
    urls = urls or []
    sources = _demo_sources(urls) if urls else []
    has_urls = len(sources) > 0
    source_summary = build_source_summary(sources) if sources else None
    matched_url = urls[0] if urls else None
    claim_texts = _extract_claims_from_text(text, urls)

    claims = []
    for idx, claim_text in enumerate(claim_texts):
        status, label, evidence = _support_for_claim(claim_text, has_urls)
        claims.append(
            apply_confidence(
                ClaimAnalysis(
                    text=claim_text,
                    status=status,
                    citations=urls[idx : idx + 1] if urls else [],
                    note=evidence,
                    matched_source=urls[idx] if idx < len(urls) else matched_url,
                    support_label=label,
                    evidence_note=evidence,
                )
            )
        )

    return AnalyzeResponse(
        overall_score=compute_overall_score(
            {
                "claim_support": CategoryScore(score=68, summary=""),
                "source_quality": CategoryScore(score=80 if has_urls else 45, summary=""),
                "citation_accuracy": CategoryScore(score=70 if has_urls else 50, summary=""),
                "freshness": CategoryScore(score=75, summary=""),
                "bias_context": CategoryScore(score=72, summary=""),
            },
            weights=weights,
        ),
        categories={
            "claim_support": CategoryScore(
                score=68,
                summary="Claims are present but not all are equally specific or well-supported in the text.",
            ),
            "source_quality": CategoryScore(
                score=80 if has_urls else 45,
                summary=(
                    "Citations are included and appear relevant at a surface level."
                    if has_urls
                    else "No citations or URLs were provided with the response."
                ),
            ),
            "citation_accuracy": CategoryScore(
                score=70 if has_urls else 50,
                summary=(
                    "Demo claim-source matching suggests partial support for at least one claim."
                    if has_urls
                    else "Without citations, structural citation accuracy cannot be assessed."
                ),
            ),
            "freshness": CategoryScore(
                score=75,
                summary="Some claims may need freshness verification depending on the subject matter.",
            ),
            "bias_context": CategoryScore(
                score=72,
                summary="Tone appears mostly balanced, though confidence level should be reviewed claim by claim.",
            ),
        },
        claims=claims,
        sources=sources,
        source_summary=source_summary,
        headline=(
            "Most claims look plausible, but verify citations before trusting this answer."
            if has_urls
            else "No sources cited — treat factual statements as unverified."
        ),
        support_summary=build_support_summary(claims),
    )
