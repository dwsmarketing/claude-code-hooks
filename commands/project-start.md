You are starting a new Claude Code session for the project in the current working directory. Follow these steps carefully.

---

## Step 1: Discover existing project context

Check for these files and directories (in order of priority):

1. `CLAUDE.md` — project instructions and conventions
2. `.claude/` directory — memory, todos, plans, session state
3. `TODO.md` or `TASKS.md` — task tracking
4. `README.md` — project overview
5. `.claude/memory/` or `memory/` — persistent memory files
6. Any `*.md` files at the project root that look like planning or context docs
7. Recent git log (`git log --oneline -20`) if this is a git repo
8. `package.json`, `pyproject.toml`, `Cargo.toml`, etc. — to identify the project type

Read everything you find before proceeding.

---

## Step 2: Assess completeness

**If sufficient context exists** (CLAUDE.md + at least one of: todos, memory, recent git history):

- Summarize the current project state in 3–5 bullets:
  - What this project is
  - What was last being worked on
  - What the open tasks or next steps are
  - Any known blockers or decisions pending
- Ask: "Ready to pick up where we left off. Does this look right, or is there anything to update before we start?"
- Wait for the user to confirm or correct before doing anything else.

**If context is missing or incomplete** (no CLAUDE.md, no todos, sparse memory):

Proceed to Step 3.

---

## Step 3: Analyze and onboard (only if context is missing)

Scan the project directory:
- List the top-level structure
- Read key files (entry points, config, main source files — up to 10 files, prioritize by relevance)
- Identify: language/stack, purpose, current state, any obvious incomplete work

Then ask the user the following questions (ask all at once, not one at a time):

1. **What is this project?** — Brief description of what it does and who it's for
2. **What were you last working on?** — Most recent task, feature, or bug
3. **What are the immediate next steps?** — What should we tackle in this session?
4. **Any constraints or context I should know?** — Deadlines, decisions already made, things to avoid
5. **Preferred working style for this project?** — e.g. "make small commits", "always run tests", "check with me before refactoring"

---

## Step 4: Create or update context files

Based on what you found and the user's answers, create or update:

**`CLAUDE.md`** (at project root) — if missing or incomplete:
```
# [Project Name]

## What This Is
[1–2 sentence description]

## Stack & Architecture
[Key technologies, structure]

## Current State
[What's done, what's in progress]

## Working Conventions
[Commit style, test requirements, anything project-specific]

## Key Files
[Most important files and what they do]
```

**`.claude/todos.md`** (or update existing) — create a task list reflecting open work:
```
# Active Tasks
- [ ] [next immediate task]
- [ ] [following task]

# Backlog
- [ ] [known future work]
```

**`.claude/memory/project.md`** — key facts that should persist across sessions:
```
---
name: project-context
type: project
---
[Key decisions, architecture choices, gotchas learned]
```

Only create files that don't already exist or need updating. Never overwrite files that are complete and accurate.

---

## Step 5: Confirm and begin

After creating/updating files, give the user a one-paragraph summary of the session starting state and ask: "What would you like to work on first?"
