#!/usr/bin/env python3
"""PostToolUse: Write|Edit|MultiEdit hook — validates file syntax after writes.

Catches syntax errors immediately after Claude writes/edits a file so they
can be fixed in the same turn rather than discovered later at runtime.

Supported file types:
  .py   — Python syntax check via py_compile (stdlib, zero deps)
  .json — JSON validation via json.loads (stdlib)
  .toml — TOML validation via tomllib/tomli if available (Python 3.11+ built-in)

Other file types pass through silently (exit 0).

Exit 0 = valid or unknown type (allow)
Exit 2 = syntax error (block, feed error back to Claude)

Works on macOS, Linux, and Windows (Python 3.8+).

# =============================================================================
# DASHBOARD GROUNDWORK NOTE
# =============================================================================
# Syntax validation results are a valuable dashboard data point:
#
#   PANEL: "Code Quality" — syntax error rate per session / per file type
#   PANEL: "Error Hotspots" — which files have the most syntax errors
#   PANEL: "Fix Velocity" — how quickly syntax errors are resolved
#
# To feed a dashboard, consider writing to:
#   {project}/.claude-flow/data/syntax-events.jsonl
# Schema:
# {
#   "timestamp": "ISO-8601",
#   "session_id": "...",
#   "file": "foo.py",
#   "ext": ".py",
#   "valid": false,
#   "error": "SyntaxError: invalid syntax (foo.py, line 42)"
# }
# =============================================================================
"""

import json
import os
import sys
import py_compile
import tempfile


def check_python(file_path):
    """Returns (valid: bool, error: str)."""
    try:
        py_compile.compile(file_path, doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, str(e)
    except Exception as e:
        return True, ""  # If we can't check, allow through


def check_json(file_path):
    """Returns (valid: bool, error: str)."""
    try:
        with open(file_path, encoding="utf-8") as f:
            json.load(f)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {e}"
    except Exception:
        return True, ""


def check_toml(file_path):
    """Returns (valid: bool, error: str). Requires Python 3.11+ or tomli."""
    try:
        # Python 3.11+ built-in
        import tomllib
        with open(file_path, "rb") as f:
            tomllib.load(f)
        return True, ""
    except ImportError:
        try:
            import tomli
            with open(file_path, "rb") as f:
                tomli.load(f)
            return True, ""
        except ImportError:
            return True, ""  # Not available — skip silently
    except Exception as e:
        return False, f"TOML syntax error: {e}"


CHECKERS = {
    ".py": check_python,
    ".json": check_json,
    ".toml": check_toml,
}


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Extract file path from PostToolUse payload
    file_path = ""
    tool_input = data.get("tool_input") or {}
    if isinstance(tool_input, dict):
        file_path = tool_input.get("file_path", "")
    if not file_path:
        # MultiEdit has a list of edits — check the first file
        edits = tool_input.get("edits", [])
        if edits and isinstance(edits, list) and isinstance(edits[0], dict):
            file_path = edits[0].get("file_path", "")

    if not file_path or not os.path.isfile(file_path):
        sys.exit(0)

    ext = os.path.splitext(file_path)[1].lower()
    checker = CHECKERS.get(ext)

    if not checker:
        sys.exit(0)  # Unknown type — allow through silently

    valid, error = checker(file_path)

    if valid:
        sys.exit(0)

    print(
        f"Syntax error in {os.path.basename(file_path)}: {error}\n"
        "Fix the syntax error before proceeding.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
