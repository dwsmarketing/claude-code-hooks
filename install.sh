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

# --- Generate and merge hooks configuration ---
# Pass values via environment variables so special characters (quotes, backslashes)
# in $NOTIFY_CMD are handled safely by Python — no bash-level JSON injection risk.
echo ""
echo "Generating hooks configuration..."

export _CLAUDE_INSTALL_PYTHON="$PYTHON_CMD"
export _CLAUDE_INSTALL_NOTIFY="$NOTIFY_CMD"
export _CLAUDE_SCRIPT_DIR="$SCRIPT_DIR"
export _CLAUDE_SETTINGS="$SETTINGS_FILE"

$PYTHON_CMD - << 'INSTALL_PYEOF'
import json, os, shutil, sys

script_dir    = os.environ["_CLAUDE_SCRIPT_DIR"]
settings_file = os.environ["_CLAUDE_SETTINGS"]
python_cmd    = os.environ["_CLAUDE_INSTALL_PYTHON"]
notify_cmd    = os.environ["_CLAUDE_INSTALL_NOTIFY"]

# Walk the JSON object tree and replace __PYTHON__ / __NOTIFY_COMMAND__ using
# Python string methods — this is safe for any value, including those containing
# quotes, backslashes, or other characters that would break bash-level JSON
# string substitution.
def replace_placeholders(obj):
    if isinstance(obj, str):
        return obj.replace("__PYTHON__", python_cmd).replace("__NOTIFY_COMMAND__", notify_cmd)
    if isinstance(obj, dict):
        return {k: replace_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_placeholders(v) for v in obj]
    return obj

template_path = os.path.join(script_dir, "settings-hooks.json")
with open(template_path, encoding="utf-8") as f:
    new_config = replace_placeholders(json.load(f))

if os.path.isfile(settings_file):
    # Back up before modifying — restoring is as simple as cp settings.json.bak settings.json
    backup = settings_file + ".bak"
    shutil.copy2(settings_file, backup)
    with open(settings_file, encoding="utf-8") as f:
        settings = json.load(f)
    settings["hooks"] = new_config["hooks"]
    print(f"  Merged hooks into existing settings.")
    print(f"  Backup saved to: {backup}")
else:
    settings = new_config
    print("  Created new settings file.")

with open(settings_file, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
INSTALL_PYEOF

if [ $? -ne 0 ]; then
  echo "ERROR: Failed to generate settings. Check Python output above."
  exit 1
fi

# --- Validate ---
echo ""
echo "Validating..."
export _CLAUDE_SETTINGS="$SETTINGS_FILE"
$PYTHON_CMD - << 'VALIDATE_PYEOF'
import json, os
settings_file = os.environ["_CLAUDE_SETTINGS"]
with open(settings_file, encoding="utf-8") as f:
    d = json.load(f)
h = d.get("hooks", {})
print(f"  Valid JSON. {len(h)} event types configured:")
for k, v in h.items():
    print(f"    {k}: {len(v)} entry/entries")
VALIDATE_PYEOF

echo ""
echo "=== Installation complete ==="
echo ""
echo "Hooks will take effect on your next Claude Code session."
echo ""
echo "Installed hooks:"
echo "  - Notification:                  Desktop alerts when Claude needs attention"
echo "  - PreToolUse (Edit|Write):        Blocks edits to sensitive files + scans content for secrets"
echo "  - PostToolUse (Write|Edit):       Syntax validation (.py, .json, .toml)"
echo "  - PostToolUse (Bash):             Bash command intelligence recording"
echo "  - Stop:                           Session stats summary + log rotation"
echo "  - SessionStart:                   Git context, file cleanup, handoff + learnings restore"
echo "  - SubagentStart/Stop:             Event logging"
echo "  - UserPromptSubmit:               Agent team suggestions for complex tasks"
echo "  - PreCompact:                     Saves handoff, session summary, and learnings before compaction"
echo "  - PermissionRequest:              Auto-approves ExitPlanMode"
echo "  - ConfigChange/PostToolUseFailure: Event logging"
echo ""
echo "Log file: $CLAUDE_DIR/logs/hook-events.jsonl"
echo "Handoffs: $CLAUDE_DIR/handoffs/"
echo "Sessions: $CLAUDE_DIR/docs/sessions/"
echo ""
echo "NOTE: Existing settings backed up to $SETTINGS_FILE.bak"
