"""User-facing confidence labels derived from claim support analysis."""

from backend.trust_models import ClaimAnalysis, ConfidenceLevel, SupportLabel

CONFIDENCE_FOR_SUPPORT: dict[SupportLabel, tuple[ConfidenceLevel, str]] = {
    "supported": (
        "high",
        "Source directly supports the claim.",
    ),
    "weakly_supported": (
        "medium",
        "Source is related but does not fully prove the claim.",
    ),
    "unclear": (
        "medium",
        "Available source excerpt does not provide enough detail to confirm support.",
    ),
    "not_supported": (
        "low",
        "Source does not clearly support the claim.",
    ),
    "source_unavailable": (
        "low",
        "Source unavailable or could not be checked.",
    ),
}


def confidence_for_support(support_label: SupportLabel | None) -> tuple[ConfidenceLevel, str]:
    if support_label is None:
        return "low", "Source unavailable or could not be checked."
    return CONFIDENCE_FOR_SUPPORT.get(support_label, CONFIDENCE_FOR_SUPPORT["unclear"])


def apply_confidence(claim: ClaimAnalysis) -> ClaimAnalysis:
    """Attach confidence level and user-facing explanation to a claim."""
    if claim.support_label is None:
        return claim
    level, note = confidence_for_support(claim.support_label)
    return claim.model_copy(
        update={
            "confidence_level": level,
            "confidence_note": note,
        }
    )
