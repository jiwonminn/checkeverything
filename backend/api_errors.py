"""Shared detection for API errors that should fall back to demo/offline mode."""

from google.genai import errors as genai_errors

RECOVERABLE_MARKERS = (
    "404",
    "429",
    "503",
    "NOT_FOUND",
    "NOT FOUND",
    "RESOURCE_EXHAUSTED",
    "UNAVAILABLE",
    "API_KEY_INVALID",
    "DEFAULT CREDENTIALS WERE NOT FOUND",
    "COULD NOT AUTOMATICALLY DETERMINE CREDENTIALS",
    "GEMINI_API_KEY IS NOT SET",
    "GOOGLE_CLOUD_PROJECT",
    "PERMISSION DENIED",
    "UNAUTHENTICATED",
    "ADK PIPELINE FINISHED WITHOUT A COORDINATOR REPORT",
    "ADK TRUST PIPELINE FINISHED WITHOUT",
)


def _message_contains_marker(message: str) -> bool:
    upper = message.upper()
    return any(marker in upper for marker in RECOVERABLE_MARKERS)


def is_recoverable_api_error(exc: Exception) -> bool:
    """Return True when live Gemini/Vertex is unavailable and demo mode is acceptable."""
    if isinstance(exc, genai_errors.APIError):
        return _message_contains_marker(str(exc))

    if isinstance(exc, RuntimeError) and _message_contains_marker(str(exc)):
        return True

    module = type(exc).__module__
    name = type(exc).__name__
    if module.startswith(("httpx", "httpcore")) and name in (
        "ConnectError",
        "ConnectTimeout",
        "ReadTimeout",
        "RemoteProtocolError",
        "NetworkError",
        "TransportError",
    ):
        return True

    if _message_contains_marker(str(exc)):
        return True

    cause = exc.__cause__ or exc.__context__
    if isinstance(cause, Exception) and cause is not exc:
        return is_recoverable_api_error(cause)

    return False
