"""Offline demo report when API quota is unavailable (reliable competition demos)."""

import re

from backend.models import (
    ActionItem,
    AgentFindingReport,
    Finding,
    ReviewReport,
    Severity,
)
from backend.review_weights import compute_weighted_overall_score

AGENT_PERSPECTIVES = {
    "Security Agent": "Security vulnerabilities and unsafe patterns",
    "Correctness Agent": "Bugs, logic errors, and edge cases",
    "Readability Agent": "Naming, structure, and maintainability",
    "Performance Agent": "Efficiency and anti-patterns",
    "Test Coverage Agent": "Testing and testability",
}

SEVERITY_PENALTY = {
    Severity.CRITICAL: 35,
    Severity.HIGH: 22,
    Severity.MEDIUM: 12,
    Severity.LOW: 6,
    Severity.INFO: 2,
}

VERDICT_THRESHOLDS = (
    (70, "approve"),
    (45, "request_changes"),
    (0, "reject"),
)


def _score_from_findings(findings: list[Finding]) -> int:
    if not findings:
        return 88
    penalty = 0.0
    for index, finding in enumerate(findings):
        multiplier = 1 + (index * 0.2)
        penalty += SEVERITY_PENALTY[finding.severity] * multiplier
    penalty = min(95, penalty)
    return max(5, round(100 - penalty))


def _first_match_hint(code: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, code, re.IGNORECASE | re.MULTILINE)
        if match:
            line_no = code[: match.start()].count("\n") + 1
            snippet = match.group(0).strip().split("\n", 1)[0][:60]
            return f"line {line_no}: {snippet}"
    return None


def _symbol_near_line(code: str, line_hint: str | None, language: str) -> str:
    if not line_hint:
        return "this code"
    match = re.search(r"line (\d+)", line_hint)
    if not match:
        return "this code"
    line_no = int(match.group(1))
    lines = code.splitlines()
    for idx in range(min(line_no, len(lines)) - 1, -1, -1):
        line = lines[idx]
        if language == "python":
            fn = re.search(r"def\s+(\w+)", line)
            if fn:
                return fn.group(1)
        if language in {"javascript", "typescript", "other"}:
            fn = re.search(r"function\s+(\w+)|(?:export\s+)?(?:async\s+)?function\s+(\w+)", line)
            if fn:
                return fn.group(1) or fn.group(2)
            fn = re.search(r"(?:export\s+)?(?:async\s+)?(\w+)\s*\(", line)
            if fn and fn.group(1) not in {"if", "for", "while", "switch"}:
                return fn.group(1)
        if language == "java":
            fn = re.search(r"(?:public|private|protected)?\s+\w+\s+(\w+)\s*\(", line)
            if fn:
                return fn.group(1)
        if language == "go":
            fn = re.search(r"func\s+(?:\([^)]+\)\s+)?(\w+)", line)
            if fn:
                return fn.group(1)
    return "this code"


def _enrich_finding(finding: Finding, code: str, language: str) -> Finding:
    sym = _symbol_near_line(code, finding.line_hint, language)
    copy = {
        "SQL injection risk": (
            f"In `{sym}()`, user-controlled input is embedded in a SQL string. "
            "An attacker could bypass authentication or read arbitrary rows using payloads like `' OR '1'='1`.",
            "Use parameterized queries with bound placeholders instead of string interpolation.",
        ),
        "Arbitrary code execution via eval()": (
            f"`{sym}()` passes untrusted input to `eval()`, which executes arbitrary JavaScript. "
            "A malicious payload can exfiltrate secrets or hijack the server process.",
            "Parse structured input with `JSON.parse` and validate against a strict schema; never eval user input.",
        ),
        "Arbitrary code execution via exec()": (
            f"`{sym}()` uses `exec()` on data that may be attacker-controlled, enabling full code execution.",
            "Replace `exec()` with safe parsing (`json.loads`, config loaders, or whitelisted operations).",
        ),
        "Hardcoded secret in source": (
            f"A secret is hardcoded near `{sym}()`. Anyone with repo access can extract it; it also leaks via logs and stack traces.",
            "Load secrets from environment variables or a secret manager and rotate any exposed values.",
        ),
        "Path traversal risk": (
            f"`{sym}()` builds a filesystem path from user input without sanitization. "
            "Attackers can request `../../etc/passwd` to read files outside the intended directory.",
            "Allowlist filenames, strip `..` segments, and resolve paths under a trusted root before reading.",
        ),
        "Command injection risk": (
            f"`{sym}()` passes external input to a shell command. Attackers can chain commands with `; rm -rf /`.",
            "Use argument arrays (no shell), validate input against a strict allowlist, and avoid string concatenation.",
        ),
        "Script engine executes user input": (
            f"`{sym}()` evaluates caller-supplied scripts via a script engine, equivalent to arbitrary code execution.",
            "Remove dynamic script evaluation or run it in an isolated sandbox with no filesystem/network access.",
        ),
        "Cross-site scripting (XSS) risk": (
            f"`{sym}()` renders user content as HTML without escaping. Attackers can inject `<script>` tags to steal sessions.",
            "Escape all dynamic output or use a template engine with contextual auto-escaping enabled.",
        ),
        "Weak password hashing": (
            f"`{sym}()` uses MD5 for credentials. MD5 is fast to brute-force and unsuitable for passwords or tokens.",
            "Switch to bcrypt, scrypt, or Argon2 with a unique salt per credential.",
        ),
        "Sensitive data in logs": (
            f"`{sym}()` writes secrets or tokens to logs. Logs are often broadly accessible and retained long-term.",
            "Log only non-sensitive identifiers; redact tokens and never log raw passwords.",
        ),
        "Off-by-one loop bounds": (
            f"The loop in `{sym}()` iterates one index past the end of the collection, causing runtime errors or wrong totals.",
            "Use `range(len(items))`, `i < items.length`, or iterate the collection directly.",
        ),
        "Ignored error return values": (
            f"`{sym}()` discards errors (`_`), so failures fail silently and callers assume success.",
            "Handle or propagate errors explicitly and return a failure response when operations do not succeed.",
        ),
        "Unchecked lookup may fail": (
            f"`{sym}()` indexes a map/dict without checking membership. Missing keys raise exceptions or return `undefined`.",
            "Validate the key first, use `.get()` with a default, or return a clear not-found error.",
        ),
        "No visible unit tests": (
            "Critical paths in this submission have no accompanying tests, so regressions will reach production unnoticed.",
            "Add unit tests for happy paths, invalid input, and each security-sensitive branch named in findings.",
        ),
        "New database connection per call": (
            f"`{sym}()` opens a new database connection on every call, adding latency and risking connection exhaustion under load.",
            "Reuse a connection pool or inject a shared client created at application startup.",
        ),
        "Unbounded worker goroutines": (
            f"`{sym}()` spawns a large number of goroutines without backpressure, which can exhaust memory under traffic spikes.",
            "Use a bounded worker pool with a job queue and ensure workers exit when the queue closes.",
        ),
        "Cache without eviction policy": (
            f"The cache in `{sym}()` never expires entries, so memory grows unbounded and stale data may be served indefinitely.",
            "Add TTL, LRU eviction, or explicit invalidation when underlying data changes.",
        ),
    }
    if finding.title in copy:
        description, recommendation = copy[finding.title]
        return finding.model_copy(update={"description": description, "recommendation": recommendation})
    return finding


def _enrich_findings(code: str, language: str, findings: list[Finding]) -> list[Finding]:
    return [_enrich_finding(f, code, language) for f in findings]


def _count_functions(code: str, language: str) -> int:
    if language in {"python"}:
        return len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))
    if language in {"javascript", "typescript"}:
        return len(re.findall(r"\bfunction\s+\w+", code)) + len(
            re.findall(r"\b(?:async\s+)?\w+\s*\([^)]*\)\s*(?::\s*\w+)?\s*{", code)
        )
    if language == "java":
        return len(re.findall(r"\b(?:public|private|protected)?\s*\w+\s+\w+\s*\(", code))
    if language == "go":
        return len(re.findall(r"^func\s+(?:\([^)]+\)\s+)?\w+", code, re.MULTILINE))
    return len(re.findall(r"\bfunction\s+\w+", code))


def _detect_security_findings(code: str, language: str) -> list[Finding]:
    findings: list[Finding] = []

    sql_patterns = [
        r'f["\'].*SELECT.*\{',
        r'["\'].*SELECT.*["\']\s*\+',
        r"fmt\.Sprintf\([^)]*SELECT",
        r"`SELECT[^`]*\$\{",
        r'query\s*=\s*["\'].*\+',
    ]
    if any(re.search(p, code, re.IGNORECASE | re.DOTALL) for p in sql_patterns):
        findings.append(
            Finding(
                title="SQL injection risk",
                description="User input appears interpolated directly into SQL query strings.",
                severity=Severity.CRITICAL,
                line_hint=_first_match_hint(code, sql_patterns),
                recommendation="Use parameterized queries or an ORM with bound parameters.",
            )
        )

    if re.search(r"\beval\s*\(", code):
        findings.append(
            Finding(
                title="Arbitrary code execution via eval()",
                description="eval() executes untrusted strings as code.",
                severity=Severity.CRITICAL,
                line_hint=_first_match_hint(code, [r"\beval\s*\("]),
                recommendation="Parse structured input with JSON/schema validation instead of eval().",
            )
        )

    if re.search(r"\bexec\s*\(", code) and language == "python":
        findings.append(
            Finding(
                title="Arbitrary code execution via exec()",
                description="exec() can run attacker-controlled code.",
                severity=Severity.CRITICAL,
                line_hint=_first_match_hint(code, [r"\bexec\s*\("]),
                recommendation="Remove exec(); use safe parsers or whitelisted operations.",
            )
        )

    if re.search(
        r'(SECRET_KEY|API_KEY|API_TOKEN|ADMIN_TOKEN|ServiceToken|SecretKey|sk-live|hardcoded-secret)\s*[=:]',
        code,
        re.IGNORECASE,
    ):
        findings.append(
            Finding(
                title="Hardcoded secret in source",
                description="Credentials or API keys are embedded directly in code.",
                severity=Severity.CRITICAL,
                line_hint=_first_match_hint(
                    code,
                    [
                        r'(SECRET_KEY|API_KEY|API_TOKEN|ADMIN_TOKEN|ServiceToken|SecretKey|sk-live|hardcoded-secret)\s*[=:]',
                    ],
                ),
                recommendation="Load secrets from environment variables or a secret manager.",
            )
        )

    path_patterns = [
        r"send_file\s*\(",
        r"os\.ReadFile\s*\(",
        r"filepath\.Join\s*\([^)]*Query",
        r'UPLOAD_DIR\s*\+\s*["\']/',
        r'readFileSync\s*\(',
        r'Paths\.get\s*\([^)]*,\s*\w+\)',
        r'UPLOAD_ROOT\s*\+\s*["\']/',
        r'read_bytes\s*\(',
    ]
    if any(re.search(p, code, re.IGNORECASE) for p in path_patterns):
        findings.append(
            Finding(
                title="Path traversal risk",
                description="File paths may be built from unsanitized user input.",
                severity=Severity.HIGH,
                line_hint=_first_match_hint(code, path_patterns),
                recommendation="Validate filenames, reject .. segments, and resolve paths inside a trusted root.",
            )
        )

    if re.search(r"Runtime\.getRuntime\(\)\.exec|generate-report\.sh|exec\.Command\s*\(", code):
        findings.append(
            Finding(
                title="Command injection risk",
                description="Shell commands are built with unsanitized external input.",
                severity=Severity.CRITICAL,
                line_hint=_first_match_hint(
                    code,
                    [r"Runtime\.getRuntime\(\)\.exec", r"generate-report", r"exec\.Command\s*\("],
                ),
                recommendation="Use ProcessBuilder with argument arrays and strict input allowlists.",
            )
        )

    if re.search(r"engine\.eval\s*\(", code):
        findings.append(
            Finding(
                title="Script engine executes user input",
                description="A scripting engine evaluates strings that may come from callers.",
                severity=Severity.CRITICAL,
                line_hint=_first_match_hint(code, [r"engine\.eval\s*\("]),
                recommendation="Remove dynamic script execution or restrict to a hardened sandbox.",
            )
        )

    if re.search(r"innerHTML|res\.send\s*\(\s*`<|f[\"']<(?:section|div|article)", code):
        findings.append(
            Finding(
                title="Cross-site scripting (XSS) risk",
                description="Untrusted data may be rendered as HTML without escaping.",
                severity=Severity.HIGH,
                line_hint=_first_match_hint(code, [r"innerHTML", r"res\.send\s*\(\s*`<"]),
                recommendation="Escape output or use a templating engine with auto-escaping.",
            )
        )

    if re.search(
        r"MessageDigest\.getInstance\([\"']MD5[\"']\)|hashlib\.md5|crypto/md5",
        code,
        re.IGNORECASE,
    ):
        findings.append(
            Finding(
                title="Weak password hashing",
                description="MD5 is not suitable for password or token comparison.",
                severity=Severity.MEDIUM,
                line_hint=_first_match_hint(code, [r"MD5", r"hashlib\.md5", r"crypto/md5"]),
                recommendation="Use bcrypt, scrypt, or Argon2 with a unique salt per password.",
            )
        )

    if re.search(
        r"logging\.(info|debug|warning).*(token|password|secret)|console\.log\s*\([^)]*(token|Token|validat)",
        code,
        re.IGNORECASE,
    ):
        findings.append(
            Finding(
                title="Sensitive data in logs",
                description="Tokens or secrets may be written to application logs.",
                severity=Severity.MEDIUM,
                line_hint=_first_match_hint(
                    code,
                    [r"logging\.(info|debug|warning)", r"console\.log\s*\("],
                ),
                recommendation="Redact secrets before logging and avoid logging raw credentials.",
            )
        )

    return findings


def _detect_correctness_findings(code: str, language: str) -> list[Finding]:
    findings: list[Finding] = []

    off_by_one_patterns = [
        r"range\s*\(\s*len\s*\([^)]+\)\s*\+\s*1\s*\)",
        r"<=\s*items\.length",
        r"<=\s*len\s*\(\s*items\s*\)",
        r"i\s*<=\s*len\s*\(\s*items\s*\)",
        r"for\s*\(\s*int\s+i\s*=\s*0;\s*i\s*<=\s*items\.length",
    ]
    if any(re.search(p, code) for p in off_by_one_patterns):
        findings.append(
            Finding(
                title="Off-by-one loop bounds",
                description="A loop iterates one step past the valid index range.",
                severity=Severity.HIGH,
                line_hint=_first_match_hint(code, off_by_one_patterns),
                recommendation="Use strict less-than bounds or iterate collections directly.",
            )
        )

    if re.search(r",\s*_\s*[:=]", code):
        findings.append(
            Finding(
                title="Ignored error return values",
                description="Errors are discarded instead of being handled or propagated.",
                severity=Severity.MEDIUM,
                line_hint=_first_match_hint(code, [r",\s*_\s*[:=]"]),
                recommendation="Check returned errors and fail safely when operations do not succeed.",
            )
        )

    if re.search(r"users\[|users\.get\(|getUser\s*\(", code) and not re.search(
        r"if\s+.*in\s+users|\.get\([^)]*,\s*None\)|containsKey|ok\s*:=",
        code,
    ):
        findings.append(
            Finding(
                title="Unchecked lookup may fail",
                description="Dictionary or map access can fail for missing keys or invalid IDs.",
                severity=Severity.MEDIUM,
                line_hint=_first_match_hint(code, [r"users\[", r"getUser\s*\("]),
                recommendation="Validate keys before access and return explicit not-found errors.",
            )
        )

    if re.search(r"Object\.assign\s*\(\s*globalThis", code):
        findings.append(
            Finding(
                title="Prototype pollution risk",
                description="Arbitrary object properties may be merged onto global scope.",
                severity=Severity.HIGH,
                line_hint=_first_match_hint(code, [r"Object\.assign\s*\(\s*globalThis"]),
                recommendation="Validate object shape and block __proto__ / constructor keys.",
            )
        )

    return findings


def _detect_readability_findings(code: str, language: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = [line for line in code.splitlines() if line.strip()]
    function_count = _count_functions(code, language)

    has_docs = bool(
        re.search(r'"""|\'\'\'|/\*\*|^\s*#|^\s*//', code, re.MULTILINE)
    )
    if function_count >= 1 and not has_docs:
        findings.append(
            Finding(
                title="Missing documentation",
                description="Functions lack docstrings or comments explaining behavior.",
                severity=Severity.LOW,
                line_hint="top of file",
                recommendation="Add brief docstrings and type hints where they clarify intent.",
            )
        )

    if len(lines) > 35 and code.count("\n\n") < 2:
        findings.append(
            Finding(
                title="Dense code block",
                description="The snippet is long with little visual separation between responsibilities.",
                severity=Severity.LOW,
                line_hint="overall structure",
                recommendation="Split into smaller functions and group related logic.",
            )
        )

    if re.search(r"\b(data|tmp|foo|bar)\b", code):
        findings.append(
            Finding(
                title="Non-descriptive naming",
                description="Some identifiers do not clearly describe their purpose.",
                severity=Severity.LOW,
                line_hint=_first_match_hint(code, [r"\b(data|tmp|foo|bar)\b"]),
                recommendation="Rename variables and functions to reflect domain meaning.",
            )
        )

    return findings


def _detect_performance_findings(code: str, language: str) -> list[Finding]:
    findings: list[Finding] = []

    if re.search(r"sqlite3\.connect|sql\.Open|DriverManager\.getConnection", code):
        findings.append(
            Finding(
                title="New database connection per call",
                description="A fresh DB connection is opened on each request or function call.",
                severity=Severity.LOW,
                line_hint=_first_match_hint(
                    code,
                    [r"sqlite3\.connect", r"sql\.Open", r"DriverManager\.getConnection"],
                ),
                recommendation="Reuse a connection pool or shared client across requests.",
            )
        )

    if re.search(r"for\s+.*:\s*\n\s*for\s+", code) or code.count("for ") >= 3:
        findings.append(
            Finding(
                title="Nested or repeated loops",
                description="Multiple nested loops may scale poorly on larger inputs.",
                severity=Severity.MEDIUM,
                line_hint="loop structure",
                recommendation="Look for map/set lookups or single-pass algorithms where possible.",
            )
        )

    if re.search(r"for\s+i\s*:=\s*0;\s*i\s*<\s*1000", code):
        findings.append(
            Finding(
                title="Unbounded worker goroutines",
                description="Many goroutines are started without a worker limit or lifecycle control.",
                severity=Severity.MEDIUM,
                line_hint=_first_match_hint(code, [r"for\s+i\s*:=\s*0;\s*i\s*<\s*1000"]),
                recommendation="Use a bounded worker pool and ensure goroutines can exit cleanly.",
            )
        )

    if re.search(r"let\s+cache\s*=\s*null|cache\s*=\s*\{\}", code) and not re.search(
        r"ttl|expire|invalidate|LRU", code, re.IGNORECASE
    ):
        findings.append(
            Finding(
                title="Cache without eviction policy",
                description="In-memory cache may grow without bounds or staleness controls.",
                severity=Severity.LOW,
                line_hint=_first_match_hint(code, [r"cache\s*=", r"let\s+cache"]),
                recommendation="Add TTL, size limits, or explicit invalidation for cached entries.",
            )
        )

    return findings


def _detect_test_findings(code: str, language: str) -> list[Finding]:
    findings: list[Finding] = []
    function_count = _count_functions(code, language)
    test_markers = re.search(
        r"\b(?:test_|describe\(|it\(|assert|pytest|unittest|@Test)",
        code,
        re.IGNORECASE,
    )

    if function_count == 0:
        return findings

    if not test_markers:
        severity = Severity.HIGH if function_count >= 2 else Severity.MEDIUM
        findings.append(
            Finding(
                title="No visible unit tests",
                description=f"{function_count} function(s) appear untested in the submitted snippet.",
                severity=severity,
                line_hint="entire submission",
                recommendation="Add tests for happy paths, invalid input, and security-sensitive branches.",
            )
        )
    elif function_count > 3:
        findings.append(
            Finding(
                title="Limited test coverage for complexity",
                description="Multiple functions are present but only basic test markers were detected.",
                severity=Severity.LOW,
                line_hint="test suite",
                recommendation="Add edge-case tests for error paths and boundary conditions.",
            )
        )

    if re.search(r"\b(global|window\.)\w+\s*=", code) or "globalThis" in code:
        findings.append(
            Finding(
                title="Global mutable state hurts testability",
                description="Shared global state makes isolated unit tests harder to write.",
                severity=Severity.MEDIUM,
                line_hint=_first_match_hint(code, [r"global\w*\s*=", r"globalThis"]),
                recommendation="Inject dependencies and avoid module-level mutable singletons.",
            )
        )

    return findings


def _build_agent_report(
    agent_name: str,
    findings: list[Finding],
    code: str,
    language: str,
) -> AgentFindingReport:
    findings = _enrich_findings(code, language, findings)
    score = _score_from_findings(findings)
    if not findings:
        summary = "Reviewed this area — no significant issues stood out in the submitted snippet."
    else:
        lead = findings[0].title
        if score < 50:
            summary = (
                f"{len(findings)} issue(s) need attention before merge; "
                f"start with {lead.lower()}."
            )
        else:
            summary = (
                f"{len(findings)} minor issue(s) noted — "
                f"main concern is {lead.lower()}."
            )

    return AgentFindingReport(
        agent_name=agent_name,
        perspective=AGENT_PERSPECTIVES[agent_name],
        score=score,
        summary=summary,
        findings=findings,
    )


def _verdict_for_score(score: int) -> str:
    for threshold, verdict in VERDICT_THRESHOLDS:
        if score >= threshold:
            return verdict
    return "reject"


def _build_action_items(agent_reports: list[AgentFindingReport]) -> list[ActionItem]:
    items: list[ActionItem] = []
    seen: set[str] = set()

    for report in agent_reports:
        for finding in report.findings:
            key = finding.title.lower()
            if key in seen:
                continue
            seen.add(key)
            if finding.severity in (Severity.CRITICAL, Severity.HIGH):
                priority = "must_fix"
            elif finding.severity == Severity.MEDIUM:
                priority = "should_fix"
            else:
                priority = "nice_to_have"
            items.append(
                ActionItem(
                    priority=priority,
                    category=report.agent_name.replace(" Agent", ""),
                    action=finding.recommendation,
                    rationale=finding.description,
                )
            )
            if len(items) >= 6:
                return items
    return items


def _build_strengths(code: str, language: str, agent_reports: list[AgentFindingReport]) -> list[str]:
    strengths: list[str] = []
    line_count = len([line for line in code.splitlines() if line.strip()])

    if line_count <= 25:
        strengths.append("Snippet is short and easy to review in one pass.")
    if all(report.score >= 70 for report in agent_reports[:3]):
        strengths.append("No critical issues flagged by security, correctness, or readability agents.")
    if _count_functions(code, language) <= 3 and line_count < 40:
        strengths.append("Functions are small and responsibilities are relatively focused.")
    if not strengths:
        strengths.append("Issues are localized and actionable with clear remediation paths.")
    return strengths[:3]


def _build_markdown(
    language: str,
    overall_score: int,
    verdict: str,
    executive_summary: str,
    strengths: list[str],
    action_items: list[ActionItem],
    agent_reports: list[AgentFindingReport],
) -> str:
    sections = [
        "## Executive Summary",
        executive_summary,
        "",
        "## Verdict & Score",
        f"**Verdict:** {verdict.replace('_', ' ').title()} · **Score:** {overall_score}/100",
        "",
        "## Strengths",
    ]
    sections.extend(f"- {s}" for s in strengths)
    sections.extend(["", "## Action Items"])
    for priority, label in (
        ("must_fix", "Must fix"),
        ("should_fix", "Should fix"),
        ("nice_to_have", "Nice to have"),
    ):
        group = [item for item in action_items if item.priority == priority]
        if not group:
            continue
        sections.append(f"\n### {label}")
        for item in group:
            sections.append(f"- **{item.category}:** {item.action} — _{item.rationale}_")
    sections.extend(["", "## Detailed Findings by Agent"])
    for report in agent_reports:
        sections.extend(["", f"### {report.agent_name} ({report.score}/100)", report.summary])
        if not report.findings:
            sections.append("- No issues flagged.")
            continue
        for finding in report.findings:
            sections.append(
                f"- **{finding.title}** ({finding.severity.value}): {finding.description} "
                f"**Fix:** {finding.recommendation}"
            )
    return "\n".join(sections)


def _executive_summary(
    agent_reports: list[AgentFindingReport],
    language: str,
    context: str,
    overall_score: int,
    verdict: str,
) -> str:
    issue_count = sum(len(r.findings) for r in agent_reports)
    critical = [
        f
        for r in agent_reports
        for f in r.findings
        if f.severity == Severity.CRITICAL
    ]
    highs = [f for r in agent_reports for f in r.findings if f.severity == Severity.HIGH]

    topic = ""
    if context and "—" in context:
        topic = context.split("—", 1)[-1].strip().rstrip(".")
    elif context:
        topic = context.replace("Demo:", "").strip().rstrip(".")

    if critical:
        lead = critical[0].title.lower()
        opener = (
            f"This {language} submission has {len(critical)} critical issue(s), "
            f"led by {lead}. Score: {overall_score}/100 ({verdict.replace('_', ' ')})."
        )
    elif highs:
        opener = (
            f"This {language} code is workable but has {len(highs)} high-severity issue(s) "
            f"to address before merge. Score: {overall_score}/100."
        )
    elif overall_score >= 75:
        opener = (
            f"This {language} snippet looks solid overall ({overall_score}/100). "
            f"Only {issue_count} minor follow-up(s) were noted."
        )
    else:
        opener = (
            f"This {language} review found {issue_count} issue(s) across five dimensions. "
            f"Score: {overall_score}/100."
        )

    if topic:
        opener += f" Reviewed as: {topic}."
    return opener


def demo_review_report(code: str, language: str, context: str) -> ReviewReport:
    """Build a demo review with scores that reflect the submitted code."""
    agent_reports = [
        _build_agent_report("Security Agent", _detect_security_findings(code, language), code, language),
        _build_agent_report("Correctness Agent", _detect_correctness_findings(code, language), code, language),
        _build_agent_report("Readability Agent", _detect_readability_findings(code, language), code, language),
        _build_agent_report("Performance Agent", _detect_performance_findings(code, language), code, language),
        _build_agent_report("Test Coverage Agent", _detect_test_findings(code, language), code, language),
    ]
    overall_score = compute_weighted_overall_score(agent_reports)
    verdict = _verdict_for_score(overall_score)
    strengths = _build_strengths(code, language, agent_reports)
    action_items = _build_action_items(agent_reports)
    executive_summary = _executive_summary(
        agent_reports, language, context, overall_score, verdict
    )

    return ReviewReport(
        overall_score=overall_score,
        verdict=verdict,
        executive_summary=executive_summary,
        strengths=strengths,
        action_items=action_items,
        agent_reports=agent_reports,
        markdown_report=_build_markdown(
            language,
            overall_score,
            verdict,
            executive_summary,
            strengths,
            action_items,
            agent_reports,
        ),
    )
