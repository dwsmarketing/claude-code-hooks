#!/usr/bin/env python3
"""JSONL event logger for Claude Code hooks. Appends one line per event."""

import sys
import json
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs")
LOG_FILE = os.path.join(LOG_DIR, "hook-events.jsonl")

def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {"_raw": raw.strip() if raw else ""}

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": data.get("hook_event_name", "unknown"),
        "session_id": data.get("session_id", ""),
        "data": data,
    }

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")

if __name__ == "__main__":
    main()
