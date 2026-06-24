"""Pydantic models for AI response trust analysis (/api/analyze)."""

from typing import Literal

from pydantic import BaseModel, Field


SourceQualityLevel = Literal["high", "medium-high", "medium", "low-medium", "low"]

SupportLabel = Literal[
    "supported",
    "weakly_supported",
    "not_supported",
    "unclear",
    "source_unavailable",
]

ConfidenceLevel = Literal["high", "medium", "low"]

ClaimStatus = Literal[
    "strongly_supported",
    "weakly_supported",
    "unclear",
    "outdated",
    "unsupported",
]

CATEGORY_KEYS = (
    "claim_support",
    "source_quality",
    "citation_accuracy",
    "freshness",
    "bias_context",
)

CATEGORY_WEIGHTS: dict[str, float] = {
    "claim_support": 0.35,
    "source_quality": 0.25,
    "citation_accuracy": 0.25,
    "bias_context": 0.10,
    "freshness": 0.05,
}

DEFAULT_WEIGHT_PERCENTAGES: dict[str, int] = {
    key: int(value * 100) for key, value in CATEGORY_WEIGHTS.items()
}


class TrustWeights(BaseModel):
    claim_support: int = Field(default=35, ge=0, le=100)
    source_quality: int = Field(default=25, ge=0, le=100)
    citation_accuracy: int = Field(default=25, ge=0, le=100)
    bias_context: int = Field(default=10, ge=0, le=100)
    freshness: int = Field(default=5, ge=0, le=100)


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, description="Full AI response text")
    urls: list[str] = Field(default_factory=list, description="Cited URLs extracted from the response")
    source: Literal["chatgpt", "google_ai", "google_ai_overview", "other"] = Field(default="chatgpt")
    weights: TrustWeights | None = None


class CategoryScore(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str = ""


class ClaimAnalysis(BaseModel):
    text: str
    status: ClaimStatus
    citations: list[str] = Field(default_factory=list)
    note: str = ""
    matched_source: str | None = None
    support_label: SupportLabel | None = None
    evidence_note: str = ""
    confidence_level: ConfidenceLevel | None = None
    confidence_note: str = ""


class CheckedSource(BaseModel):
    url: str
    domain: str
    reachable: bool
    status_code: int | None = None
    title: str | None = None
    meta_description: str | None = None
    page_text: str | None = None
    source_quality: SourceQualityLevel
    notes: str = ""


class SourceCheckSummary(BaseModel):
    sources_checked: int = 0
    reachable_count: int = 0
    primary_official_count: int = 0
    issues: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    categories: dict[str, CategoryScore]
    claims: list[ClaimAnalysis] = Field(default_factory=list)
    sources: list[CheckedSource] = Field(default_factory=list)
    source_summary: SourceCheckSummary | None = None
    headline: str = ""
    support_summary: str = ""
    analysis_type: Literal["preliminary"] = "preliminary"


class CategoryAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str = ""


class ClaimDraft(BaseModel):
    text: str
    status: ClaimStatus
    is_specific: bool = True
    needs_freshness_check: bool = False
    related_citations: list[str] = Field(default_factory=list)
    note: str = ""


class TrustAnalysisDraft(BaseModel):
    claims: list[ClaimDraft] = Field(default_factory=list)
    claim_support: CategoryAssessment
    source_quality: CategoryAssessment
    citation_accuracy: CategoryAssessment
    freshness: CategoryAssessment
    bias_context: CategoryAssessment
    headline: str = ""
    support_summary: str = ""


class ClaimSourceMatchItem(BaseModel):
    claim_text: str
    matched_source: str | None = None
    support_label: SupportLabel
    evidence_note: str = ""


class ClaimMatchingDraft(BaseModel):
    matches: list[ClaimSourceMatchItem] = Field(default_factory=list)
