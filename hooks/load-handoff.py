#!/usr/bin/env python3
"""SessionStart hook — loads the most recent handoff file into Claude's context
after compaction or resume. Cross-platform equivalent of load-handoff.sh.

Works on macOS, Linux, and Windows (Python 3.8+).
"""

import os
import sys
import glob


def main():
    handoff_dir = os.path.join(os.path.expanduser("~"), ".claude", "handoffs")

    if not os.path.isdir(handoff_dir):
        print("Context was compacted. Re-read CLAUDE.md and MEMORY.md before continuing.")
        sys.exit(0)

    pattern = os.path.join(handoff_dir, "handoff-*.md")
    files = sorted(glob.glob(pattern), reverse=True)

    if not files:
        print("Context was compacted. No handoff file found. Re-read CLAUDE.md and MEMORY.md before continuing.")
        sys.exit(0)

    latest = files[0]
    try:
        with open(latest, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        print("Context was compacted. Could not read handoff file. Re-read CLAUDE.md and MEMORY.md before continuing.")
        sys.exit(0)

    print(f"=== SESSION HANDOFF (loaded from {latest}) ===")
    print(content)
    print()
    print("=== END HANDOFF ===")
    print("Re-read CLAUDE.md and check MEMORY.md for accumulated context.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
