#!/usr/bin/env python3
"""SessionStart hook — surfaces pending learnings for review at session start.
Cross-platform equivalent of load-learnings.sh.

Works on macOS, Linux, and Windows (Python 3.8+).
"""

import os
import sys


def main():
    learnings_file = os.path.join(
        os.path.expanduser("~"), ".claude", "docs", "pending-learnings.md"
    )

    if not os.path.isfile(learnings_file):
        sys.exit(0)

    try:
        with open(learnings_file, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        sys.exit(0)

    if not content.strip():
        sys.exit(0)

    print("=== PENDING LEARNINGS FOR REVIEW ===")
    print(content)
    print()
    print("=== END PENDING LEARNINGS ===")
    print(
        "Review the above learnings. Consider incorporating relevant items into memory "
        "(MEMORY.md) if they are durable and non-obvious. Remove items from "
        "pending-learnings.md once processed."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
