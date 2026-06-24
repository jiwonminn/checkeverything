"""Tests for code review agent weight normalization."""

from backend.demo_report import demo_review_report
from backend.models import ReviewWeights
from backend.review_weights import (
    apply_review_weights,
    compute_weighted_overall_score,
    normalize_review_weights,
)


def test_normalize_review_weights_defaults():
    weights = normalize_review_weights(None)
    assert abs(sum(weights.values()) - 1.0) < 0.001
    assert weights["security"] == 0.20


def test_normalize_review_weights_scales_to_one():
    weights = normalize_review_weights(
        ReviewWeights(security=20, correctness=20, readability=20, performance=20, test_coverage=20)
    )
    assert abs(weights["security"] - 0.2) < 0.001


def test_compute_weighted_overall_score_uses_custom_weights():
    report = demo_review_report("x = 1", "python", "")
    scores = {r.agent_name: r.score for r in report.agent_reports}
    security_only = normalize_review_weights(
        ReviewWeights(security=100, correctness=0, readability=0, performance=0, test_coverage=0)
    )
    expected = scores["Security Agent"]
    assert compute_weighted_overall_score(report.agent_reports, security_only) == expected


def test_apply_review_weights_updates_overall_score():
    report = demo_review_report("x = 1", "python", "")
    weighted, percentages = apply_review_weights(report, None)
    assert weighted.overall_score == compute_weighted_overall_score(report.agent_reports)
    assert percentages["security"] == 20
    assert sum(percentages.values()) == 100


def test_demo_report_scores_vary_by_submitted_code():
    clean = demo_review_report("def add(a, b):\n    return a + b\n", "python", "")
    risky = demo_review_report(
        'SECRET_KEY = "x"\ndef login(u, p):\n    return f"SELECT * FROM users WHERE u=\'{u}\'"\n',
        "python",
        "",
    )
    assert clean.overall_score != risky.overall_score
    assert risky.overall_score < clean.overall_score
