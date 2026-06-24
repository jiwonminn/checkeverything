"""Trust score weight normalization for /api/analyze."""

from backend.trust_models import CATEGORY_KEYS, CATEGORY_WEIGHTS, CategoryScore, TrustWeights


def normalize_weights(weights: TrustWeights | None) -> dict[str, float]:
    """Normalize category weights to sum to 1.0. Falls back to defaults if invalid."""
    if weights is None:
        return dict(CATEGORY_WEIGHTS)

    raw = {key: max(0, getattr(weights, key)) for key in CATEGORY_KEYS}
    total = sum(raw.values())
    if total <= 0:
        return dict(CATEGORY_WEIGHTS)
    return {key: raw[key] / total for key in CATEGORY_KEYS}


def compute_overall_score(
    categories: dict[str, CategoryScore],
    weights: dict[str, float] | None = None,
) -> int:
    active_weights = weights or CATEGORY_WEIGHTS
    total = sum(categories[key].score * active_weights[key] for key in CATEGORY_KEYS)
    return max(0, min(100, round(total)))
