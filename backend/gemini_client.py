"""Shared Gemini / Vertex AI client configuration."""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
MODEL_FALLBACK_CHAIN = [
    m.strip()
    for m in os.getenv(
        "GEMINI_MODEL_FALLBACKS",
        "gemini-2.5-flash-lite,gemini-2.0-flash-lite,gemini-2.0-flash",
    ).split(",")
    if m.strip()
]


def use_vertex_ai() -> bool:
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes")


def get_client() -> genai.Client:
    if use_vertex_ai():
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        if not project:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT is required when GOOGLE_GENAI_USE_VERTEXAI=true. "
                "Run: gcloud auth application-default login"
            )
        return genai.Client(vertexai=True, project=project, location=location)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey "
            "or set GOOGLE_GENAI_USE_VERTEXAI=true for Vertex AI."
        )
    return genai.Client(api_key=api_key)


def get_model() -> str:
    return DEFAULT_MODEL


def get_model_chain() -> list[str]:
    chain: list[str] = []
    for model in [DEFAULT_MODEL, *MODEL_FALLBACK_CHAIN]:
        if model not in chain:
            chain.append(model)
    return chain


def generate_with_fallback(client: genai.Client, **kwargs):
    """Try models in order; retry on 429 with backoff."""
    last_error: Exception | None = None
    models = get_model_chain()

    for model in models:
        for attempt in range(3):
            try:
                return client.models.generate_content(model=model, **kwargs)
            except genai_errors.ClientError as exc:
                last_error = exc
                message = str(exc)
                if "429" in message or "RESOURCE_EXHAUSTED" in message:
                    wait = min(2 ** attempt * 5, 45)
                    time.sleep(wait)
                    continue
                if "404" in message or "NOT_FOUND" in message:
                    break
                raise

    if last_error:
        raise last_error
    raise RuntimeError("No models available for generate_content")
