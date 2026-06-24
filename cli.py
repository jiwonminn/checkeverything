#!/usr/bin/env python3
"""CLI for checkeverything multi-agent code review."""

import argparse
import json
import sys
from pathlib import Path

from backend.orchestrator import review_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="checkeverything — multi-agent code review (GDG York University)"
    )
    parser.add_argument("file", nargs="?", help="Path to code file to review")
    parser.add_argument(
        "--language", "-l", default="python", help="Language hint (default: python)"
    )
    parser.add_argument(
        "--context", "-c", default="", help="Optional PR or submission context"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output full JSON report instead of Markdown"
    )
    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        return 1

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    code = path.read_text(encoding="utf-8")
    language = args.language or path.suffix.lstrip(".") or "python"

    print("Running checkeverything review (5 sub-agents + coordinator)...", file=sys.stderr)
    result = review_code(code=code, language=language, context=args.context)
    report = result.report

    if args.json:
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print(report.markdown_report)
        print(f"\n---\nPipeline: {result.pipeline} | Model: {result.model} | {result.duration_ms}ms", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
