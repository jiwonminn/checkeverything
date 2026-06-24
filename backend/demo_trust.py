"""Offline demo trust analysis when API quota is unavailable."""

from backend.trust_models import AnalyzeResponse, CategoryScore, ClaimAnalysis


def demo_trust_report(text: str, urls: list[str] | None = None) -> AnalyzeResponse:
    """Return a plausible preliminary trust report for demos and API fallbacks."""
    urls = urls or []
    has_urls = len(urls) > 0
    word_count = len(text.split())

    claims = [
        ClaimAnalysis(
            text="The response presents factual statements that could be verified with external sources.",
            status="unclear" if not has_urls else "weakly_supported",
            citations=urls[:1],
            note="Preliminary demo analysis — full source verification not performed.",
        ),
    ]
    if word_count > 80:
        claims.append(
            ClaimAnalysis(
                text="Some statements may require freshness verification depending on the topic.",
                status="unclear",
                citations=[],
                note="Time-sensitive topics benefit from checking publication dates.",
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
                    "Citations appear related to the topic, but full claim-to-source matching is not verified."
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
        headline="Preliminary credibility signal — some claims need stronger support",
        support_summary=f"Demo analysis of {len(claims)} sample claim(s). Full claim extraction requires a live API key.",
    )
