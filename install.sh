#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo "=== Claude Code Config Installer ==="
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

# --- Detect OS and architecture ---
OS_TYPE=""
ARCH_TYPE=""
SHELL_TYPE=""
NOTIFY_CMD=""

if [[ "$OSTYPE" == "darwin"* ]]; then
  OS_TYPE="darwin"
  ARCH_TYPE="$(uname -m)"  # arm64 or x86_64
  SHELL_TYPE="${SHELL##*/}"
  NOTIFY_CMD="osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  OS_TYPE="windows"
  ARCH_TYPE="x86_64"
  SHELL_TYPE="bash"
  NOTIFY_CMD='powershell.exe -Command "[void][System.Reflection.Assembly]::LoadWithPartialName('"'"'System.Windows.Forms'"'"'); $n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; $n.Visible = $true; $n.ShowBalloonTip(5000, '"'"'Claude Code'"'"', '"'"'Claude needs your attention'"'"', '"'"'Info'"'"')"'
elif command -v notify-send &>/dev/null; then
  OS_TYPE="linux"
  ARCH_TYPE="$(uname -m)"
  SHELL_TYPE="${SHELL##*/}"
  NOTIFY_CMD="notify-send 'Claude Code' 'Claude Code needs your attention'"
else
  OS_TYPE="linux"
  ARCH_TYPE="$(uname -m)"
  SHELL_TYPE="${SHELL##*/}"
  NOTIFY_CMD="echo 'Claude Code needs your attention'"
fi

echo "Platform: $OS_TYPE ($ARCH_TYPE, shell: $SHELL_TYPE)"
echo ""

# --- Create directories ---
echo "Creating directories..."
mkdir -p "$HOOKS_DIR"
mkdir -p "$CLAUDE_DIR/logs"
mkdir -p "$CLAUDE_DIR/handoffs"
mkdir -p "$CLAUDE_DIR/docs/sessions"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/skills"
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$CLAUDE_DIR/helpers"
echo "  $CLAUDE_DIR/{hooks,logs,handoffs,docs,commands,skills,agents,helpers}"

# --- Copy hook scripts ---
echo ""
echo "Copying hook scripts..."
cp "$SCRIPT_DIR/hooks/"* "$HOOKS_DIR/"
chmod +x "$HOOKS_DIR/"*.sh "$HOOKS_DIR/"*.py 2>/dev/null || true
echo "  Copied $(ls -1 "$SCRIPT_DIR/hooks/" | wc -l | tr -d ' ') scripts to $HOOKS_DIR"

# --- Copy slash commands ---
echo ""
echo "Copying slash commands..."
if [ -d "$SCRIPT_DIR/commands" ]; then
  cp -r "$SCRIPT_DIR/commands/." "$CLAUDE_DIR/commands/"
  CMD_COUNT=$(find "$SCRIPT_DIR/commands" -name "*.md" | wc -l | tr -d ' ')
  echo "  Copied $CMD_COUNT command files to $CLAUDE_DIR/commands/"
else
  echo "  No commands/ directory found, skipping."
fi

# --- Copy skills ---
echo ""
echo "Copying skills..."
if [ -d "$SCRIPT_DIR/skills" ]; then
  cp -r "$SCRIPT_DIR/skills/." "$CLAUDE_DIR/skills/"
  SKILL_COUNT=$(ls -1 "$SCRIPT_DIR/skills/" | wc -l | tr -d ' ')
  echo "  Copied $SKILL_COUNT skill directories to $CLAUDE_DIR/skills/"
else
  echo "  No skills/ directory found, skipping."
fi

# --- Copy agents ---
echo ""
echo "Copying agents..."
if [ -d "$SCRIPT_DIR/agents" ]; then
  cp -r "$SCRIPT_DIR/agents/." "$CLAUDE_DIR/agents/"
  AGENT_COUNT=$(ls -1 "$SCRIPT_DIR/agents/" | wc -l | tr -d ' ')
  echo "  Copied $AGENT_COUNT agent category directories to $CLAUDE_DIR/agents/"
else
  echo "  No agents/ directory found, skipping."
fi

# --- Copy helpers ---
echo ""
echo "Copying helpers..."
if [ -d "$SCRIPT_DIR/helpers" ]; then
  cp -r "$SCRIPT_DIR/helpers/." "$CLAUDE_DIR/helpers/"
  HELPER_COUNT=$(ls -1 "$SCRIPT_DIR/helpers/" | wc -l | tr -d ' ')
  echo "  Copied $HELPER_COUNT helper files to $CLAUDE_DIR/helpers/"
else
  echo "  No helpers/ directory found, skipping."
fi

# --- Copy CLAUDE.md to home directory ---
echo ""
echo "Copying CLAUDE.md..."
if [ -f "$SCRIPT_DIR/CLAUDE.md" ]; then
  if [ -f "$HOME/CLAUDE.md" ]; then
    cp "$HOME/CLAUDE.md" "$HOME/CLAUDE.md.bak"
    echo "  Backed up existing ~/CLAUDE.md to ~/CLAUDE.md.bak"
  fi
  cp "$SCRIPT_DIR/CLAUDE.md" "$HOME/CLAUDE.md"
  echo "  Installed ~/CLAUDE.md"
else
  echo "  No CLAUDE.md in repo, skipping."
fi

# --- Generate and merge settings configuration ---
echo ""
echo "Merging settings configuration..."

export _CLAUDE_INSTALL_PYTHON="$PYTHON_CMD"
export _CLAUDE_INSTALL_NOTIFY="$NOTIFY_CMD"
export _CLAUDE_INSTALL_OS="$OS_TYPE"
export _CLAUDE_INSTALL_ARCH="$ARCH_TYPE"
export _CLAUDE_INSTALL_SHELL="$SHELL_TYPE"
export _CLAUDE_SCRIPT_DIR="$SCRIPT_DIR"
export _CLAUDE_SETTINGS="$SETTINGS_FILE"

$PYTHON_CMD - << 'INSTALL_PYEOF'
import json, os, shutil, sys

script_dir    = os.environ["_CLAUDE_SCRIPT_DIR"]
settings_file = os.environ["_CLAUDE_SETTINGS"]
python_cmd    = os.environ["_CLAUDE_INSTALL_PYTHON"]
notify_cmd    = os.environ["_CLAUDE_INSTALL_NOTIFY"]
os_type       = os.environ["_CLAUDE_INSTALL_OS"]
arch_type     = os.environ["_CLAUDE_INSTALL_ARCH"]
shell_type    = os.environ["_CLAUDE_INSTALL_SHELL"]

def replace_placeholders(obj):
    if isinstance(obj, str):
        return (obj
            .replace("__PYTHON__", python_cmd)
            .replace("__NOTIFY_COMMAND__", notify_cmd)
            .replace("__OS__", os_type)
            .replace("__ARCH__", arch_type)
            .replace("__SHELL__", shell_type))
    if isinstance(obj, dict):
        return {k: replace_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_placeholders(v) for v in obj]
    return obj

# Prefer settings-template.json for full merge; fall back to settings-hooks.json
template_path = os.path.join(script_dir, "settings-template.json")
hooks_only_path = os.path.join(script_dir, "settings-hooks.json")

if os.path.isfile(template_path):
    with open(template_path, encoding="utf-8") as f:
        new_config = replace_placeholders(json.load(f))
    merge_mode = "full"
else:
    with open(hooks_only_path, encoding="utf-8") as f:
        new_config = replace_placeholders(json.load(f))
    merge_mode = "hooks-only"

if os.path.isfile(settings_file):
    backup = settings_file + ".bak"
    shutil.copy2(settings_file, backup)
    with open(settings_file, encoding="utf-8") as f:
        settings = json.load(f)

    if merge_mode == "full":
        # Non-destructive merge: template fills in missing keys only.
        # Always replaces hooks (primary purpose of this repo).
        for key, value in new_config.items():
            if key not in settings:
                settings[key] = value
            elif isinstance(value, dict) and isinstance(settings[key], dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in settings[key]:
                        settings[key][sub_key] = sub_value
        settings["hooks"] = new_config["hooks"]
        print(f"  Full settings merge complete.")
    else:
        settings["hooks"] = new_config["hooks"]
        print(f"  Hooks-only merge complete.")

    print(f"  Backup saved to: {backup}")
else:
    settings = new_config
    print("  Created new settings file.")

with open(settings_file, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
INSTALL_PYEOF

if [ $? -ne 0 ]; then
  echo "ERROR: Failed to merge settings. Check Python output above."
  exit 1
fi

# --- Validate ---
echo ""
echo "Validating..."
export _CLAUDE_SETTINGS="$SETTINGS_FILE"
$PYTHON_CMD - << 'VALIDATE_PYEOF'
import json, os, glob as _glob

settings_file = os.environ["_CLAUDE_SETTINGS"]
with open(settings_file, encoding="utf-8") as f:
    d = json.load(f)
h = d.get("hooks", {})
print(f"  Valid JSON. {len(h)} hook event types configured.")
claude_dir = os.path.join(os.path.expanduser("~"), ".claude")
cmd_dir    = os.path.join(claude_dir, "commands")
skill_dir  = os.path.join(claude_dir, "skills")
agent_dir  = os.path.join(claude_dir, "agents")
cmds   = len(_glob.glob(os.path.join(cmd_dir, "**", "*.md"), recursive=True))
skills = len([x for x in os.listdir(skill_dir) if os.path.isdir(os.path.join(skill_dir, x))]) if os.path.isdir(skill_dir) else 0
agents = len([x for x in os.listdir(agent_dir) if os.path.isdir(os.path.join(agent_dir, x))]) if os.path.isdir(agent_dir) else 0
print(f"  Slash commands: {cmds} files")
print(f"  Skills:         {skills} installed")
print(f"  Agent types:    {agents} categories")
VALIDATE_PYEOF

echo ""
echo "=== Installation complete ==="
echo ""
echo "Everything takes effect on your next Claude Code session."
echo ""
echo "Installed:"
echo "  Hooks:     $HOOKS_DIR"
echo "  Commands:  $CLAUDE_DIR/commands/"
echo "  Skills:    $CLAUDE_DIR/skills/"
echo "  Agents:    $CLAUDE_DIR/agents/"
echo "  Helpers:   $CLAUDE_DIR/helpers/"
echo "  CLAUDE.md: $HOME/CLAUDE.md"
echo "  Settings:  $SETTINGS_FILE"
echo ""
echo "Log file:  $CLAUDE_DIR/logs/hook-events.jsonl"
echo "Handoffs:  $CLAUDE_DIR/handoffs/"
echo "Sessions:  $CLAUDE_DIR/docs/sessions/"
echo ""

if [[ "$OS_TYPE" == "windows" ]]; then
  echo "Windows note:"
  echo "  Claude Code stores config in %USERPROFILE%\\.claude\\"
  echo "  (same as ~/.claude/ in Git Bash — no path changes needed)."
  echo "  Restart the Claude Desktop App after install for commands to appear."
  echo ""
fi

echo "NOTE: Existing settings backed up to $SETTINGS_FILE.bak"
echo ""
echo "--- Next steps ---"
echo ""
echo "1. SYNC Windows-only commands (e.g. /project-start):"
echo "   On your Windows PC, run from inside the cloned repo:"
echo "     cp ~/.claude/commands/project-start.md commands/"
echo "     git add commands/ && git commit -m 'sync: add Windows commands' && git push"
echo "   Then on Mac: git pull && bash install.sh"
echo ""
echo "2. /remote-access is now installed."
echo "   Invoke it in Claude Code for Dispatch setup guidance."
echo ""
echo "3. Keeping machines in sync:"
echo "   After config changes on either machine -> commit, push, pull on other, run install.sh"
