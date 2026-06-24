"""Tests for user-facing confidence labels."""

from backend.confidence import apply_confidence, confidence_for_support
from backend.trust_models import ClaimAnalysis


def test_confidence_for_supported_is_high():
    level, note = confidence_for_support("supported")
    assert level == "high"
    assert "directly supports" in note.lower()


def test_confidence_for_weakly_supported_is_medium():
    level, note = confidence_for_support("weakly_supported")
    assert level == "medium"
    assert "does not fully prove" in note.lower()


def test_confidence_for_source_unavailable_is_low():
    level, note = confidence_for_support("source_unavailable")
    assert level == "low"
    assert "unavailable" in note.lower()


def test_apply_confidence_enriches_claim():
    claim = apply_confidence(
        ClaimAnalysis(
            text="Vitamin D may reduce infection risk.",
            status="weakly_supported",
            support_label="weakly_supported",
        )
    )
    assert claim.confidence_level == "medium"
    assert claim.confidence_note
