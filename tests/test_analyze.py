"""Tests for preliminary trust analysis."""

import pytest

from backend.trust_weights import compute_overall_score
from backend.analyze import draft_to_response
from backend.demo_trust import demo_trust_report
from backend.trust_models import (
    AnalyzeRequest,
    CategoryAssessment,
    CategoryScore,
    ClaimDraft,
    CheckedSource,
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

    response = draft_to_response(draft, sources=[])

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
    assert result.pipeline == "demo"
    assert result.overall_score >= 0


def test_analyze_with_gemini_enriches_claims_with_source_matches(monkeypatch):
    from backend import analyze

    draft = TrustAnalysisDraft(
        claims=[
            ClaimDraft(
                text="Exercise can improve sleep quality.",
                status="unclear",
                related_citations=["https://example.org/sleep"],
                note="",
            )
        ],
        claim_support=CategoryAssessment(score=60, summary="Some support."),
        source_quality=CategoryAssessment(score=70, summary="Reachable source."),
        citation_accuracy=CategoryAssessment(score=50, summary="Citation needs checking."),
        freshness=CategoryAssessment(score=80, summary="Recent enough."),
        bias_context=CategoryAssessment(score=75, summary="Balanced."),
        headline="Needs source verification",
        support_summary="Draft summary",
    )
    source = CheckedSource(
        url="https://example.org/sleep",
        domain="example.org",
        reachable=True,
        status_code=200,
        page_text="Exercise can improve sleep quality for many adults.",
        source_quality="medium",
    )

    class FakeResponse:
        text = draft.model_dump_json()

    monkeypatch.setattr(analyze, "get_client", lambda: object())
    monkeypatch.setattr(analyze, "generate_with_fallback", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(
        analyze,
        "match_claims_to_sources",
        lambda claims, sources: [
            analyze.apply_confidence(
                analyze.ClaimAnalysis(
                    text=claims[0].text,
                    status="strongly_supported",
                    citations=[source.url],
                    matched_source=source.url,
                    support_label="supported",
                    evidence_note="The source excerpt supports the claim.",
                )
            )
        ],
    )
    monkeypatch.setattr(
        analyze,
        "build_support_summary",
        lambda claims: "Claim-source matching: 1/1 claims had supporting or partial source evidence.",
    )

    result = analyze._analyze_with_gemini(
        AnalyzeRequest(text="Exercise can improve sleep quality.", urls=[source.url]),
        [source],
    )

    assert result.claims[0].support_label == "supported"
    assert result.claims[0].matched_source == source.url
    assert result.support_summary.startswith("Claim-source matching: 1/1")
