"""Agent score weight normalization for code review."""

from backend.models import AgentFindingReport, ReviewReport, ReviewWeights

AGENT_WEIGHT_KEYS = (
    "security",
    "correctness",
    "readability",
    "performance",
    "test_coverage",
)

AGENT_NAME_TO_KEY: dict[str, str] = {
    "Security Agent": "security",
    "Correctness Agent": "correctness",
    "Readability Agent": "readability",
    "Performance Agent": "performance",
    "Test Coverage Agent": "test_coverage",
}

DEFAULT_WEIGHT_PERCENTAGES: dict[str, int] = {
    "security": 20,
    "correctness": 25,
    "readability": 15,
    "performance": 15,
    "test_coverage": 25,
}

DEFAULT_AGENT_WEIGHTS: dict[str, float] = {
    key: value / 100 for key, value in DEFAULT_WEIGHT_PERCENTAGES.items()
}


def normalize_review_weights(weights: ReviewWeights | None) -> dict[str, float]:
    """Normalize agent weights to sum to 1.0. Falls back to defaults if invalid."""
    if weights is None:
        return dict(DEFAULT_AGENT_WEIGHTS)

    raw = {key: max(0, getattr(weights, key)) for key in AGENT_WEIGHT_KEYS}
    total = sum(raw.values())
    if total <= 0:
        return dict(DEFAULT_AGENT_WEIGHTS)
    return {key: raw[key] / total for key in AGENT_WEIGHT_KEYS}


def weights_to_percentages(weights: dict[str, float]) -> dict[str, int]:
    return {key: round(weights[key] * 100) for key in AGENT_WEIGHT_KEYS}


def compute_weighted_overall_score(
    agent_reports: list[AgentFindingReport],
    weights: dict[str, float] | None = None,
) -> int:
    active = weights or DEFAULT_AGENT_WEIGHTS
    total = 0.0
    for report in agent_reports:
        key = AGENT_NAME_TO_KEY.get(report.agent_name)
        if key:
            total += report.score * active[key]
    return max(0, min(100, round(total)))


def apply_review_weights(report: ReviewReport, weights: ReviewWeights | None) -> tuple[ReviewReport, dict[str, int]]:
    normalized = normalize_review_weights(weights)
    percentages = weights_to_percentages(normalized)
    score = compute_weighted_overall_score(report.agent_reports, normalized)
    return report.model_copy(update={"overall_score": score}), percentages
