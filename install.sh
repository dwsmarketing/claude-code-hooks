#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo "=== Claude Code Hooks Installer ==="
echo ""

# --- Detect Python ---
PYTHON_CMD=""
if command -v python3 &>/dev/null && python3 --version &>/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python &>/dev/null && python --version &>/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "ERROR: Python 3 is required but not found."
  echo "Install Python 3 and ensure 'python3' or 'python' is on your PATH."
  exit 1
fi

echo "Python: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"

# --- Detect notification command ---
NOTIFY_CMD=""
if [[ "$OSTYPE" == "darwin"* ]]; then
  NOTIFY_CMD="osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  NOTIFY_CMD='powershell.exe -Command "[void][System.Reflection.Assembly]::LoadWithPartialName('"'"'System.Windows.Forms'"'"'); $n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; $n.Visible = $true; $n.ShowBalloonTip(5000, '"'"'Claude Code'"'"', '"'"'Claude needs your attention'"'"', '"'"'Info'"'"')"'
elif command -v notify-send &>/dev/null; then
  NOTIFY_CMD="notify-send 'Claude Code' 'Claude Code needs your attention'"
else
  NOTIFY_CMD="echo 'Claude Code needs your attention'"
fi

echo "Platform: $OSTYPE"
echo ""

# --- Create directories ---
echo "Creating directories..."
mkdir -p "$HOOKS_DIR"
mkdir -p "$CLAUDE_DIR/logs"
mkdir -p "$CLAUDE_DIR/handoffs"
mkdir -p "$CLAUDE_DIR/docs/sessions"
echo "  $HOOKS_DIR"
echo "  $CLAUDE_DIR/logs"
echo "  $CLAUDE_DIR/handoffs"
echo "  $CLAUDE_DIR/docs/sessions"

# --- Copy hook scripts ---
echo ""
echo "Copying hook scripts..."
cp "$SCRIPT_DIR/hooks/"* "$HOOKS_DIR/"
chmod +x "$HOOKS_DIR/"*.sh "$HOOKS_DIR/"*.py 2>/dev/null || true
echo "  Copied $(ls -1 "$SCRIPT_DIR/hooks/" | wc -l | tr -d ' ') scripts to $HOOKS_DIR"

# --- Generate resolved settings ---
echo ""
echo "Generating hooks configuration..."

# Read the template and replace placeholders
HOOKS_JSON=$(cat "$SCRIPT_DIR/settings-hooks.json")
HOOKS_JSON="${HOOKS_JSON//__PYTHON__/$PYTHON_CMD}"
HOOKS_JSON="${HOOKS_JSON//__NOTIFY_COMMAND__/$NOTIFY_CMD}"

# --- Merge into settings.json ---
if [ -f "$SETTINGS_FILE" ]; then
  echo "Merging hooks into existing $SETTINGS_FILE..."

  # Use Python to merge the hooks key into existing settings
  $PYTHON_CMD -c "
import json, sys

with open('$SETTINGS_FILE', 'r') as f:
    settings = json.load(f)

new_hooks = json.loads('''$HOOKS_JSON''')

settings['hooks'] = new_hooks['hooks']

with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)

print('  Merged hooks into existing settings.')
"
else
  echo "Creating new $SETTINGS_FILE..."
  echo "$HOOKS_JSON" | $PYTHON_CMD -c "
import json, sys
data = json.load(sys.stdin)
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print('  Created new settings file.')
"
fi

# --- Validate ---
echo ""
echo "Validating..."
$PYTHON_CMD -c "
import json
with open('$SETTINGS_FILE') as f:
    d = json.load(f)
h = d.get('hooks', {})
print(f'  Valid JSON. {len(h)} event types configured:')
for k, v in h.items():
    print(f'    {k}: {len(v)} entry/entries')
"

echo ""
echo "=== Installation complete ==="
echo ""
echo "Hooks will take effect on your next Claude Code session."
echo ""
echo "Installed hooks:"
echo "  - Notification:      Desktop alerts when Claude needs attention"
echo "  - PreToolUse:        Blocks edits to sensitive files (.env, credentials, etc.)"
echo "  - PostToolUse:       Event logging"
echo "  - Stop:              Event logging"
echo "  - SessionStart:      Loads handoff context + pending learnings"
echo "  - SubagentStart/Stop: Event logging"
echo "  - UserPromptSubmit:  Agent team suggestions for complex tasks"
echo "  - PreCompact:        Saves handoff, session summary, and learnings before compaction"
echo "  - PermissionRequest: Auto-approves ExitPlanMode + event logging"
echo "  - ConfigChange:      Event logging"
echo ""
echo "Log file: $CLAUDE_DIR/logs/hook-events.jsonl"
echo "Handoffs: $CLAUDE_DIR/handoffs/"
echo "Sessions: $CLAUDE_DIR/docs/sessions/"
