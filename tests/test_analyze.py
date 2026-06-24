"""Tests for preliminary trust analysis."""

import pytest

from backend.analyze import compute_overall_score, draft_to_response
from backend.demo_trust import demo_trust_report
from backend.trust_models import (
    AnalyzeRequest,
    CategoryAssessment,
    CategoryScore,
    ClaimDraft,
    TrustAnalysisDraft,
)


def test_compute_overall_score_uses_fixed_weights():
    categories = {
        "claim_support": CategoryScore(score=70, summary=""),
        "source_quality": CategoryScore(score=85, summary=""),
        "citation_accuracy": CategoryScore(score=65, summary=""),
        "freshness": CategoryScore(score=90, summary=""),
        "bias_context": CategoryScore(score=75, summary=""),
    }
    assert compute_overall_score(categories) == 74


def test_draft_to_response_maps_categories_and_claims():
    draft = TrustAnalysisDraft(
        claims=[
            ClaimDraft(
                text="Vitamin D may reduce cold risk.",
                status="weakly_supported",
                related_citations=["https://example.com/study"],
                note="Citation is related, but does not clearly prove the full claim.",
            )
        ],
        claim_support=CategoryAssessment(score=70, summary="Most claims are supported."),
        source_quality=CategoryAssessment(score=85, summary="Sources appear mostly reliable."),
        citation_accuracy=CategoryAssessment(score=65, summary="Some citations are loosely matched."),
        freshness=CategoryAssessment(score=90, summary="Information appears recent enough."),
        bias_context=CategoryAssessment(score=75, summary="Mostly balanced."),
        headline="Some claims are weakly supported",
        support_summary="Strong support found for 0/1 claims",
    )

    response = draft_to_response(draft)

    assert response.overall_score == 74
    assert response.categories["claim_support"].score == 70
    assert response.claims[0].status == "weakly_supported"
    assert response.analysis_type == "preliminary"


def test_demo_trust_report_shape():
    report = demo_trust_report("AI says exercise helps sleep. See https://example.com", ["https://example.com"])
    assert 0 <= report.overall_score <= 100
    assert set(report.categories) == {
        "claim_support",
        "source_quality",
        "citation_accuracy",
        "freshness",
        "bias_context",
    }
    assert report.claims
    assert report.headline


def test_analyze_request_requires_text():
    from backend.analyze import analyze_response

    with pytest.raises(ValueError, match="text is required"):
        analyze_response(AnalyzeRequest(text="   "))


def test_analyze_response_in_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from backend.analyze import analyze_response

    result = analyze_response(
        AnalyzeRequest(text="Regular exercise can improve sleep quality for many adults.")
    )
    assert result.analysis_type == "preliminary"
    assert result.overall_score >= 0
