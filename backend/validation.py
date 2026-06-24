"""Input validation for code submissions."""

from backend.prompts import MAX_CODE_CHARS


def validate_submission(code: str, language: str) -> None:
    if not code or not code.strip():
        raise ValueError("Code submission cannot be empty.")
    if len(code) > MAX_CODE_CHARS:
        raise ValueError(
            f"Code too large ({len(code):,} chars). Maximum is {MAX_CODE_CHARS:,} characters. "
            "Submit a single file or function instead of an entire repository."
        )
    if not language or not language.strip():
        raise ValueError("Language is required.")


def format_review_input(code: str, language: str, context: str) -> str:
    return f"""Review this {language} code submission.

Additional context from submitter:
{context or "None provided."}

```
{code}
```
"""
