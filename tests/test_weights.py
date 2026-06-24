"""Tests for trust score weight normalization."""

from backend.trust_weights import compute_overall_score
from backend.trust_models import CategoryScore, TrustWeights
from backend.trust_weights import normalize_weights


def test_normalize_weights_defaults_when_none():
    weights = normalize_weights(None)
    assert abs(sum(weights.values()) - 1.0) < 0.001
    assert weights["claim_support"] == 0.35


def test_normalize_weights_scales_to_one():
    weights = normalize_weights(
        TrustWeights(
            claim_support=50,
            source_quality=50,
            citation_accuracy=0,
            bias_context=0,
            freshness=0,
        )
    )
    assert abs(weights["claim_support"] - 0.5) < 0.001
    assert abs(weights["source_quality"] - 0.5) < 0.001


def test_normalize_weights_falls_back_when_all_zero():
    weights = normalize_weights(
        TrustWeights(
            claim_support=0,
            source_quality=0,
            citation_accuracy=0,
            bias_context=0,
            freshness=0,
        )
    )
    assert weights["claim_support"] == 0.35


def test_compute_overall_score_respects_custom_weights():
    categories = {
        "claim_support": CategoryScore(score=100, summary=""),
        "source_quality": CategoryScore(score=0, summary=""),
        "citation_accuracy": CategoryScore(score=0, summary=""),
        "freshness": CategoryScore(score=0, summary=""),
        "bias_context": CategoryScore(score=0, summary=""),
    }
    default_score = compute_overall_score(categories)
    custom_score = compute_overall_score(
        categories,
        weights={"claim_support": 1.0, "source_quality": 0.0, "citation_accuracy": 0.0, "freshness": 0.0, "bias_context": 0.0},
    )
    assert default_score == 35
    assert custom_score == 100
