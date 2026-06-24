"""Evaluation harness — measure agent finding recall on labeled samples."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from backend.orchestrator import review_code

EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"
SAMPLES_FILE = EVAL_DIR / "samples.json"


@dataclass
class SampleResult:
    sample_id: str
    passed: bool
    checks_passed: int
    checks_total: int
    pipeline: str
    details: list[str]


def _keyword_hit(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


def evaluate_sample(sample: dict, use_demo: bool = True) -> SampleResult:
    if use_demo:
        os.environ["DEMO_MODE"] = "true"

    path = Path(sample["file"])
    code = path.read_text(encoding="utf-8")
    response = review_code(code, sample.get("language", "python"), sample.get("context", ""))

    details: list[str] = []
    passed_checks = 0
    total = len(sample.get("expected", []))

    for check in sample.get("expected", []):
        agent_name = check["agent"]
        keywords = check["keywords"]
        agent_report = next(
            (r for r in response.report.agent_reports if r.agent_name == agent_name),
            None,
        )
        if not agent_report:
            details.append(f"FAIL {agent_name}: agent report missing")
            continue

        blob = agent_report.summary + " " + json.dumps([f.model_dump() for f in agent_report.findings])
        if _keyword_hit(blob, keywords):
            passed_checks += 1
            details.append(f"PASS {agent_name}: matched {keywords}")
        else:
            details.append(f"FAIL {agent_name}: expected keywords {keywords}")

    return SampleResult(
        sample_id=sample["id"],
        passed=passed_checks == total and total > 0,
        checks_passed=passed_checks,
        checks_total=total,
        pipeline=response.pipeline,
        details=details,
    )


def run_evaluation(use_demo: bool = True) -> dict:
    samples = json.loads(SAMPLES_FILE.read_text(encoding="utf-8"))
    results = [evaluate_sample(s, use_demo=use_demo) for s in samples]

    total_checks = sum(r.checks_total for r in results)
    passed_checks = sum(r.checks_passed for r in results)

    return {
        "samples": len(results),
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "recall": round(passed_checks / total_checks, 2) if total_checks else 0,
        "all_passed": all(r.passed for r in results),
        "results": [
            {
                "id": r.sample_id,
                "passed": r.passed,
                "score": f"{r.checks_passed}/{r.checks_total}",
                "pipeline": r.pipeline,
                "details": r.details,
            }
            for r in results
        ],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="checkeverything evaluation harness")
    parser.add_argument("--live", action="store_true", help="Use live API instead of demo mode")
    args = parser.parse_args()

    report = run_evaluation(use_demo=not args.live)
    print(json.dumps(report, indent=2))
    print(f"\nRecall: {report['recall']*100:.0f}% ({report['checks_passed']}/{report['checks_total']} checks)")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
