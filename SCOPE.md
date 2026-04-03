# Repository Scope — Current State and Strategic Note

## Original Scope

This repository was created as a focused collection of **Claude Code hooks** — scripts wired into the 13 hook event types (PreToolUse, PostToolUse, SessionStart, etc.) to add observability, context persistence, file protection, and agent routing to Claude Code sessions.

## Current State (as of April 2026)

The repository now contains or directly supports components that go beyond the hooks system:

| Component | Type | Location |
|-----------|------|----------|
| Hook scripts (`hooks/*.py`) | Claude Code hooks | `~/.claude/hooks/` |
| Hook config (`settings-hooks.json`) | Hook wiring template | merged into `~/.claude/settings.json` |
| Scheduled tasks (`SKILL.md` files) | Claude Code scheduled sessions | `~/.claude/scheduled-tasks/` |
| Maintenance job (`*.plist`) | macOS launchd agent | `~/Library/LaunchAgents/` |
| Val Town dashboard endpoint | Hosted web service | Val Town (`claudeCodeDashboard`) |

The **scheduled tasks** and **launchd agent** are not hooks — they are separate scheduling mechanisms that run nightly maintenance work (learning review, intelligence consolidation, log rotation) independently of any active Claude Code session.

The **Val Town dashboard endpoint** is a hosted stub for a future activity visualization tool that would consume hook-event data — again, not a hook itself.

## What This Means

The repository has begun to evolve into a broader **Claude Code ecosystem configuration toolkit**, covering:

- **Hooks** — reactive automation tied to Claude Code events
- **Scheduled tasks** — proactive maintenance that runs on cron-like schedules
- **Infrastructure** — system-level services (launchd) supporting the above
- **Observability groundwork** — data schemas, log file conventions, and a stub dashboard endpoint designed to eventually visualize all of the above

## Strategic Options to Assess

When planning the next phase of this project, consider:

**Option A — Expand scope in place**
Rename to `claude-code-toolkit` or `claude-code-config` and reorganize:
```
hooks/           # hook scripts (current)
scheduled-tasks/ # SKILL.md templates for recurring Claude sessions
infrastructure/  # launchd plists, Windows Task Scheduler XMLs
dashboard/       # Val Town code, schema docs, integration guide
install.sh       # updated to handle all components
```

**Option B — Split into focused repos**
Keep this repo as hooks-only and create a sibling:
- `dwsmarketing/claude-code-hooks` — hooks scripts + settings-hooks.json (current)
- `dwsmarketing/claude-code-toolkit` — scheduled tasks, infrastructure, dashboard

**Option C — Monorepo with clear boundaries**
Keep everything here but add clear directory structure and separate install scripts per component. Each component gets its own `README` in its subdirectory.

## Recommendation

Assess before the next major addition. The current state is manageable — the divergence is modest. The decision point will come if/when the dashboard is built out (it will likely need its own install flow, environment variables, and documentation that would be awkward alongside the hooks README).

## What Has NOT Changed

- All hook scripts remain fully functional and the primary content of this repo
- `install.sh` still installs only the hooks and settings-hooks.json
- The repo name and URL remain unchanged — no action required today
