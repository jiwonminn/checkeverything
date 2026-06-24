"""Tests for diff parser."""

import pytest

from backend.diff_parser import infer_language_from_diff, parse_unified_diff


SAMPLE = """diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,3 +1,5 @@
 import sqlite3
+SECRET = "x"
 def login(u, p):
-    pass
+    exec(p)
"""


def test_parse_unified_diff_extracts_additions():
    result = parse_unified_diff(SAMPLE)
    assert "SECRET" in result.extracted_code
    assert "exec" in result.extracted_code
    assert result.added_lines >= 2
    assert "auth.py" in result.files


def test_infer_language_from_diff():
    assert infer_language_from_diff(["src/auth.py"]) == "python"
    assert infer_language_from_diff(["api.js"]) == "javascript"


def test_empty_diff_raises():
    with pytest.raises(ValueError):
        parse_unified_diff("")
