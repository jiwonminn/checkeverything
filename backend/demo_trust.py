"""Offline demo trust analysis when API quota is unavailable."""

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


def demo_trust_report(text: str, urls: list[str] | None = None) -> AnalyzeResponse:
    """Return a plausible preliminary trust report for demos and API fallbacks."""
    urls = urls or []
    sources = _demo_sources(urls) if urls else []
    has_urls = len(sources) > 0
    word_count = len(text.split())
    source_summary = build_source_summary(sources) if sources else None
    matched_url = urls[0] if urls else None

    claims = [
        ClaimAnalysis(
            text="The response presents factual statements that could be verified with external sources.",
            status="weakly_supported" if has_urls else "unclear",
            citations=urls[:1],
            note="Preliminary demo analysis — full source verification not performed.",
            matched_source=matched_url,
            support_label="weakly_supported" if has_urls else "source_unavailable",
            evidence_note=(
                "Demo mode: source appears related, but live claim-to-source matching was not performed."
                if has_urls
                else "No usable source content was available for this claim."
            ),
        ),
    ]
    if word_count > 80:
        claims.append(
            ClaimAnalysis(
                text="Some statements may require freshness verification depending on the topic.",
                status="unclear",
                citations=[],
                matched_source=None,
                support_label="unclear",
                evidence_note="Time-sensitive topics benefit from checking publication dates.",
            )
        )

    return AnalyzeResponse(
        overall_score=72 if has_urls else 58,
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
        headline="Preliminary credibility signal — some claims need stronger support",
        support_summary=build_support_summary(claims),
    )
