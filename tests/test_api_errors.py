"""Tests for shared API error fallback detection."""

from backend.api_errors import is_recoverable_api_error


def test_credentials_error_is_recoverable():
    exc = Exception(
        "Your default credentials were not found. To set up Application Default Credentials..."
    )
    assert is_recoverable_api_error(exc)


def test_not_found_message_is_recoverable():
    assert is_recoverable_api_error(Exception("404 Not Found"))


def test_random_error_is_not_recoverable():
    assert not is_recoverable_api_error(ValueError("invalid input"))
