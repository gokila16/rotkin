# 🎃 Rotkin

**A pumpkin in your sidebar that rots while you vibecode with Claude Code, and heals when you take breaks and think for yourself.**

Every "fix it", every 20,000-token reply, every hour without a break makes Rotkin a little moldier. Let it die and Claude Code stops taking your prompts until you touch actual grass.

## Requirements

- macOS or Linux
- Python 3.8 or newer (`python3` on your PATH)
- [Claude Code](https://claude.com/claude-code)

## Getting started

1. Install the extension. Rotkin asks to connect to Claude Code. Click **Connect**.
   This adds two hooks and a status line to `~/.claude/settings.json`, after backing it up. Your other settings stay as they are.
2. Find **Rotkin** in the Explorer sidebar. The status bar shows its rot level.
3. Click the status bar item for the full dashboard, with **🌱 Touch Grass** (webcam check for real grass) and **🧠 Think Mode**.

The extension starts the dashboard server at http://localhost:8765 by itself. Nothing leaves your machine. State lives in `~/.rotkin/`.

## Commands

- **Rotkin: Open Dashboard**
- **Rotkin: Connect to Claude Code**
- **Rotkin: Disconnect from Claude Code** removes only Rotkin's entries. Do this before uninstalling the extension.

## What rots it

| | |
|---|---|
| Long sessions | +0.5 per minute after 25 minutes without a 10-minute break |
| Token burn | +1 per 10,000 tokens Claude writes |
| Doom-prompting | "fix it", "still broken", "try again", "pls"… 4+ in a row, each within 3 minutes of the last = +2 each |
| Brain-to-bot ratio | Claude writing over 1,000 tokens per word you wrote |

Walking away for more than 5 minutes heals 2 rot per minute. Stay away 10 minutes and it counts as a real break: the session timer and token count reset, and you heal 10 more.

Curiosity heals too. A prompt with "explain", "why does", "how does", "walk me through" and the like heals 3 and resets your doom streak.

## License

MIT
