"""HTTP API smoke tests (demo mode — no live Gemini required)."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("USE_ADK", "false")

from backend.server import app  # noqa: E402

client = TestClient(app)

SAMPLE_CODE = "def add(a, b):\n    return a + b\n"
SAMPLE_AI = (
    "Vitamin D supplements may reduce respiratory infections, according to observational studies. "
    "Daily doses of 600–800 IU are generally considered safe for most adults."
)


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("USE_ADK", "false")


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


def test_analyze_ai_answer():
    response = client.post(
        "/api/analyze",
        json={
            "text": SAMPLE_AI,
            "urls": ["https://www.who.int", "https://www.ncbi.nlm.nih.gov"],
            "source": "other",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert 0 <= body["overall_score"] <= 100
    assert body["categories"]
    assert body["claims"]


def test_review_stream_completes():
    with client.stream(
        "POST",
        "/api/review/stream",
        json={
            "code": SAMPLE_CODE,
            "submission_type": "code",
            "language": "python",
            "context": "API test",
            "weights": {
                "security": 20,
                "correctness": 25,
                "readability": 15,
                "performance": 15,
                "test_coverage": 25,
            },
        },
    ) as response:
        assert response.status_code == 200
        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                import json

                events.append(json.loads(line[6:]))
    types = [event["type"] for event in events]
    assert "complete" in types
    assert "error" not in types
    complete = next(event for event in events if event["type"] == "complete")
    report = complete["data"]["report"]
    assert report["overall_score"] >= 0
    assert len(report["agent_reports"]) == 5
    assert complete["data"]["score_weights"]["security"] == 20
