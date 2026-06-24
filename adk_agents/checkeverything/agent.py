"""checkeverything multi-agent code review — Google ADK definition.

Run interactively:
  adk web adk_agents
  adk run adk_agents/checkeverything
"""

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from backend.gemini_client import get_model
from backend.models import AgentFindingReport, ReviewReport
from backend.prompts import (
    COORDINATOR_INSTRUCTION,
    CORRECTNESS_INSTRUCTION,
    PERFORMANCE_INSTRUCTION,
    READABILITY_INSTRUCTION,
    SECURITY_INSTRUCTION,
    TEST_COVERAGE_INSTRUCTION,
)

_MODEL = get_model()

security_agent = LlmAgent(
    name="security_agent",
    model=_MODEL,
    description="Flags security vulnerabilities and unsafe patterns.",
    instruction=SECURITY_INSTRUCTION,
    output_schema=AgentFindingReport,
    output_key="security_report",
)

correctness_agent = LlmAgent(
    name="correctness_agent",
    model=_MODEL,
    description="Finds bugs, logic errors, and edge-case failures.",
    instruction=CORRECTNESS_INSTRUCTION,
    output_schema=AgentFindingReport,
    output_key="correctness_report",
)

readability_agent = LlmAgent(
    name="readability_agent",
    model=_MODEL,
    description="Evaluates naming, structure, and maintainability.",
    instruction=READABILITY_INSTRUCTION,
    output_schema=AgentFindingReport,
    output_key="readability_report",
)

performance_agent = LlmAgent(
    name="performance_agent",
    model=_MODEL,
    description="Identifies inefficiencies and performance anti-patterns.",
    instruction=PERFORMANCE_INSTRUCTION,
    output_schema=AgentFindingReport,
    output_key="performance_report",
)

test_coverage_agent = LlmAgent(
    name="test_coverage_agent",
    model=_MODEL,
    description="Assesses test coverage and testability.",
    instruction=TEST_COVERAGE_INSTRUCTION,
    output_schema=AgentFindingReport,
    output_key="test_coverage_report",
)

parallel_review = ParallelAgent(
    name="parallel_specialists",
    description="Runs five specialist agents in parallel.",
    sub_agents=[
        security_agent,
        correctness_agent,
        readability_agent,
        performance_agent,
        test_coverage_agent,
    ],
)

coordinator_agent = LlmAgent(
    name="coordinator_agent",
    model=_MODEL,
    description="Synthesizes specialist findings into one actionable report.",
    instruction="""You are the Coordinator Agent for checkeverything.

Read all specialist reports in session state:
security_report, correctness_report, readability_report,
performance_report, test_coverage_report.

Also use the code submission from the user message.

"""
    + COORDINATOR_INSTRUCTION,
    output_schema=ReviewReport,
    output_key="final_report",
)

root_agent = SequentialAgent(
    name="checkeverything_root",
    description="Five parallel specialists then coordinator synthesis.",
    sub_agents=[parallel_review, coordinator_agent],
)
