"""Tests for claim-to-source matching."""

from backend.claim_matcher import (
    _fallback_match,
    build_support_summary,
    match_claims_to_sources,
    support_label_to_status,
)
from backend.source_checker import html_to_plain_text
from backend.trust_models import ClaimDraft, CheckedSource


def test_html_to_plain_text_extracts_paragraphs():
    html = """
    <html><head><title>Test</title></head><body>
    <script>ignore()</script>
    <p>Vitamin D supplementation may reduce the risk of acute respiratory infections in some adults.</p>
    <p>Researchers continue to study exact dosage recommendations and population-level effects.</p>
    </body></html>
    """
    text = html_to_plain_text(html)
    assert "Vitamin D supplementation" in text
    assert "ignore()" not in text


def test_support_label_to_status_mapping():
    assert support_label_to_status("supported") == "strongly_supported"
    assert support_label_to_status("source_unavailable") == "unclear"


def test_fallback_match_marks_unreachable_source():
    claim = ClaimDraft(
        text="Vitamin D reduces cold risk by 40%.",
        status="weakly_supported",
        related_citations=["https://broken.example/article"],
        note="",
    )
    sources = [
        CheckedSource(
            url="https://broken.example/article",
            domain="broken.example",
            reachable=False,
            status_code=404,
            title=None,
            source_quality="low",
            notes="Broken",
        )
    ]
    result = _fallback_match(claim, sources)
    assert result.support_label == "source_unavailable"
    assert result.matched_source == "https://broken.example/article"


def test_build_support_summary():
    from backend.trust_models import ClaimAnalysis

    claims = [
        ClaimAnalysis(
            text="Claim A",
            status="strongly_supported",
            support_label="supported",
        ),
        ClaimAnalysis(
            text="Claim B",
            status="unclear",
            support_label="source_unavailable",
        ),
    ]
    summary = build_support_summary(claims)
    assert "1/2" in summary


def test_match_claims_without_sources():
    claims = [
        ClaimDraft(
            text="Exercise improves sleep.",
            status="unclear",
            related_citations=[],
            note="",
        )
    ]
    matched = match_claims_to_sources(claims, [])
    assert matched[0].support_label == "source_unavailable"
