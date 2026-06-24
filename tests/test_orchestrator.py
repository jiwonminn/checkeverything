"""Tests for checkeverything orchestration and validation."""

import pytest

from backend.demo_report import demo_review_report
from backend.models import AgentFindingReport, ReviewResponse
from backend.orchestrator import _is_recoverable_api_error, _sort_reports, review_code
from backend.validation import validate_submission


SAMPLE = "def add(a, b):\n    return a + b\n"


def test_validate_empty_code_raises():
    with pytest.raises(ValueError, match="empty"):
        validate_submission("", "python")


def test_validate_oversized_code_raises():
    with pytest.raises(ValueError, match="too large"):
        validate_submission("x" * 60_000, "python")


def test_demo_mode_returns_response(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    result = review_code(SAMPLE, "python", "unit test")
    assert isinstance(result, ReviewResponse)
    assert result.pipeline == "demo"
    assert result.report.overall_score >= 0
    assert len(result.report.agent_reports) == 5


def test_adk_quota_error_falls_back_to_demo(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setenv("USE_ADK", "true")

    def raise_quota_error(*_args, **_kwargs):
        raise RuntimeError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr("backend.orchestrator.review_code_with_adk", raise_quota_error)
    monkeypatch.setattr("backend.orchestrator._run_agents_parallel", raise_quota_error)

    result = review_code(SAMPLE, "python", "unit test")
    assert result.pipeline == "demo"
    assert len(result.report.agent_reports) == 5


def test_demo_report_has_five_agents():
    report = demo_review_report(SAMPLE, "python", "test")
    assert len(report.agent_reports) == 5
    names = {a.agent_name for a in report.agent_reports}
    assert "Performance Agent" in names
    assert "Test Coverage Agent" in names


def test_demo_report_has_action_items():
    report = demo_review_report(SAMPLE, "python", "test")
    assert len(report.action_items) >= 1
    assert report.verdict in ("approve", "request_changes", "reject")


def test_agent_report_names_are_normalized():
    reports = [
        AgentFindingReport(
            agent_name="test_coverage_agent",
            perspective="tests",
            score=80,
            summary="ok",
            findings=[],
        )
    ]

    assert _sort_reports(reports)[0].agent_name == "Test Coverage Agent"


def test_missing_api_key_error_is_recoverable():
    error = RuntimeError(
        "GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey"
    )
    assert _is_recoverable_api_error(error)


def test_model_unavailable_error_is_recoverable():
    error = RuntimeError(
        "503 UNAVAILABLE. This model is currently experiencing high demand."
    )
    assert _is_recoverable_api_error(error)


def test_adk_no_report_error_is_recoverable():
    error = RuntimeError("ADK pipeline finished without a coordinator report.")
    assert _is_recoverable_api_error(error)


def test_network_error_in_exception_chain_is_recoverable():
    class ConnectError(Exception):
        __module__ = "httpx"

    error = RuntimeError("wrapped")
    error.__cause__ = ConnectError("nodename nor servname provided")

    assert _is_recoverable_api_error(error)
