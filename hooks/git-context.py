#!/usr/bin/env python3
"""SessionStart hook — injects current git context into Claude's awareness.

Runs on every session start. Outputs branch, recent commits, and a summary
of dirty working tree files so Claude starts each session git-aware.

Works on macOS, Linux, and Windows (Python 3.8+).
Exits silently (no output) if the working directory is not a git repo.

# =============================================================================
# DASHBOARD GROUNDWORK NOTE
# =============================================================================
# This script outputs git state to Claude's context. For future dashboard
# integration, this same data could be:
#   - Written to ~/.claude/logs/git-context.jsonl (one entry per session)
#   - Used to populate a "repo activity" panel in the dashboard
#   - Tracked over time to show which branches/repos Claude works in most
#
# Suggested future schema for git-context.jsonl:
# {
#   "timestamp": "ISO-8601",
#   "session_id": "...",
#   "cwd": "/path/to/project",
#   "branch": "main",
#   "repo_name": "my-project",
#   "uncommitted_files": 3,
#   "untracked_files": 1,
#   "recent_commits": ["abc1234 Fix auth bug", "def5678 Add tests"],
#   "has_stash": false
# }
# =============================================================================
"""

import subprocess
import sys
import os
import json


def run(cmd, cwd=None):
    """Run a git command, return stdout or empty string on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd or os.getcwd(),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def main():
    cwd = os.getcwd()

    # Confirm this is a git repo — exit silently if not
    if not run(["git", "rev-parse", "--is-inside-work-tree"], cwd):
        sys.exit(0)

    branch = run(["git", "branch", "--show-current"], cwd) or run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd
    )
    repo_name = os.path.basename(run(["git", "rev-parse", "--show-toplevel"], cwd) or cwd)

    # Uncommitted changes (staged + unstaged + untracked)
    status_lines = [
        l for l in run(["git", "status", "--short"], cwd).splitlines() if l.strip()
    ]
    modified = [l for l in status_lines if not l.startswith("?")]
    untracked = [l for l in status_lines if l.startswith("?")]

    # Last 3 commits
    log = run(["git", "log", "--oneline", "-3"], cwd)
    commits = log.splitlines() if log else []

    # Stash count
    stash = run(["git", "stash", "list"], cwd)
    stash_count = len(stash.splitlines()) if stash else 0

    # Build compact output
    lines = [f"[GIT] {repo_name} · branch: {branch}"]

    if modified:
        lines.append(f"  {len(modified)} uncommitted change(s): " + ", ".join(
            l[3:].split(" -> ")[-1] for l in modified[:5]
        ) + ("…" if len(modified) > 5 else ""))
    if untracked:
        lines.append(f"  {len(untracked)} untracked file(s)")
    if not modified and not untracked:
        lines.append("  Working tree clean")
    if commits:
        lines.append("  Recent: " + " | ".join(commits))
    if stash_count:
        lines.append(f"  Stash: {stash_count} entry/entries")

    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
