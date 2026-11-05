# 🎃 Rotkin

**A pumpkin that rots while you vibecode with Claude Code, and heals when you take breaks and think for yourself.**

Every "fix it", every 20,000-token reply, every hour without a break makes Rotkin a little moldier. Keep going and the fruit flies move in. Keep going after that and it dies, and Claude Code stops taking your prompts until you go outside and touch actual grass.

Python standard library only. No pip installs, no accounts, nothing leaves your machine.

## Install

```bash
git clone <your-repo-url> rotkin && cd rotkin && python3 install.py
```

This backs up `~/.claude/settings.json`, then adds two hooks and a status line next to whatever you already have. To remove it: `python3 uninstall.py` (it only removes Rotkin's entries).

## VS Code extension

The extension in `vscode/` carries its own copy of the Python app. It starts the dashboard server itself and asks before connecting to Claude Code. Its hooks run a copy at `~/.rotkin/bin/rotkin.py`, so they keep working after extension updates.

```bash
cd vscode
npx @vscode/vsce package     # copies the Python files in, then builds rotkin-<version>.vsix
```

To try it without packaging, run `node bundle.js` in `vscode/`, open that folder in VS Code and press F5.

## Run the dashboard

```bash
python3 server.py
```

Open http://localhost:8765 and leave it on a second screen. It updates every 2 seconds.

- **🌱 Touch Grass** opens your webcam and checks the photo for green. Real grass heals 40 rot. Your keyboard does not.
- **🧠 Think Mode** is a recall check: without looking at the code, explain what Claude just built and why, in at least 40 of your own words. Heals 15 rot, once every 30 minutes.

## What rots it

| | |
|---|---|
| Long sessions | +0.5 per minute after 25 minutes without a 10-minute break |
| Token burn | +1 per 10,000 tokens Claude writes |
| Doom-prompting | "fix it", "still broken", "try again", "pls"… 4+ in a row, each within 3 minutes of the last = +2 each |
| Brain-to-bot ratio | Claude writing over 1,000 tokens per word you wrote adds a little rot every event |

A bad session (a prompt every 2 minutes, mostly "fix it", no breaks) gets Rotkin moldy in about an hour and kills him in about two.

Walking away for more than 5 minutes heals 2 rot per minute. Stay away 10 minutes and it counts as a real break: the session timer and token count reset, and you heal 10 more.

Curiosity heals too. A prompt with "explain", "why does", "how does", "walk me through" and the like heals 3 and resets your doom streak.

The stages are **Fresh → Soft Spot → Moldy → Fruit Flies → Collapsing → Dead**. When Rotkin is dead, your prompts are blocked:

> 🎃💀 Your pumpkin has died. Touch grass (or explain what Claude built in Think Mode) to revive it.

All the numbers are at the top of `rotkin.py` if you want to be nicer to yourself.

## The research behind Rotkin

- Developers using AI scored 50% vs 67% on a skills quiz, but those who asked conceptual questions kept their learning ([Anthropic, 2026](https://www.anthropic.com/research/AI-assistance-coding-skills))
- Experienced developers felt 20% faster with AI but were actually 19% slower ([METR, 2025](https://arxiv.org/abs/2507.09089))
- More confidence in AI was linked to less critical thinking ([Microsoft Research & CMU, CHI 2025](https://doi.org/10.1145/3706598.3713778))
- ChatGPT users struggled to recall essays they had just written ([MIT Media Lab, 2025, early-stage](https://arxiv.org/abs/2506.08872))
- Short breaks reduce fatigue; longer ones help more after draining work ([PLOS ONE meta-analysis, 2022](https://doi.org/10.1371/journal.pone.0272460))

The exact thresholds (25 minutes, 10,000 tokens, 40 words…) are design choices, not scientific limits.

## Kill switch

```bash
python3 rotkin.py disable   # hooks do nothing (or set ROTKIN_DISABLE=1)
python3 rotkin.py enable
python3 rotkin.py reset     # a fresh pumpkin
python3 rotkin.py status
```

The hooks never break Claude Code: if anything goes wrong inside Rotkin, the hook quietly does nothing.

## Making a demo video

```bash
python3 server.py            # in one terminal
python3 simulate.py 3        # in another: 3 seconds per step
```

`simulate.py` plays a full cycle without spending a single real token: a bad session, death, touching grass, a curious question, a real break and Think Mode. To speed up real time instead, set `ROTKIN_SPEED=10` for both the server and Claude Code.

## Files

| File | What it does |
|---|---|
| `rotkin.py` | Rot engine, hooks and CLI |
| `server.py` | Dashboard server on port 8765 |
| `dashboard.html` | The pumpkin, stats, Touch Grass and Think Mode |
| `simulate.py` | Fake events for filming |
| `install.py` / `uninstall.py` | Add or remove Rotkin in Claude Code settings |
| `vscode/` | The VS Code extension (`bundle.js` copies the Python app into it) |
| `LICENSE` | MIT |

State lives in `~/.rotkin/state.json`.

---

## Devpost

**Rotkin: your pumpkin is only as healthy as your coding habits.**

We all know the loop. Claude writes 400 lines, something breaks, you type "fix it". Then "still broken". Then "pls". Two hours later you haven't stood up, and you couldn't explain what your own code does.

Rotkin is a virtual pumpkin that lives next to Claude Code and keeps score. Hooks watch every prompt you send and every token Claude writes. Long sessions with no breaks, giant token bills, doom-prompting and letting the bot do all the thinking each make it rot a little more. You can watch it go from a happy orange pumpkin to a moldy, sagging, fruit-fly-infested pile of mush, live on the dashboard.

If you let it die, it fights back: Claude Code refuses your prompts until you revive it. There are only two ways to do that, and they're both good for you:

- **Touch grass**, literally. Point your webcam at real grass and the dashboard checks it for green. (It knows your keyboard isn't grass.)
- **Think Mode.** Without looking at the code, explain what Claude just built and why, in 40 words of your own.

Rotkin isn't anti-AI. It was vibecoded with Claude Code. It just thinks you should blink sometimes.

**Built with:** Python (standard library only), Claude Code hooks, one HTML page with a hand-drawn SVG pumpkin, and webcam pixel math.
