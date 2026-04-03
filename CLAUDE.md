# Claude Code Configuration - RuFlo V3

## Behavioral Rules (Always Enforced)

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested
- NEVER save working files, text/mds, or tests to the root folder
- Never continuously check status after spawning a swarm — wait for results
- ALWAYS read a file before editing it
- NEVER commit secrets, credentials, or .env files

## File Organization

- NEVER save to root folder — use the directories below
- Use `/src` for source code files
- Use `/tests` for test files
- Use `/docs` for documentation and markdown files
- Use `/config` for configuration files
- Use `/scripts` for utility scripts
- Use `/examples` for example code

## Project Architecture

- Follow Domain-Driven Design with bounded contexts
- Keep files under 500 lines
- Use typed interfaces for all public APIs
- Prefer TDD London School (mock-first) for new code
- Use event sourcing for state changes
- Ensure input validation at system boundaries

### Project Config

- **Topology**: hierarchical-mesh
- **Max Agents**: 15
- **Memory**: hybrid
- **HNSW**: Enabled
- **Neural**: Enabled

## Build & Test

```bash
# Build
npm run build

# Test
npm test

# Lint
npm run lint
```

- ALWAYS run tests after making code changes
- ALWAYS verify build succeeds before committing

## Security Rules

- NEVER hardcode API keys, secrets, or credentials in source files
- NEVER commit .env files or any file containing secrets
- Always validate user input at system boundaries
- Always sanitize file paths to prevent directory traversal
- Run `npx @claude-flow/cli@latest security scan` after security-related changes

## Concurrency: 1 MESSAGE = ALL RELATED OPERATIONS

- All operations MUST be concurrent/parallel in a single message
- Use Claude Code's Task tool for spawning agents, not just MCP
- ALWAYS batch ALL todos in ONE TodoWrite call (5-10+ minimum)
- ALWAYS spawn ALL agents in ONE message with full instructions via Task tool
- ALWAYS batch ALL file reads/writes/edits in ONE message
- ALWAYS batch ALL Bash commands in ONE message

## Swarm Orchestration

- MUST initialize the swarm using CLI tools when starting complex tasks
- MUST spawn concurrent agents using Claude Code's Task tool
- Never use CLI tools alone for execution — Task tool agents do the actual work
- MUST call CLI tools AND Task tool in ONE message for complex work

### 3-Tier Model Routing (ADR-026)

| Tier | Handler | Latency | Cost | Use Cases |
|------|---------|---------|------|-----------|
| **1** | Agent Booster (WASM) | <1ms | $0 | Simple transforms (var→const, add types) — Skip LLM |
| **2** | Haiku | ~500ms | $0.0002 | Simple tasks, low complexity (<30%) |
| **3** | Sonnet/Opus | 2-5s | $0.003-0.015 | Complex reasoning, architecture, security (>30%) |

- Always check for `[AGENT_BOOSTER_AVAILABLE]` or `[TASK_MODEL_RECOMMENDATION]` before spawning agents
- Use Edit tool directly when `[AGENT_BOOSTER_AVAILABLE]`

## Swarm Configuration & Anti-Drift

- ALWAYS use hierarchical topology for coding swarms
- Keep maxAgents at 6-8 for tight coordination
- Use specialized strategy for clear role boundaries
- Use `raft` consensus for hive-mind (leader maintains authoritative state)
- Run frequent checkpoints via `post-task` hooks
- Keep shared memory namespace for all agents

```bash
npx @claude-flow/cli@latest swarm init --topology hierarchical --max-agents 8 --strategy specialized
```

## Swarm Execution Rules

- ALWAYS use `run_in_background: true` for all agent Task calls
- ALWAYS put ALL agent Task calls in ONE message for parallel execution
- After spawning, STOP — do NOT add more tool calls or check status
- Never poll TaskOutput or check swarm status — trust agents to return
- When agent results arrive, review ALL results before proceeding

## V3 CLI Commands

### Core Commands

| Command | Subcommands | Description |
|---------|-------------|-------------|
| `init` | 4 | Project initialization |
| `agent` | 8 | Agent lifecycle management |
| `swarm` | 6 | Multi-agent swarm coordination |
| `memory` | 11 | AgentDB memory with HNSW search |
| `task` | 6 | Task creation and lifecycle |
| `session` | 7 | Session state management |
| `hooks` | 17 | Self-learning hooks + 12 workers |
| `hive-mind` | 6 | Byzantine fault-tolerant consensus |

### Quick CLI Examples

```bash
npx @claude-flow/cli@latest init --wizard
npx @claude-flow/cli@latest agent spawn -t coder --name my-coder
npx @claude-flow/cli@latest swarm init --v3-mode
npx @claude-flow/cli@latest memory search --query "authentication patterns"
npx @claude-flow/cli@latest doctor --fix
```

## Available Agents (60+ Types)

### Core Development
`coder`, `reviewer`, `tester`, `planner`, `researcher`

### Specialized
`security-architect`, `security-auditor`, `memory-specialist`, `performance-engineer`

### Swarm Coordination
`hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`

### GitHub & Repository
`pr-manager`, `code-review-swarm`, `issue-tracker`, `release-manager`

### SPARC Methodology
`sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`

## Memory Commands Reference

```bash
# Store (REQUIRED: --key, --value; OPTIONAL: --namespace, --ttl, --tags)
npx @claude-flow/cli@latest memory store --key "pattern-auth" --value "JWT with refresh" --namespace patterns

# Search (REQUIRED: --query; OPTIONAL: --namespace, --limit, --threshold)
npx @claude-flow/cli@latest memory search --query "authentication patterns"

# List (OPTIONAL: --namespace, --limit)
npx @claude-flow/cli@latest memory list --namespace patterns --limit 10

# Retrieve (REQUIRED: --key; OPTIONAL: --namespace)
npx @claude-flow/cli@latest memory retrieve --key "pattern-auth" --namespace patterns
```

## Quick Setup

```bash
claude mcp add claude-flow -- npx -y @claude-flow/cli@latest
npx @claude-flow/cli@latest daemon start
npx @claude-flow/cli@latest doctor --fix
```

## Claude Code vs CLI Tools

- Claude Code's Task tool handles ALL execution: agents, file ops, code generation, git
- CLI tools handle coordination via Bash: swarm init, memory, hooks, routing
- NEVER use CLI tools as a substitute for Task tool agents

## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues

---

## Pokemon Forest Hill ROM Hack (pokefirered decompilation)

Project root: `/Users/derryksivley/pokemon-forest-hill/pokefirered/`

### Build Command
```bash
cd /Users/derryksivley/pokemon-forest-hill/pokefirered
DEVKITARM=/opt/devkitpro/devkitARM make
```
Do NOT use `npm run build` — this is a GBA C/assembly project built with devkitARM.

### ROM Debugging — Critical Rules
1. **Vanilla parity check FIRST.** Before spending any time on OS/emulator diagnosis, build `upstream/master` and test it. If vanilla works and the hack doesn't, the bug is in our code. This single step would have saved hours in session B-3.
   ```bash
   git worktree add /tmp/pokefirered-vanilla upstream/master
   cp /Users/derryksivley/pokemon-forest-hill/pokefirered/tools /tmp/pokefirered-vanilla/ -r
   cd /tmp/pokefirered-vanilla && DEVKITARM=/opt/devkitpro/devkitARM make
   open -a mGBA /tmp/pokefirered-vanilla/pokefirered.gba
   # Cleanup: git worktree remove /tmp/pokefirered-vanilla --force
   ```
2. **Do not diagnose OS/emulator/keyboard until vanilla parity is confirmed.**
3. **Both mGBA and OpenEmu are affected by the same ROM bugs** — if both stick, it's the ROM.
4. **mGBA `/opt/homebrew/bin/mgba` is a shell wrapper** that launches the Qt `.app`. There is no separate SDL build via Homebrew.

### oak_speech.c State Machine Architecture
- `Task_NewGameScene` owns `gMain.state` as its internal sub-state counter (cases 0–10+).
- Case 10 is where the Controls Guide hands off to `Task_ControlsGuide_HandleInput` — or in Forest Hill, skips directly to `Task_PikachuIntro_LoadPage1`.
- Data macros (`tTimer = data[3]`, `tTextCursorSpriteId = data[5]`, etc.) are defined at line ~691 and work as `gTasks[taskId].macroName` inside functions that have no local `s16 *data`, or as `macroName` inside functions that do.
- `sOakSpeechResources` is allocated with `AllocZeroed` (case 1) — all fields start at 0.
- Window counts: page 1 allocates `NUM_CONTROLS_GUIDE_PAGE_1_WINDOWS = 1` window; pages 2–3 allocate `NUM_CONTROLS_GUIDE_PAGES_2_3_WINDOWS = 2` windows. These MUST match any cleanup loops.

### Window System Rule
**Always clean up exactly as many windows as were allocated.** `Task_ControlsGuide_Clear`'s cleanup loop hardcodes `NUM_CONTROLS_GUIDE_PAGES_2_3_WINDOWS = 2`. If you exit the Controls Guide from page 1 (only 1 window allocated), you MUST do the cleanup yourself with count = 1, not route through `Task_ControlsGuide_Clear`. Routing through it causes a double-`RemoveWindow(0)` which corrupts the entire window/text infrastructure and manifests as game auto-advancing without input.

### Session Docs
- `docs/b3-input-bug-postmortem.md` — full technical post-mortem on the B-3 input bug
- `docs/phase-b4-brief.md` — Phase B-4 briefing with exact file paths and task breakdown
