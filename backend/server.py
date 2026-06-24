"""FastAPI server for checkeverything code review."""

import asyncio
import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from backend.analyze import analyze_response
from backend.diff_parser import infer_language_from_diff, parse_unified_diff
from backend.gemini_client import get_model, use_vertex_ai
from backend.orchestrator import review_code, review_code_stream
from backend.trust_models import AnalyzeRequest

STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="checkeverything",
    description="Multi-agent code review — Google ADK + Gemini + 5 specialist agents",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    code: str = Field(default="", description="Raw code submission")
    diff: str = Field(default="", description="Unified diff (PR patch)")
    submission_type: Literal["code", "diff"] = Field(default="code")
    language: str = Field(default="python")
    context: str = Field(default="")

    @model_validator(mode="after")
    def validate_input(self):
        if self.submission_type == "code" and not self.code.strip():
            raise ValueError("code is required when submission_type is 'code'")
        if self.submission_type == "diff" and not self.diff.strip():
            raise ValueError("diff is required when submission_type is 'diff'")
        return self

    def resolve(self) -> tuple[str, str, str]:
        if self.submission_type == "diff":
            summary = parse_unified_diff(self.diff)
            lang = self.language if self.language != "python" else infer_language_from_diff(summary.files)
            ctx = f"{self.context}\n{summary.context_note}".strip()
            return summary.extracted_code, lang, ctx
        return self.code, self.language, self.context


class ParseDiffRequest(BaseModel):
    diff: str = Field(min_length=1)


@app.get("/")
async def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


@app.get("/health")
async def health():
    import os

    return {
        "status": "ok",
        "service": "checkeverything",
        "version": "2.0.0",
        "agents": 5,
        "google_technologies": {
            "gemini_api": not use_vertex_ai(),
            "vertex_ai": use_vertex_ai(),
            "google_adk": os.getenv("USE_ADK", "true").lower() in ("1", "true", "yes"),
        },
        "model": get_model(),
        "demo_mode": os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes"),
    }


@app.post("/api/parse-diff")
async def parse_diff(request: ParseDiffRequest):
    try:
        summary = parse_unified_diff(request.diff)
        return {
            "files": summary.files,
            "added_lines": summary.added_lines,
            "removed_lines": summary.removed_lines,
            "extracted_code": summary.extracted_code,
            "context_note": summary.context_note,
            "language": infer_language_from_diff(summary.files),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _run_review(request: ReviewRequest):
    code, language, context = request.resolve()
    return review_code(code=code, language=language, context=context)


def _stream_review(request: ReviewRequest):
    code, language, context = request.resolve()
    return review_code_stream(code=code, language=language, context=context)


@app.post("/api/review")
async def create_review(request: ReviewRequest):
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: _run_review(request))
        return response.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Review failed: {exc}") from exc


@app.post("/api/analyze")
async def analyze_ai_response(request: AnalyzeRequest):
    """Analyze an AI response for trust and credibility (planned)."""
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: analyze_response(request))
        return response.model_dump()
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


@app.post("/api/review/stream")
async def create_review_stream(request: ReviewRequest):
    def event_generator():
        try:
            for event in _stream_review(request):
                yield f"data: {json.dumps(event)}\n\n"
        except ValueError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Review failed: {exc}'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
