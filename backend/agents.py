"""Specialized review sub-agents powered by Gemini."""

from google.genai import types

from backend.gemini_client import generate_with_fallback, get_client, get_model
from backend.models import AgentFindingReport
from backend.prompts import AGENT_KEYS
from backend.validation import format_review_input, validate_submission


def _run_agent(instruction: str, code: str, language: str, context: str) -> AgentFindingReport:
    validate_submission(code, language)
    client = get_client()
    response = generate_with_fallback(
        client,
        contents=format_review_input(code, language, context),
        config=types.GenerateContentConfig(
            system_instruction=instruction,
            response_mime_type="application/json",
            response_schema=AgentFindingReport,
            temperature=0.2,
        ),
    )
    return AgentFindingReport.model_validate_json(response.text)


def run_security_agent(code: str, language: str, context: str = "") -> AgentFindingReport:
    return _run_agent(AGENT_KEYS["security"][1], code, language, context)


def run_correctness_agent(code: str, language: str, context: str = "") -> AgentFindingReport:
    return _run_agent(AGENT_KEYS["correctness"][1], code, language, context)


def run_readability_agent(code: str, language: str, context: str = "") -> AgentFindingReport:
    return _run_agent(AGENT_KEYS["readability"][1], code, language, context)


def run_performance_agent(code: str, language: str, context: str = "") -> AgentFindingReport:
    return _run_agent(AGENT_KEYS["performance"][1], code, language, context)


def run_test_coverage_agent(code: str, language: str, context: str = "") -> AgentFindingReport:
    return _run_agent(AGENT_KEYS["test_coverage"][1], code, language, context)


def get_model_name() -> str:
    return get_model()
