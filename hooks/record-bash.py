#!/usr/bin/env python3
"""PostToolUse: Bash hook — records executed commands to pending-insights.jsonl
so intelligence.cjs consolidate() can surface frequently-run commands in the graph."""

import json
import os
import sys
import time

DATA_DIR = os.path.join(os.getcwd(), ".claude-flow", "data")
PENDING_PATH = os.path.join(DATA_DIR, "pending-insights.jsonl")


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

    # Normalize: strip leading/trailing whitespace, collapse internal newlines
    cmd = " ".join(cmd.split())

    # Truncate very long commands to keep the graph readable
    if len(cmd) > 120:
        cmd = cmd[:120] + "…"

    os.makedirs(DATA_DIR, exist_ok=True)

    entry = json.dumps({
        "type": "command",
        "file": cmd,
        "timestamp": int(time.time() * 1000),
        "sessionId": os.environ.get("CLAUDE_SESSION_ID"),
        "cwd": data.get("cwd") or os.getcwd(),
    })

    with open(PENDING_PATH, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # Hooks must never crash Claude Code
    sys.exit(0)
