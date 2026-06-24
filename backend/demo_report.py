"""Offline demo report when API quota is unavailable (reliable competition demos)."""

from backend.models import (
    ActionItem,
    AgentFindingReport,
    Finding,
    ReviewReport,
    Severity,
)


def demo_review_report(code: str, language: str, context: str) -> ReviewReport:
    security = AgentFindingReport(
        agent_name="Security Agent",
        perspective="Security vulnerabilities and unsafe patterns",
        score=35,
        summary="Multiple critical security issues including SQL injection and unsafe code execution.",
        findings=[
            Finding(
                title="SQL injection in login()",
                description="User input is interpolated directly into the SQL query string.",
                severity=Severity.CRITICAL,
                line_hint="login()",
                recommendation="Use parameterized queries: cursor.execute('SELECT ... WHERE username = ?', (username,))",
            ),
            Finding(
                title="Arbitrary code execution via exec()",
                description="save_config() passes user-controlled data to exec().",
                severity=Severity.CRITICAL,
                line_hint="save_config()",
                recommendation="Remove exec(); parse configuration with json.loads or a safe schema validator.",
            ),
        ],
    )
    correctness = AgentFindingReport(
        agent_name="Correctness Agent",
        perspective="Bugs, logic errors, and edge cases",
        score=42,
        summary="Off-by-one loop bug and incorrect max-finding logic for negative numbers.",
        findings=[
            Finding(
                title="Off-by-one in process_items()",
                description="Loop runs to len(items)+1, causing IndexError on the last iteration.",
                severity=Severity.HIGH,
                line_hint="process_items()",
                recommendation="Use range(len(items)) or iterate items directly.",
            ),
            Finding(
                title="find_max() fails for all-negative lists",
                description="Initial max_val=0 never updates when all values are negative.",
                severity=Severity.MEDIUM,
                line_hint="find_max()",
                recommendation="Initialize with nums[0] after checking the list is non-empty.",
            ),
        ],
    )
    readability = AgentFindingReport(
        agent_name="Readability Agent",
        perspective="Naming, structure, and maintainability",
        score=58,
        summary="Functions lack docstrings; mixed naming and global secret constant reduce clarity.",
        findings=[
            Finding(
                title="Missing function documentation",
                description="Public functions have no docstrings describing parameters or return values.",
                severity=Severity.LOW,
                recommendation="Add docstrings and type hints to each function.",
            ),
        ],
    )
    performance = AgentFindingReport(
        agent_name="Performance Agent",
        perspective="Efficiency and anti-patterns",
        score=62,
        summary="No major algorithmic bottlenecks, but repeated DB connections per login call add overhead.",
        findings=[
            Finding(
                title="New DB connection per login() call",
                description="sqlite3.connect() is called on every login without pooling or context manager reuse.",
                severity=Severity.LOW,
                line_hint="login()",
                recommendation="Use connection pooling or a context manager pattern for database access.",
            ),
        ],
    )
    test_coverage = AgentFindingReport(
        agent_name="Test Coverage Agent",
        perspective="Testing and testability",
        score=25,
        summary="No tests present. Critical auth and data-processing functions are untested.",
        findings=[
            Finding(
                title="No unit tests for auth or data functions",
                description="login(), process_items(), and find_max() have no test coverage for edge cases.",
                severity=Severity.HIGH,
                recommendation="Add pytest cases for valid login, SQL injection attempts, empty lists, and negative numbers.",
            ),
        ],
    )
    agent_reports = [security, correctness, readability, performance, test_coverage]
    markdown = f"""## Executive Summary
checkeverything found **critical security flaws** and **logic bugs** in this {language} submission.
The code should not be merged until SQL injection and exec() usage are removed.

## Verdict & Score
**Verdict:** Request Changes · **Score:** 38/100

## Strengths
- Functions are small and individually reviewable
- Uses standard library modules familiar to Python developers

## Action Items

### Must Fix
- Replace string-interpolated SQL with parameterized queries
- Remove exec() from save_config()
- Fix off-by-one error in process_items()

### Should Fix
- Correct find_max() for negative number lists
- Add input validation to divide()

## Detailed Findings by Agent

### Security Agent (35/100)
{security.summary}

### Correctness Agent (42/100)
{correctness.summary}

### Readability Agent (58/100)
{readability.summary}

### Performance Agent (62/100)
{performance.summary}

### Test Coverage Agent (25/100)
{test_coverage.summary}

---
*Demo mode report — enable live Gemini/ADK by setting a valid API key or Vertex AI credentials.*
"""
    return ReviewReport(
        overall_score=38,
        verdict="request_changes",
        executive_summary=(
            "Critical security issues (SQL injection, exec) and logic bugs (off-by-one loop) "
            "make this code unsafe to merge. Address must-fix items before shipping."
        ),
        strengths=[
            "Functions are small and easy to locate",
            "Uses familiar Python standard library modules",
        ],
        action_items=[
            ActionItem(
                priority="must_fix",
                category="Security",
                action="Use parameterized SQL queries in login()",
                rationale="Prevents SQL injection attacks",
            ),
            ActionItem(
                priority="must_fix",
                category="Security",
                action="Remove exec() from save_config()",
                rationale="Prevents arbitrary code execution",
            ),
            ActionItem(
                priority="must_fix",
                category="Correctness",
                action="Fix off-by-one loop in process_items()",
                rationale="Current code raises IndexError at runtime",
            ),
            ActionItem(
                priority="should_fix",
                category="Correctness",
                action="Fix find_max() for all-negative inputs",
                rationale="Returns incorrect result for valid inputs",
            ),
        ],
        agent_reports=agent_reports,
        markdown_report=markdown,
    )
