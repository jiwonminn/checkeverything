"""Rich demo trust report for screenshot and local testing."""

from backend.confidence import apply_confidence
from backend.trust_weights import compute_overall_score
from backend.claim_matcher import build_support_summary
from backend.source_checker import build_source_summary
from backend.trust_models import AnalyzeResponse, CategoryScore, ClaimAnalysis, CheckedSource


def _screenshot_sources(urls: list[str]) -> list[CheckedSource]:
    catalog = {
        "nih.gov": CheckedSource(
            url="https://www.nih.gov/health-information/vitamin-d",
            domain="nih.gov",
            reachable=True,
            status_code=200,
            title="Vitamin D — NIH Office of Dietary Supplements",
            meta_description="Fact sheet on vitamin D sources, benefits, and intake.",
            page_text="Vitamin D helps the body absorb calcium and supports bone health.",
            source_quality="high",
            notes="Government, university, or primary authority source. Title: Vitamin D — NIH",
        ),
        "cdc.gov": CheckedSource(
            url="https://www.cdc.gov/vitamin-d/index.html",
            domain="cdc.gov",
            reachable=True,
            status_code=200,
            title="Vitamin D — CDC",
            meta_description="Overview of vitamin D and health.",
            page_text="Vitamin D is important for bone health and immune function.",
            source_quality="high",
            notes="Government, university, or primary authority source. Title: Vitamin D — CDC",
        ),
    }
    broken = CheckedSource(
        url="https://demo.invalid/vitamin-study",
        domain="demo.invalid",
        reachable=False,
        status_code=404,
        title=None,
        meta_description=None,
        page_text=None,
        source_quality="low",
        notes="Broken or inaccessible citation.",
    )

    sources: list[CheckedSource] = []
    for url in urls:
        for key, source in catalog.items():
            if key in url and source.url not in [s.url for s in sources]:
                sources.append(source)
    if any("invalid" in u or "broken" in u for u in urls) or len(sources) < 2:
        if broken.url not in [s.url for s in sources]:
            sources.append(broken)
    if not sources:
        sources = list(catalog.values()) + [broken]
    return sources


def demo_trust_screenshot_report(
    urls: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> AnalyzeResponse:
    """Polished multi-claim report for demos and screenshots."""
    urls = urls or [
        "https://www.nih.gov/health-information/vitamin-d",
        "https://www.cdc.gov/vitamin-d/index.html",
        "https://demo.invalid/vitamin-study",
    ]
    sources = _screenshot_sources(urls)
    source_summary = build_source_summary(sources)

    claims = [
        apply_confidence(
            ClaimAnalysis(
                text="Vitamin D helps the body absorb calcium and supports bone health.",
                status="strongly_supported",
                citations=["https://www.nih.gov/health-information/vitamin-d"],
                matched_source="https://www.nih.gov/health-information/vitamin-d",
                support_label="supported",
                evidence_note="NIH source excerpt aligns with the claim about calcium absorption and bone health.",
            )
        ),
        apply_confidence(
            ClaimAnalysis(
                text="Vitamin D supplementation reduces cold risk by 40% for most adults.",
                status="weakly_supported",
                citations=["https://www.cdc.gov/vitamin-d/index.html"],
                matched_source="https://www.cdc.gov/vitamin-d/index.html",
                support_label="weakly_supported",
                evidence_note="CDC material discusses immune function but does not clearly prove the 40% figure.",
            )
        ),
        apply_confidence(
            ClaimAnalysis(
                text="Vitamin D prevents all chronic disease when taken daily.",
                status="unsupported",
                citations=["https://www.cdc.gov/vitamin-d/index.html"],
                matched_source="https://www.cdc.gov/vitamin-d/index.html",
                support_label="not_supported",
                evidence_note="Available excerpt does not support this broad prevention claim.",
            )
        ),
        apply_confidence(
            ClaimAnalysis(
                text="A cited study confirms vitamin D cures seasonal illness in every population.",
                status="unclear",
                citations=["https://demo.invalid/vitamin-study"],
                matched_source="https://demo.invalid/vitamin-study",
                support_label="source_unavailable",
                evidence_note="Citation was unreachable — content could not be verified.",
            )
        ),
    ]

    categories = {
        "claim_support": CategoryScore(
            score=72,
            summary="Most claims are specific, but one overstates what sources likely support.",
        ),
        "source_quality": CategoryScore(
            score=85,
            summary="2/3 cited sources were reachable. NIH and CDC are high-authority sources.",
        ),
        "citation_accuracy": CategoryScore(
            score=68,
            summary="2/4 claims matched to supportive or partial source evidence.",
        ),
        "freshness": CategoryScore(
            score=78,
            summary="Topic is relatively stable; dosage guidance may still need date checks.",
        ),
        "bias_context": CategoryScore(
            score=74,
            summary="Answer is mostly balanced but includes one overly broad health claim.",
        ),
    }

    return AnalyzeResponse(
        overall_score=compute_overall_score(categories, weights=weights),
        categories=categories,
        claims=claims,
        sources=sources,
        source_summary=source_summary,
        headline="Some claims are weakly supported — one citation was unreachable",
        support_summary=build_support_summary(claims),
    )
