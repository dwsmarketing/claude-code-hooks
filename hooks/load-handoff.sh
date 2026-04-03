#!/bin/bash
# Loads the most recent handoff file into Claude's context after compaction/resume.

HANDOFF_DIR="$HOME/.claude/handoffs"

if [ ! -d "$HANDOFF_DIR" ]; then
  echo "Context was compacted. Re-read CLAUDE.md and MEMORY.md before continuing."
  exit 0
fi

# Find the most recent handoff file (sorted by name, which includes timestamp)
LATEST=$(ls -1 "$HANDOFF_DIR"/handoff-*.md 2>/dev/null | sort -r | head -1)

if [ -z "$LATEST" ]; then
  echo "Context was compacted. No handoff file found. Re-read CLAUDE.md and MEMORY.md before continuing."
  exit 0
fi

echo "=== SESSION HANDOFF (loaded from $LATEST) ==="
cat "$LATEST"
echo ""
echo "=== END HANDOFF ==="
echo "Re-read CLAUDE.md and check MEMORY.md for accumulated context."

exit 0
