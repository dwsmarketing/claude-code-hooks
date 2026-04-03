# Remote Access via Claude Dispatch

This command helps you set up and use the **Dispatch** feature in the Claude mobile app to send tasks to a running Claude Code session on your desktop.

## What Is Dispatch?

Dispatch lets you send tasks to Claude Code from the Claude iOS/Android app — so you can kick off work on your desktop PC while you're away from it.

## Prerequisites

1. **Claude mobile app** installed (iOS or Android)
2. **Same Anthropic account** signed in on both devices
3. A **Claude Code session open** on the target desktop machine (the Desktop App must be running and have an active session)

## How to Use

### From your phone (Claude mobile app):
1. Open the Claude app
2. Tap the **Dispatch** icon (lightning bolt / remote icon in the compose area)
3. Select your desktop machine from the device list
4. Type your task and send — Claude Code on your desktop will pick it up

### From this session (confirm Dispatch is active):

Run the following to check that your current session is reachable:

```bash
echo "Session ID: $CLAUDE_SESSION_ID"
echo "Machine: $(hostname)"
echo "Claude Code: $(which claude 2>/dev/null || echo 'Desktop App')"
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Desktop not appearing in Dispatch list | Ensure the Desktop App is open with an active session |
| Same account on both devices? | Sign out and back in on one device to re-sync |
| Task not arriving | Check your internet connection on both devices |
| Session idle/timed out | Send any message in Claude Code first to wake the session |

## Notes

- Dispatch sends tasks to the **currently active** Claude Code session on the selected machine
- The desktop session must be open — Claude Code does not run as a background daemon by default
- Tasks dispatched while no session is open will be queued and delivered when a session starts (behavior may vary by app version)
