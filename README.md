# claude-code-hooks

A portable set of hooks for [Claude Code](https://code.claude.com) that add observability, context persistence, file protection, and intelligent agent routing.

## What's Included

| Hook | Event | What It Does |
|------|-------|-------------|
| **Desktop Notifications** | Notification | Native OS alert when Claude needs your attention |
| **Protected Files** | PreToolUse (Edit\|Write) | Blocks edits to `.env`, credentials, keys, lock files |
| **Observability Logger** | All 12 event types | Appends every hook event to a structured JSONL log |
| **Handoff System** | PreCompact + SessionStart | Saves session state before compaction, restores it after |
| **Session Summaries** | PreCompact | Writes a summary of each session segment to disk |
| **Pending Learnings** | PreCompact + SessionStart | Extracts learnings and surfaces them for review |
| **Agent Team Suggestions** | UserPromptSubmit | Recommends parallel agents for complex tasks |
| **Auto-approve ExitPlanMode** | PermissionRequest | Skips the permission dialog for plan mode exit |

## Requirements

- [Claude Code](https://code.claude.com) (CLI or Desktop)
- Python 3.8+
- bash (Git Bash on Windows, native on macOS/Linux)

## Installation

```bash
git clone https://github.com/dwsmarketing/claude-code-hooks.git
cd claude-code-hooks
bash install.sh
```

The installer:
1. Detects your Python command (`python3` or `python`)
2. Detects your OS for native notifications (macOS, Windows, Linux)
3. Copies hook scripts to `~/.claude/hooks/`
4. Creates required directories (`logs/`, `handoffs/`, `docs/sessions/`)
5. Merges the hooks configuration into your existing `~/.claude/settings.json`

Hooks take effect on your next Claude Code session.

## How It Works

### Observability

Every hook event is logged to `~/.claude/logs/hook-events.jsonl` as one JSON line:

```json
{"timestamp":"2026-04-03T14:22:01.003Z","event":"PreToolUse","session_id":"abc123","data":{...}}
```

Query with standard tools:
```bash
# Count events by type
python3 -c "import json; from collections import Counter; c=Counter(json.loads(l)['event'] for l in open('$HOME/.claude/logs/hook-events.jsonl')); print(dict(c))"

# Last 10 events
tail -10 ~/.claude/logs/hook-events.jsonl | python3 -m json.tool --no-ensure-ascii
```

### Context Persistence (Handoff System)

When Claude Code compacts your conversation (to free up context window), the **PreCompact** agent hook automatically:

1. Writes a **handoff file** (`~/.claude/handoffs/handoff-{timestamp}.md`) with: current goal, work completed, decisions made, open tasks, key context
2. Writes a **session summary** (`~/.claude/docs/sessions/{timestamp}.md`) with: what was accomplished, files changed, errors encountered
3. Appends **pending learnings** to `~/.claude/docs/pending-learnings.md`

On the next session start (or after compaction), the **SessionStart** hooks:
- Load the latest handoff into Claude's context
- Surface any pending learnings for review

### Agent Team Suggestions

The `suggest-agents.py` hook analyzes each user prompt for complexity signals:

| Signal | Points | Examples |
|--------|--------|---------|
| Scope keywords | 2 | "implement feature", "debug complex", "full-stack" |
| Broad scope | 1 | "all files", "entire codebase", "multiple components" |
| Multi-step language | 1-2 | numbered lists, "first...then", "after that" |
| Compound problems | 1 | "not sure if X or Y", "middleware...database" |
| Direct request | auto | "use parallel agents", "agent teams" |

At 3+ points, it suggests specific approaches:
- **Debug tasks** -> `/team-debug` (parallel hypothesis testing)
- **Review tasks** -> `/team-review` (multi-dimensional review)
- **Feature tasks** -> `/team-feature` (parallel development)
- **Refactor tasks** -> parallel subagents with file ownership

Simple prompts produce no output.

### File Protection

Blocks Claude from editing sensitive files:
- `.env`, `.gitignore`
- `package-lock.json`, `yarn.lock`
- Private keys (`.key`, `.pem`, `.cert`, `id_rsa`, `id_ed25519`)
- Files matching `secrets` or `credentials`

When blocked, Claude receives feedback explaining why and is asked to get explicit user permission.

## File Structure

```
~/.claude/
  hooks/
    protect-files.sh        # File edit blocker
    log-event.py            # JSONL event logger
    load-handoff.sh         # Handoff context loader
    load-learnings.sh       # Pending learnings surfacer
    suggest-agents.py       # Agent team suggester
  logs/
    hook-events.jsonl       # Event log (auto-created)
  handoffs/
    handoff-*.md            # Session handoffs (auto-created)
  docs/
    sessions/
      *.md                  # Session summaries (auto-created)
    pending-learnings.md    # Learning candidates (auto-created)
  settings.json             # Claude Code settings (hooks merged here)
```

## Customization

### Add protected file patterns

Edit `~/.claude/hooks/protect-files.sh` and add patterns to the `PROTECTED_PATTERNS` array.

### Adjust agent suggestion sensitivity

Edit `~/.claude/hooks/suggest-agents.py`:
- Change the threshold (default: 3 points) on line with `if score < 3`
- Add keyword patterns to the regex constants at the top

### Disable specific hooks

Remove or comment out entries in the `hooks` section of `~/.claude/settings.json`.

## Uninstall

```bash
# Remove hook scripts
rm ~/.claude/hooks/{protect-files.sh,log-event.py,load-handoff.sh,load-learnings.sh,suggest-agents.py}

# Remove the hooks key from settings.json (manually edit, or use Python):
python3 -c "
import json
with open('$HOME/.claude/settings.json') as f: d = json.load(f)
d.pop('hooks', None)
with open('$HOME/.claude/settings.json', 'w') as f: json.dump(d, f, indent=2)
"
```

Data directories (`logs/`, `handoffs/`, `docs/`) are preserved. Delete manually if not needed.

## License

MIT
