#!/usr/bin/env python3
"""Stop hook — prints a session activity summary and rotates the event log.

Runs at the end of each Claude Code turn (Stop event).
  1. Reads hook-events.jsonl for the current session_id
  2. Counts edits, bash commands, failures, subagent events
  3. Prints a one-line session summary
  4. Rotates hook-events.jsonl if it exceeds MAX_LOG_SIZE_MB

Works on macOS, Linux, and Windows (Python 3.8+).

# =============================================================================
# DASHBOARD GROUNDWORK NOTE
# =============================================================================
# This script is the natural data provider for a session activity dashboard.
# The stats it computes per-session could power:
#
#   PANEL: "Session Activity" — bar chart of tool types used this turn
#   PANEL: "Session History" — cumulative edits/commands/failures per session
#   PANEL: "Health Indicator" — failure rate, failure types over last N sessions
#
# To feed a dashboard, consider writing stats to a structured store:
#   ~/.claude/logs/session-summaries.jsonl
# Schema per entry:
# {
#   "timestamp": "ISO-8601",        # when the session ended
#   "session_id": "...",
#   "duration_turns": 1,            # Stop events = turns completed
#   "edits": 12,
#   "bash_commands": 8,
#   "tool_failures": 0,
#   "subagents_spawned": 2,
#   "files_modified": ["foo.py"],   # extracted from PostToolUse payloads
#   "log_rotated": false
# }
#
# The Val Town dashboard endpoint (see ~/.claude/docs/dashboard-vision.md)
# can ingest these entries via POST for real-time display.
# =============================================================================
"""

import json
import os
import sys
import shutil
from datetime import datetime, timezone
from collections import Counter

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs")
LOG_FILE = os.path.join(LOG_DIR, "hook-events.jsonl")
SUMMARIES_FILE = os.path.join(LOG_DIR, "session-summaries.jsonl")
MAX_LOG_SIZE_MB = 5


def main():
    # Parse stdin to get current session_id
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    session_id = data.get("session_id", "")

    if not os.path.exists(LOG_FILE):
        sys.exit(0)

    # --- Count events for this session ---
    event_counts = Counter()
    files_modified = set()
    commands_run = []

    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Filter to current session if we have one
                if session_id and entry.get("session_id") != session_id:
                    continue

                event = entry.get("event", "unknown")
                event_counts[event] += 1

                # Extract file paths from PostToolUse edits
                inner = entry.get("data", {})
                tool_input = inner.get("tool_input") or {}
                if isinstance(tool_input, dict):
                    fp = tool_input.get("file_path")
                    if fp:
                        files_modified.add(os.path.basename(fp))
                    cmd = tool_input.get("command", "")
                    if cmd:
                        commands_run.append(cmd[:60])
    except Exception:
        pass

    edits = event_counts.get("PostToolUse", 0)
    failures = event_counts.get("PostToolUseFailure", 0)
    subagents = event_counts.get("SubagentStop", 0)
    bash_count = len(commands_run)

    # --- Print summary ---
    parts = []
    if edits:
        parts.append(f"{edits} tool uses")
    if bash_count:
        parts.append(f"{bash_count} commands")
    if subagents:
        parts.append(f"{subagents} subagents")
    if failures:
        parts.append(f"[!] {failures} failures")
    if files_modified:
        sample = ", ".join(sorted(files_modified)[:4])
        extra = f" +{len(files_modified)-4} more" if len(files_modified) > 4 else ""
        parts.append(f"files: {sample}{extra}")

    if parts:
        print(f"[Session] {' · '.join(parts)}")

    # --- Write to session-summaries.jsonl (dashboard feed) ---
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "tool_uses": edits,
        "bash_commands": bash_count,
        "tool_failures": failures,
        "subagents_spawned": subagents,
        "files_modified": sorted(files_modified),
        "log_rotated": False,
    }

    # --- Rotate log if oversized ---
    try:
        size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
        if size_mb >= MAX_LOG_SIZE_MB:
            rotated = LOG_FILE + ".1"
            shutil.move(LOG_FILE, rotated)
            # Keep only last 2000 lines of the rotated file to prevent runaway growth
            with open(rotated, encoding="utf-8") as f:
                lines = f.readlines()
            with open(rotated, "w", encoding="utf-8") as f:
                f.writelines(lines[-2000:])
            summary["log_rotated"] = True
            print(f"[Session] Log rotated ({size_mb:.1f}MB → {rotated})")
    except Exception:
        pass

    # Write summary entry
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(SUMMARIES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
