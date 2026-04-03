#!/usr/bin/env python
"""Analyzes user prompts and suggests agent teams/parallel execution for complex tasks."""

import sys
import json
import re

# --- Complexity signals and their weights ---

# Direct requests for parallelism (auto-trigger)
DIRECT_TRIGGERS = re.compile(
    r"(parallel agents?|agent teams?|agent swarm|multiple agents|concurrent|in parallel)",
    re.IGNORECASE,
)

# Task scope keywords (2 points each) -- \W+ allows intervening words
SCOPE_KEYWORDS = re.compile(
    r"(refactor\W+\w+\W+entire|refactor entire|implement\W+\w*\W*feature|"
    r"build\W+\w*\W*system|comprehensive review|full review|"
    r"debug\W+(?:\w+\W+){0,3}complex|complex\W+(?:\w+\W+){0,3}debug|"
    r"migrate from|end.to.end|full.stack|across the codebase|"
    r"complete rewrite|overhaul|redesign|multi.step|production.ready)",
    re.IGNORECASE,
)

# Multi-file/broad scope indicators (1 point each)
BROAD_SCOPE = re.compile(
    r"(all files|every file|entire codebase|across all|multiple files|"
    r"several components|multiple components|multiple services|each module)",
    re.IGNORECASE,
)

# Compound problem indicators -- multiple systems/causes mentioned (1 point each)
COMPOUND_PROBLEM = re.compile(
    r"(or the |could be .+ or|might be .+ or|not sure if .+ or|"
    r"middleware.+database|frontend.+backend|client.+server|"
    r"api.+database|auth.+session|multiple possible|several areas)",
    re.IGNORECASE,
)

# Sequential/multi-step language (1 point each)
MULTI_STEP = re.compile(
    r"(step \d|first.+then|after that|once .+ is done|and also|additionally|"
    r"^\s*\d+[\.\)]\s|\band\b.+\band\b.+\band\b)",
    re.IGNORECASE | re.MULTILINE,
)

# Task-type patterns for specific suggestions
TASK_DEBUG = re.compile(r"(debug|diagnose|investigate|track down|root cause|not working|broken)", re.IGNORECASE)
TASK_REVIEW = re.compile(r"(review|audit|check for|analyze code|code quality|security scan)", re.IGNORECASE)
TASK_FEATURE = re.compile(r"(implement|build|create|add feature|develop|set up|scaffold)", re.IGNORECASE)
TASK_REFACTOR = re.compile(r"(refactor|rename across|update all|modernize|migrate)", re.IGNORECASE)


def score_complexity(prompt: str) -> tuple[int, list[str]]:
    """Score prompt complexity. Returns (score, list of matched signal names)."""
    score = 0
    signals = []

    if DIRECT_TRIGGERS.search(prompt):
        return 99, ["direct_request"]

    for match in SCOPE_KEYWORDS.finditer(prompt):
        score += 2
        signals.append(f"scope:{match.group()}")

    for match in BROAD_SCOPE.finditer(prompt):
        score += 1
        signals.append(f"broad:{match.group()}")

    step_matches = MULTI_STEP.findall(prompt)
    if len(step_matches) >= 2:
        score += 2
        signals.append(f"multi_step:{len(step_matches)}_indicators")
    elif step_matches:
        score += 1
        signals.append("multi_step:1_indicator")

    for match in COMPOUND_PROBLEM.finditer(prompt):
        score += 1
        signals.append(f"compound:{match.group().strip()}")

    # Long prompts with action verbs suggest complex tasks
    if len(prompt) > 400 and TASK_FEATURE.search(prompt):
        score += 1
        signals.append("long_prompt_with_action")

    return score, signals


def suggest(prompt: str) -> str:
    """Generate a specific suggestion based on task type."""
    suggestions = []

    if TASK_DEBUG.search(prompt):
        suggestions.append("- /team-debug: parallel hypothesis testing with multiple agents")

    if TASK_REVIEW.search(prompt):
        suggestions.append("- /team-review: multi-dimensional review (security, performance, architecture)")

    if TASK_FEATURE.search(prompt):
        suggestions.append("- /team-feature: parallel feature development with file ownership coordination")
        suggestions.append("- Launch parallel Explore agents to research before implementing")

    if TASK_REFACTOR.search(prompt):
        suggestions.append("- Launch parallel subagents with file ownership boundaries for independent changes")

    if not suggestions:
        suggestions.append("- Use the Agent tool to launch parallel subagents for independent subtasks")
        suggestions.append("- Use /team-feature, /team-debug, or /team-review for structured multi-agent work")

    return "\n".join(suggestions)


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Extract user prompt -- try known field names
    prompt = ""
    for field in ("content", "message", "prompt", "user_message", "text"):
        if field in data and isinstance(data[field], str):
            prompt = data[field]
            break
    # Also check nested structures
    if not prompt and "tool_input" in data:
        ti = data["tool_input"]
        if isinstance(ti, dict):
            for field in ("content", "message", "prompt"):
                if field in ti and isinstance(ti[field], str):
                    prompt = ti[field]
                    break

    if not prompt:
        sys.exit(0)

    score, signals = score_complexity(prompt)

    # Threshold: 3+ points triggers suggestion
    if score < 3:
        sys.exit(0)

    recommendations = suggest(prompt)

    # Output gets injected into Claude's context
    print(f"""AGENT EFFICIENCY HINT: This task appears complex enough to benefit from multi-agent execution rather than linear processing. Consider:
{recommendations}

Multi-agent approaches run faster (parallel execution) and preserve the main context window. Evaluate whether independent subtasks exist that can be delegated.""")


if __name__ == "__main__":
    main()
