"""Tests for trust evaluation harness."""

import json
from pathlib import Path

from backend.trust_evaluation import evaluate_trust_sample, run_trust_evaluation


def test_trust_eval_sample_passes_in_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    samples = json.loads(
        (Path(__file__).resolve().parent.parent / "eval" / "trust_samples.json").read_text()
    )
    result = evaluate_trust_sample(samples[0], use_demo=True)
    assert result.passed
    assert result.checks_passed == result.checks_total
    assert result.pipeline == "demo"


def test_run_trust_evaluation_all_pass(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    report = run_trust_evaluation(use_demo=True)
    assert report["all_passed"]
    assert report["checks_total"] >= 4
