"""Pydantic models for structured agent outputs and final review report."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    title: str = Field(description="Short title for the finding")
    description: str = Field(description="Detailed explanation of the issue")
    severity: Severity
    line_hint: str | None = Field(
        default=None,
        description="Approximate line number or code snippet reference",
    )
    recommendation: str = Field(description="Concrete fix or improvement")


class AgentFindingReport(BaseModel):
    agent_name: str
    perspective: str
    score: int = Field(ge=0, le=100, description="0-100 quality score for this dimension")
    summary: str
    findings: list[Finding]


class ActionItem(BaseModel):
    priority: Literal["must_fix", "should_fix", "nice_to_have"]
    category: str
    action: str
    rationale: str


class ReviewReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    verdict: Literal["approve", "request_changes", "reject"]
    executive_summary: str
    strengths: list[str]
    action_items: list[ActionItem]
    agent_reports: list[AgentFindingReport]
    markdown_report: str


class ReviewWeights(BaseModel):
    security: int = Field(default=20, ge=0, le=100)
    correctness: int = Field(default=25, ge=0, le=100)
    readability: int = Field(default=15, ge=0, le=100)
    performance: int = Field(default=15, ge=0, le=100)
    test_coverage: int = Field(default=25, ge=0, le=100)


PipelineType = Literal["adk", "gemini", "demo"]


class ReviewResponse(BaseModel):
    """API response wrapper with execution metadata for transparency."""

    report: ReviewReport
    pipeline: PipelineType
    model: str
    duration_ms: int
    google_technologies: list[str]
    score_weights: dict[str, int] | None = Field(
        default=None,
        description="Normalized agent weight percentages used for overall_score",
    )
