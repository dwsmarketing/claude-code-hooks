#!/bin/bash
# Blocks Edit/Write to sensitive files. Used as a PreToolUse hook.
# Exit 0 = allow, Exit 2 = block with feedback to Claude.

INPUT=$(cat)

# Detect Python command
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
else
  # No Python available -- allow through rather than block everything
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | $PYTHON_CMD -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

PROTECTED_PATTERNS=(
  ".env"
  "package-lock.json"
  "yarn.lock"
  ".git/"
  ".gitignore"
  "secrets"
  "credentials"
  ".key"
  ".pem"
  ".cert"
  "id_rsa"
  "id_ed25519"
)

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Blocked: cannot edit '$FILE_PATH' (matches protected pattern '$pattern'). Ask the user for explicit permission to modify this file." >&2
    exit 2
  fi
done

exit 0
