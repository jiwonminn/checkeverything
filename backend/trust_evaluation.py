"""Evaluation harness for trust analysis — claim support label recall on labeled samples."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from backend.analyze import analyze_response
from backend.trust_models import AnalyzeRequest

EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"
TRUST_SAMPLES_FILE = EVAL_DIR / "trust_samples.json"


@dataclass
class TrustSampleResult:
    sample_id: str
    passed: bool
    checks_passed: int
    checks_total: int
    pipeline: str
    details: list[str]


def _find_claim_by_fragment(claims, fragment: str):
    fragment_lower = fragment.lower()
    for claim in claims:
        if fragment_lower in claim.text.lower():
            return claim
    return None


def evaluate_trust_sample(sample: dict, use_demo: bool = True) -> TrustSampleResult:
    if use_demo:
        os.environ["DEMO_MODE"] = "true"

    text = Path(sample["file"]).read_text(encoding="utf-8")
    response = analyze_response(
        AnalyzeRequest(
            text=text,
            urls=sample.get("urls", []),
            source=sample.get("source", "chatgpt"),
        )
    )

    details: list[str] = []
    passed_checks = 0
    expected_claims = sample.get("expected_claims", [])
    total = len(expected_claims)

    for check in expected_claims:
        fragment = check["text_contains"]
        expected_label = check["support_label"]
        claim = _find_claim_by_fragment(response.claims, fragment)
        if not claim:
            details.append(f"FAIL claim '{fragment}': not found in response")
            continue
        if claim.support_label == expected_label:
            passed_checks += 1
            details.append(f"PASS claim '{fragment}': {expected_label}")
        else:
            details.append(
                f"FAIL claim '{fragment}': expected {expected_label}, got {claim.support_label}"
            )

    for category, minimum in sample.get("expected_categories_min", {}).items():
        total += 1
        score = response.categories.get(category)
        if score and score.score >= minimum:
            passed_checks += 1
            details.append(f"PASS {category}: {score.score} >= {minimum}")
        else:
            actual = score.score if score else "missing"
            details.append(f"FAIL {category}: expected >= {minimum}, got {actual}")

    return TrustSampleResult(
        sample_id=sample["id"],
        passed=passed_checks == total and total > 0,
        checks_passed=passed_checks,
        checks_total=total,
        pipeline=response.pipeline,
        details=details,
    )


def run_trust_evaluation(use_demo: bool = True) -> dict:
    samples = json.loads(TRUST_SAMPLES_FILE.read_text(encoding="utf-8"))
    results = [evaluate_trust_sample(sample, use_demo=use_demo) for sample in samples]

    total_checks = sum(result.checks_total for result in results)
    passed_checks = sum(result.checks_passed for result in results)

    return {
        "samples": len(results),
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "recall": round(passed_checks / total_checks, 2) if total_checks else 0,
        "all_passed": all(result.passed for result in results),
        "results": [
            {
                "id": result.sample_id,
                "passed": result.passed,
                "score": f"{result.checks_passed}/{result.checks_total}",
                "pipeline": result.pipeline,
                "details": result.details,
            }
            for result in results
        ],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="CheckEverything trust evaluation harness")
    parser.add_argument("--live", action="store_true", help="Use live API instead of demo mode")
    args = parser.parse_args()

    report = run_trust_evaluation(use_demo=not args.live)
    print(json.dumps(report, indent=2))
    print(
        f"\nTrust recall: {report['recall'] * 100:.0f}% "
        f"({report['checks_passed']}/{report['checks_total']} checks)"
    )
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
