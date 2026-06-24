"""Pydantic models for AI response trust analysis (/api/analyze)."""

from typing import Literal

from pydantic import BaseModel, Field


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


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, description="Full AI response text")
    urls: list[str] = Field(default_factory=list, description="Cited URLs extracted from the response")
    source: Literal["chatgpt", "google_ai", "other"] = Field(default="chatgpt")


class CategoryScore(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str = ""


class ClaimAnalysis(BaseModel):
    text: str
    status: ClaimStatus
    citations: list[str] = Field(default_factory=list)
    note: str = ""


class AnalyzeResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    categories: dict[str, CategoryScore]
    claims: list[ClaimAnalysis] = Field(default_factory=list)
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
