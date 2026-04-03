#!/usr/bin/env python3
"""PreToolUse: Edit|Write hook — two-layer file protection.

Layer 1 (Path check): Blocks edits to sensitive files by path pattern.
Layer 2 (Content scan): Scans file content being written for secret patterns.

Exit 0 = allow
Exit 2 = block (feedback injected into Claude's context)

Works on macOS, Linux, and Windows (Python 3.8+).

# =============================================================================
# DASHBOARD GROUNDWORK NOTE
# =============================================================================
# Protection events are high-value security signals for a dashboard:
#
#   PANEL: "Security Events" — timeline of blocked edits / detected secrets
#   ALERT: "Secret Detected" — real-time alert when credentials are intercepted
#   PANEL: "Protected File Attempts" — which protected paths Claude tried to edit
#
# To feed a dashboard, write block events to:
#   ~/.claude/logs/security-events.jsonl
# Schema:
# {
#   "timestamp": "ISO-8601",
#   "session_id": "...",
#   "type": "path_blocked" | "secret_detected",
#   "file": "path/to/file",
#   "pattern_matched": ".env",
#   "secret_type": "aws_access_key"    # only for secret_detected
# }
# =============================================================================
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Layer 1: Path-based protection
# Files whose paths match any of these substrings will be blocked.
# ---------------------------------------------------------------------------
PROTECTED_PATH_PATTERNS = [
    ".env",
    "package-lock.json",
    "yarn.lock",
    ".git/",
    ".gitignore",
    "secrets",
    "credentials",
    ".key",
    ".pem",
    ".cert",
    "id_rsa",
    "id_ed25519",
]

# ---------------------------------------------------------------------------
# Layer 2: Content-based secret scanning
# Patterns applied to the content being written. Each is a (name, regex) tuple.
# Based on patterns from anthropics/claude-code security-guidance plugin.
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    # Cloud provider keys
    ("aws_access_key",      re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE)),
    ("aws_secret_key",      re.compile(r"(?i)aws[_\-.]?secret[_\-.]?(?:access[_\-.]?)?key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}")),
    # GitHub / GitLab tokens
    ("github_token",        re.compile(r"ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}")),
    ("gitlab_token",        re.compile(r"glpat-[A-Za-z0-9\-_]{20}")),
    # Generic API key assignments
    ("api_key_assignment",  re.compile(r"(?i)(?:api[_\-.]?key|api[_\-.]?secret|app[_\-.]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9\-_]{16,}")),
    # Generic password assignments
    ("password_assignment", re.compile(r"(?i)password\s*[:=]\s*['\"](?!.*\{)[^'\"]{8,}['\"]")),
    # Bearer tokens in code
    ("bearer_token",        re.compile(r"Bearer\s+[A-Za-z0-9\-_.~+/]+=*")),
    # Private key headers
    ("private_key_header",  re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    # Slack tokens
    ("slack_token",         re.compile(r"xox[baprs]-[A-Za-z0-9\-]+")),
    # Anthropic / OpenAI keys
    ("anthropic_key",       re.compile(r"sk-ant-[A-Za-z0-9\-_]{90,}")),
    ("openai_key",          re.compile(r"sk-[A-Za-z0-9]{48}")),
]

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs")
SECURITY_LOG = os.path.join(LOG_DIR, "security-events.jsonl")


def log_block(event_type, file_path, pattern_matched, secret_type=None, session_id=""):
    """Write a security event to security-events.jsonl for future dashboard."""
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "type": event_type,
        "file": file_path,
        "pattern_matched": pattern_matched,
    }
    if secret_type:
        entry["secret_type"] = secret_type
    try:
        with open(SECURITY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError:
        pass


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    session_id = data.get("session_id", "")
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "") or tool_input.get("new_string", "")

    # --- Layer 1: Path check ---
    if file_path:
        # Normalize to forward slashes so patterns work on Windows too
        normalized_path = file_path.replace("\\", "/")
        for pattern in PROTECTED_PATH_PATTERNS:
            if pattern in normalized_path:
                log_block("path_blocked", file_path, pattern, session_id=session_id)
                print(
                    f"Blocked: cannot edit '{file_path}' (matches protected pattern '{pattern}'). "
                    "Ask the user for explicit permission to modify this file.",
                    file=sys.stderr,
                )
                sys.exit(2)

    # --- Layer 2: Content secret scan ---
    if content and isinstance(content, str):
        for secret_name, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                log_block("secret_detected", file_path, secret_name, secret_type=secret_name, session_id=session_id)
                print(
                    f"Blocked: the content being written to '{os.path.basename(file_path) or 'file'}' "
                    f"appears to contain a credential or secret ({secret_name}). "
                    "Remove the secret before writing. Store sensitive values in environment variables "
                    "or a secrets manager, never hardcoded in source files.",
                    file=sys.stderr,
                )
                sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
