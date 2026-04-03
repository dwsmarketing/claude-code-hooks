#!/usr/bin/env python3
"""SessionStart hook — prunes stale handoff and session files.

Runs at the start of every session. Deletes files older than RETENTION_DAYS
from the handoff and session summary directories to prevent unbounded growth.

Thresholds (configurable via env vars):
  CLAUDE_HANDOFF_RETENTION_DAYS   default 7   — handoff-*.md files
  CLAUDE_SESSION_RETENTION_DAYS   default 30  — docs/sessions/*.md files
  CLAUDE_INSIGHTS_RETENTION_DAYS  default 14  — pending-insights.jsonl lines (by age)

Prints a one-line summary only if files were deleted.

Works on macOS, Linux, and Windows (Python 3.8+).

# =============================================================================
# DASHBOARD GROUNDWORK NOTE
# =============================================================================
# Cleanup events are useful for dashboard health monitoring:
#
#   PANEL: "Storage Health" — show disk usage of ~/.claude dirs over time
#   ALERT: "Disk Warning" — trigger if ~/.claude/logs/ exceeds 100MB
#
# To feed a dashboard, cleanup actions could be logged to:
#   ~/.claude/logs/maintenance.jsonl
# Schema:
# {
#   "timestamp": "ISO-8601",
#   "type": "cleanup",
#   "handoffs_deleted": 2,
#   "sessions_deleted": 5,
#   "bytes_freed": 40960
# }
# =============================================================================
"""

import glob
import os
import sys
import time
import json
from datetime import datetime, timezone

CLAUDE_DIR = os.path.expanduser("~/.claude")
HANDOFF_DIR = os.path.join(CLAUDE_DIR, "handoffs")
SESSIONS_DIR = os.path.join(CLAUDE_DIR, "docs", "sessions")
LOG_DIR = os.path.join(CLAUDE_DIR, "logs")
MAINTENANCE_LOG = os.path.join(LOG_DIR, "maintenance.jsonl")

HANDOFF_DAYS = int(os.environ.get("CLAUDE_HANDOFF_RETENTION_DAYS", "7"))
SESSION_DAYS = int(os.environ.get("CLAUDE_SESSION_RETENTION_DAYS", "30"))

NOW = time.time()


def age_days(path):
    try:
        return (NOW - os.path.getmtime(path)) / 86400
    except OSError:
        return 0


def prune_dir(directory, pattern, max_age_days):
    """Delete files matching pattern older than max_age_days. Returns (count, bytes)."""
    if not os.path.isdir(directory):
        return 0, 0
    deleted_count = 0
    deleted_bytes = 0
    for path in glob.glob(os.path.join(directory, pattern)):
        if age_days(path) > max_age_days:
            try:
                deleted_bytes += os.path.getsize(path)
                os.remove(path)
                deleted_count += 1
            except OSError:
                pass
    return deleted_count, deleted_bytes


def main():
    h_deleted, h_bytes = prune_dir(HANDOFF_DIR, "handoff-*.md", HANDOFF_DAYS)
    s_deleted, s_bytes = prune_dir(SESSIONS_DIR, "*.md", SESSION_DAYS)

    total_deleted = h_deleted + s_deleted
    total_bytes = h_bytes + s_bytes

    if total_deleted:
        kb = total_bytes / 1024
        print(
            f"[Cleanup] Pruned {total_deleted} file(s) "
            f"({h_deleted} handoffs >{HANDOFF_DAYS}d, "
            f"{s_deleted} session summaries >{SESSION_DAYS}d) "
            f"— freed {kb:.0f}KB"
        )

    # Write maintenance log entry (for future dashboard)
    if total_deleted:
        os.makedirs(LOG_DIR, exist_ok=True)
        entry = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "cleanup",
            "handoffs_deleted": h_deleted,
            "sessions_deleted": s_deleted,
            "bytes_freed": total_bytes,
        }, separators=(",", ":"))
        try:
            with open(MAINTENANCE_LOG, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except OSError:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
