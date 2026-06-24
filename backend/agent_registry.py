"""Registry of all specialist agents — used by orchestrator and streaming."""

from collections.abc import Callable

from backend.agents import (
    run_correctness_agent,
    run_performance_agent,
    run_readability_agent,
    run_security_agent,
    run_test_coverage_agent,
)
from backend.models import AgentFindingReport

AgentRunner = Callable[[str, str, str], AgentFindingReport]

AGENT_RUNNERS: list[tuple[str, AgentRunner]] = [
    ("Security Agent", run_security_agent),
    ("Correctness Agent", run_correctness_agent),
    ("Readability Agent", run_readability_agent),
    ("Performance Agent", run_performance_agent),
    ("Test Coverage Agent", run_test_coverage_agent),
]
