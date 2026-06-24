"""Orchestrates multi-agent code review via Google ADK or direct Gemini fallback."""

import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from google.genai import errors as genai_errors

from backend.adk_runner import review_code_with_adk
from backend.agent_registry import AGENT_RUNNERS
from backend.agents import get_model_name
from backend.coordinator import run_coordinator
from backend.demo_report import demo_review_report
from backend.gemini_client import use_vertex_ai
from backend.models import AgentFindingReport, PipelineType, ReviewReport, ReviewResponse
from backend.prompts import AGENT_ORDER
from backend.validation import validate_submission

MAX_PARALLEL_AGENTS = 5


def _demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")


def _use_adk() -> bool:
    return os.getenv("USE_ADK", "true").lower() in ("1", "true", "yes")


def _google_technologies(pipeline: PipelineType) -> list[str]:
    tech = ["Gemini API"]
    if use_vertex_ai():
        tech.append("Vertex AI")
    if pipeline == "adk":
        tech.append("Google ADK")
    return tech


def _sort_reports(reports: list[AgentFindingReport]) -> list[AgentFindingReport]:
    order = {name: idx for idx, name in enumerate(AGENT_ORDER)}
    return sorted(reports, key=lambda r: order.get(r.agent_name, 99))


def _wrap(report: ReviewReport, pipeline: PipelineType, started: float) -> ReviewResponse:
    return ReviewResponse(
        report=report,
        pipeline=pipeline,
        model=get_model_name(),
        duration_ms=int((time.perf_counter() - started) * 1000),
        google_technologies=_google_technologies(pipeline),
    )


def _run_agents_parallel(code: str, language: str, context: str) -> list[AgentFindingReport]:
    reports: list[AgentFindingReport] = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_AGENTS) as pool:
        futures = [pool.submit(fn, code, language, context) for _, fn in AGENT_RUNNERS]
        for future in as_completed(futures):
            reports.append(future.result())
    return _sort_reports(reports)


def _is_recoverable_api_error(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.ClientError):
        msg = str(exc)
        return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "API_KEY_INVALID" in msg
    for current in _exception_chain(exc):
        module = type(current).__module__
        name = type(current).__name__
        msg = str(current)
        if module.startswith(("httpx", "httpcore")) and name in (
            "ConnectError",
            "ConnectTimeout",
            "ReadTimeout",
            "RemoteProtocolError",
            "NetworkError",
            "TransportError",
        ):
            return True
        if isinstance(current, RuntimeError) and (
            "GEMINI_API_KEY is not set" in msg
            or "ADK pipeline finished without a coordinator report" in msg
        ):
            return True
    return False


def _exception_chain(exc: Exception) -> Iterator[BaseException]:
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def review_code(code: str, language: str = "python", context: str = "") -> ReviewResponse:
    validate_submission(code, language)
    started = time.perf_counter()

    if _demo_mode_enabled():
        return _wrap(demo_review_report(code, language, context), "demo", started)

    if _use_adk():
        try:
            report = review_code_with_adk(code, language, context)
            return _wrap(report, "adk", started)
        except Exception as exc:
            if not _is_recoverable_api_error(exc):
                raise

    try:
        reports = _run_agents_parallel(code, language, context)
        report = run_coordinator(code, language, context, reports)
        return _wrap(report, "gemini", started)
    except Exception as exc:
        if _is_recoverable_api_error(exc):
            report = demo_review_report(code, language, context)
            report.executive_summary += (
                " (Live API unavailable — demo report shown. Check API key/quota or Vertex AI.)"
            )
            return _wrap(report, "demo", started)
        raise


def review_code_stream(
    code: str,
    language: str = "python",
    context: str = "",
) -> Iterator[dict[str, Any]]:
    validate_submission(code, language)
    started = time.perf_counter()

    yield {"type": "status", "message": "Starting 5-agent review…"}

    if _demo_mode_enabled():
        for name in AGENT_ORDER:
            yield {"type": "agent_start", "agent": name}
        report = demo_review_report(code, language, context)
        for agent_report in report.agent_reports:
            yield {"type": "agent_complete", "report": agent_report.model_dump()}
        yield {"type": "coordinator_start", "message": "Coordinator synthesizing findings…"}
        yield {"type": "complete", "data": _wrap(report, "demo", started).model_dump()}
        return

    yield {"type": "pipeline", "pipeline": "gemini"}

    for name in AGENT_ORDER:
        yield {"type": "agent_start", "agent": name}

    completed: list[AgentFindingReport] = []
    try:
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_AGENTS) as pool:
            future_map = {
                pool.submit(fn, code, language, context): label for label, fn in AGENT_RUNNERS
            }
            for future in as_completed(future_map):
                report = future.result()
                completed.append(report)
                yield {"type": "agent_complete", "report": report.model_dump()}

        yield {"type": "coordinator_start", "message": "Coordinator synthesizing findings…"}
        final = run_coordinator(code, language, context, _sort_reports(completed))
        yield {"type": "complete", "data": _wrap(final, "gemini", started).model_dump()}
    except Exception as exc:
        if _is_recoverable_api_error(exc):
            report = demo_review_report(code, language, context)
            yield {"type": "fallback", "message": "API quota exhausted — using demo report"}
            yield {"type": "complete", "data": _wrap(report, "demo", started).model_dump()}
        else:
            yield {"type": "error", "message": str(exc)}
