#!/bin/bash
# Surfaces pending learnings for review at session start.

LEARNINGS_FILE="$HOME/.claude/docs/pending-learnings.md"

if [ ! -f "$LEARNINGS_FILE" ]; then
  exit 0
fi

# Check if file has content (not just whitespace)
if [ ! -s "$LEARNINGS_FILE" ]; then
  exit 0
fi

echo "=== PENDING LEARNINGS FOR REVIEW ==="
cat "$LEARNINGS_FILE"
echo ""
echo "=== END PENDING LEARNINGS ==="
echo "Review the above learnings. Consider incorporating relevant items into memory (MEMORY.md) if they are durable and non-obvious. Remove items from pending-learnings.md once processed."

exit 0
