"""Parse unified diffs for PR-style code review."""

import re
from dataclasses import dataclass


@dataclass
class DiffSummary:
    files: list[str]
    added_lines: int
    removed_lines: int
    extracted_code: str
    context_note: str


def parse_unified_diff(diff_text: str) -> DiffSummary:
    """Extract changed/added lines from a unified diff for agent review."""
    if not diff_text or not diff_text.strip():
        raise ValueError("Diff is empty.")

    files: list[str] = []
    extracted: list[str] = []
    added = 0
    removed = 0
    current_file = "unknown"

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            match = re.search(r"b/(.+)$", line)
            if match:
                current_file = match.group(1)
                if current_file not in files:
                    files.append(current_file)
            extracted.append(f"\n# --- {current_file} ---")
            continue
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            if current_file not in files:
                files.append(current_file)
            continue
        if line.startswith("@@"):
            extracted.append(f"# {line}")
            continue
        if line.startswith("+") and not line.startswith("+++"):
            extracted.append(line[1:])
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            extracted.append(f"# removed: {line[1:]}")
            removed += 1
        elif line.startswith(" "):
            extracted.append(line[1:])

    code = "\n".join(extracted).strip()
    if not code:
        raise ValueError("No reviewable changes found in diff.")

    file_list = ", ".join(files[:5])
    if len(files) > 5:
        file_list += f" (+{len(files) - 5} more)"

    return DiffSummary(
        files=files,
        added_lines=added,
        removed_lines=removed,
        extracted_code=code,
        context_note=(
            f"PR diff review — {len(files)} file(s): {file_list}. "
            f"+{added}/-{removed} lines."
        ),
    )


def infer_language_from_diff(files: list[str], fallback: str = "python") -> str:
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".cpp": "cpp",
        ".c": "c",
    }
    for f in files:
        for ext, lang in ext_map.items():
            if f.endswith(ext):
                return lang
    return fallback
