#!/usr/bin/env python3
"""PostToolUse: Bash hook — records executed commands to pending-insights.jsonl
so intelligence.cjs consolidate() can surface frequently-run commands in the graph.

Works on macOS, Linux, and Windows (Python 3.8+).
"""

import json
import os
import sys
import time


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Extract command text from PostToolUse payload
    cmd = ""
    tool_input = data.get("tool_input") or data.get("toolInput") or {}
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command", "")
    if not cmd:
        cmd = data.get("command", "")

    # Skip empty or trivially short commands
    cmd = cmd.strip()
    if len(cmd) < 3:
        sys.exit(0)

    # Normalize: collapse internal newlines/extra whitespace
    cmd = " ".join(cmd.split())

    # Truncate very long commands to keep the graph readable
    if len(cmd) > 120:
        cmd = cmd[:120] + "\u2026"

    # Write to project-local pending-insights.jsonl (same file recordEdit uses)
    data_dir = os.path.join(os.getcwd(), ".claude-flow", "data")
    pending_path = os.path.join(data_dir, "pending-insights.jsonl")

    os.makedirs(data_dir, exist_ok=True)

    entry = json.dumps({
        "type": "command",
        "file": cmd,
        "timestamp": int(time.time() * 1000),
        "sessionId": os.environ.get("CLAUDE_SESSION_ID"),
        "cwd": data.get("cwd") or os.getcwd(),
    })

    with open(pending_path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # Hooks must never crash Claude Code
    sys.exit(0)
