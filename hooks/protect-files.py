#!/usr/bin/env python3
"""PreToolUse: Edit|Write hook — blocks edits to sensitive files.
Cross-platform Python equivalent of protect-files.sh.

Exit 0 = allow, Exit 2 = block with feedback to Claude.
Works on macOS, Linux, and Windows (Python 3.8+).
"""

import json
import sys

PROTECTED_PATTERNS = [
    ".env",
    "package-lock.json",
    "yarn.lock",
    ".git/",
    ".gitignore",
    "secrets",
    "credentials",
    ".key",
    ".pem",
    ".cert",
    "id_rsa",
    "id_ed25519",
]


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    file_path = ""
    tool_input = data.get("tool_input") or {}
    if isinstance(tool_input, dict):
        file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    for pattern in PROTECTED_PATTERNS:
        if pattern in file_path:
            print(
                f"Blocked: cannot edit '{file_path}' (matches protected pattern '{pattern}'). "
                "Ask the user for explicit permission to modify this file.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
