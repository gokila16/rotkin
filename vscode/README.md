# 🎃 ROTkin

**A pumpkin that rots if you brainrot.**

It sits in your sidebar, watches how you vibecode with Claude Code, and heals when you take breaks and think for yourself.

Every "fix it", every decision you hand to Claude, every "do that" and every pile of changes you never ask about makes ROTkin a little moldier. Using AI never rots it by itself; using it on autopilot does. Let it die and Claude Code stops taking your prompts until you touch actual grass.

## Requirements

- macOS or Linux
- Python 3.8 or newer (`python3` on your PATH)
- [Claude Code](https://claude.com/claude-code)

## Getting started

1. Install the extension. ROTkin asks to connect to Claude Code. Click **Connect**.
   This adds two hooks and a status line to `~/.claude/settings.json`, after backing it up. Your other settings stay as they are.
2. Find **ROTkin** in the Explorer sidebar. The status bar shows its rot level.
3. Click the status bar item for the full dashboard, with **🌱 Touch Grass** (webcam check for real grass) and **🧠 Think Mode**.

The extension starts the dashboard server at http://localhost:8765 by itself. Nothing leaves your machine. State lives in `~/.rotkin/`.

## Commands

- **ROTkin: Open Dashboard**
- **ROTkin: Connect to Claude Code**
- **ROTkin: Disconnect from Claude Code** removes only ROTkin's entries. Do this before uninstalling the extension.

## What rots it

| | |
|---|---|
| Stuck loops | "fix it", "still broken", "same error", bare pasted errors or logs, or the same prompt again. 2 free, then +3 each |
| Not reading the reply | Answering a long reply faster than you could have read it. 2 free, then +3 each |
| Handing over the wheel | "ok", "do that", "do phase 2", "next step", or any prompt under 6 words. 2 free, then +2 each |
| Not looking at what Claude did | After a turn with 5+ tool calls or 4,000+ tokens, moving on without asking about it. 0.5 + 1 per 8,000 tokens, up to 3 |
| Claude didn't explain itself | A busy turn explained in fewer than 6 words per tool call. +2 |
| Handing over your decisions | "should I…", "you decide", "which one should we…" with no lean of your own. +1, then +3 for each more within 6 prompts |
| Brain-to-bot ratio | Claude writing over 1,000 tokens per word you wrote |

Stay away 10 minutes and it counts as a real break: your streaks and token count reset, and you heal 5. Idle minutes don't heal by themselves, and time alone never rots it. A small bruise shows from 5 rot.

Curiosity heals too. A prompt with "explain", "why did you", "what changed", "walk me through" and the like heals 1, cancels the rot for not looking at Claude's work and clears your streaks. Adding your own take ("I'm leaning X because…", "maybe it's the config") clears them too, and breaking a stuck loop that way heals 3.

## License

MIT
