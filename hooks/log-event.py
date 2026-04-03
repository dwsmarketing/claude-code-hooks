#!/usr/bin/env python3
"""JSONL event logger for Claude Code hooks. Appends one line per event.

Catches all hook events and writes structured entries to hook-events.jsonl.
This file is the primary audit trail for all Claude Code activity and serves
as the main data source for the future Claude Code activity dashboard.

# =============================================================================
# DASHBOARD GROUNDWORK NOTE
# =============================================================================
# hook-events.jsonl is the backbone data source for a real-time Claude Code
# activity dashboard. Every hook event flows through here.
#
# RECOMMENDED DASHBOARD PANELS (all powered by this file):
#
#   PANEL: "Activity Timeline" — scrolling event log with event type, tool,
#          file, and timestamp. Refreshes every 5–10 seconds.
#          Filter: hook_event_name IN (PreToolUse, PostToolUse, Bash, Write, Edit)
#
#   PANEL: "Tool Usage Breakdown" — pie or bar chart of tool_name counts
#          over the last session or last 24 hours.
#          Query: GROUP BY tool_name, COUNT(*)
#
#   PANEL: "Session Overview" — card showing current session_id, start time,
#          total events, and unique files modified.
#          Query: WHERE session_id = <current>, aggregate counts
#
#   PANEL: "Error Rate" — line chart of PostToolUseFailure events over time.
#          Alert if error rate > 10% of total PostToolUse events in 15 minutes.
#
#   PANEL: "Files Modified" — table of files changed in the current session,
#          sorted by modification count. Source: tool_name=Write|Edit entries.
#
#   PANEL: "Command History" — list of Bash commands run, with timestamps.
#          Source: tool_name=Bash entries, command field from tool_input.
#
# INTEGRATION PATH:
#   Option A (simple): Tail hook-events.jsonl from a web server process;
#     serve via Server-Sent Events (SSE) to a browser dashboard.
#   Option B (Val Town): POST each event to a Val Town HTTP endpoint that
#     stores in SQLite and serves a dashboard. See ~/.claude/docs/dashboard-vision.md
#   Option C (local): Use a Python FastAPI server with a React frontend,
#     reading hook-events.jsonl on a polling interval.
#
# EVENT SCHEMA (current):
# {
#   "timestamp": "ISO-8601",        # UTC
#   "event": "PostToolUse",          # hook_event_name
#   "session_id": "...",
#   "tool_name": "Bash",             # from tool_name field
#   "tool_command": "npm test",      # Bash-specific: the command run
#   "tool_file": "src/foo.py",       # Write/Edit-specific: file path
#   "tool_success": true,            # PostToolUse only
#   "data": { ... }                  # full raw payload (remove for prod to save space)
# }
#
# ROTATION:
#   session-stats.py rotates hook-events.jsonl when it exceeds 5MB.
#   The rotated file is saved as hook-events.jsonl.1.
#   For a dashboard, consider reading both files when the primary is empty.
#
# VAL TOWN INTEGRATION STUB:
#   When ready to push events to Val Town for a hosted dashboard, add:
#
#     import urllib.request
#     DASHBOARD_ENDPOINT = os.environ.get("CLAUDE_DASHBOARD_URL", "")
#     if DASHBOARD_ENDPOINT:
#         try:
#             req = urllib.request.Request(
#                 DASHBOARD_ENDPOINT,
#                 data=json.dumps(entry).encode(),
#                 headers={"Content-Type": "application/json"},
#                 method="POST"
#             )
#             urllib.request.urlopen(req, timeout=2)
#         except Exception:
#             pass  # Never block on dashboard failures
#
#   Set CLAUDE_DASHBOARD_URL in settings.json "env" block to activate.
# =============================================================================

Works on macOS, Linux, and Windows (Python 3.8+).
"""

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

    # Extract richer metadata for dashboard use
    tool_input = data.get("tool_input") or {}
    hook_event = data.get("hook_event_name", "unknown")
    tool_name = data.get("tool_name", "")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": hook_event,
        "session_id": data.get("session_id", ""),
        "tool_name": tool_name,
    }

    # Bash: capture the command text
    if tool_name == "Bash" and isinstance(tool_input, dict):
        cmd = tool_input.get("command", "")
        if cmd:
            entry["tool_command"] = cmd[:200]  # cap at 200 chars

    # Write/Edit/MultiEdit: capture the file path
    if tool_name in ("Write", "Edit", "MultiEdit") and isinstance(tool_input, dict):
        file_path = tool_input.get("file_path", "")
        if not file_path:
            edits = tool_input.get("edits", [])
            if edits and isinstance(edits[0], dict):
                file_path = edits[0].get("file_path", "")
        if file_path:
            entry["tool_file"] = file_path

    # PostToolUse: note success/failure
    if hook_event == "PostToolUse":
        entry["tool_success"] = True
    elif hook_event == "PostToolUseFailure":
        entry["tool_success"] = False
        error = data.get("error", "")
        if error:
            entry["error"] = str(error)[:300]

    # Include full payload for debugging (omit in prod to reduce file size)
    entry["data"] = data

    os.makedirs(LOG_DIR, exist_ok=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
