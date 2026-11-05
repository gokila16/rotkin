# 🎃 Rotkin

**A pumpkin that rots while you vibecode with Claude Code, and heals when you take breaks and think for yourself.**

We all know the loop. Claude writes 400 lines, something breaks, you type "fix it". Then "still broken". Then "pls". Two hours later you haven't stood up, and you couldn't explain what your own code does.

Rotkin keeps score. Every doom prompt, giant reply and hour without a break makes it a little moldier. Let it die and Claude Code stops taking your prompts until you go outside and touch actual grass.

Python standard library only. No accounts, nothing leaves your machine.

## Install

```bash
git clone https://github.com/gokila16/rotkin && cd rotkin
python3 install.py    # adds two hooks and a status line to ~/.claude/settings.json (backed up first)
python3 server.py     # then open http://localhost:8765
```

`python3 uninstall.py` removes only Rotkin's entries.

Prefer VS Code? The extension in `vscode/` puts the pumpkin in your sidebar and starts the server for you.

## How it rots

- **Long sessions:** +0.5 per minute after 25 minutes without a 10-minute break
- **Token burn:** +1 per 10,000 tokens Claude writes
- **Doom-prompting:** "fix it", "still broken", "try again"… past 3 in a row, +2 each
- **Brain-to-bot ratio:** a little rot whenever Claude writes over 1,000 tokens per word you wrote

A bad session (a prompt every 2 minutes, mostly "fix it", no breaks) makes it moldy in about an hour and kills it in about two.

## How it heals

- **Step away:** 2 per minute after 5 minutes idle. At 10 minutes it counts as a real break: +10 more and the session starts over.
- **Ask why:** prompts like "explain", "why does" or "walk me through" heal 3 and reset your doom streak.
- **🌱 Touch Grass:** point your webcam at real grass for −40. Your keyboard doesn't count.
- **🧠 Think Mode:** without looking at the code, explain what Claude just built and why, in 40 words of your own. −15, once every 30 minutes.

It goes **Fresh → Soft Spot → Moldy → Fruit Flies → Collapsing → Dead**. All the numbers are at the top of `rotkin.py` if you want to be nicer to yourself.

## The research behind it

- Developers using AI scored 50% vs 67% on a skills quiz, but those who asked conceptual questions kept their learning ([Anthropic, 2026](https://www.anthropic.com/research/AI-assistance-coding-skills))
- Experienced developers felt 20% faster with AI but were actually 19% slower ([METR, 2025](https://arxiv.org/abs/2507.09089))
- More confidence in AI was linked to less critical thinking ([Microsoft Research & CMU, CHI 2025](https://doi.org/10.1145/3706598.3713778))
- ChatGPT users struggled to recall essays they had just written ([MIT Media Lab, 2025, early-stage](https://arxiv.org/abs/2506.08872))
- Short breaks reduce fatigue; longer ones help more after draining work ([PLOS ONE meta-analysis, 2022](https://doi.org/10.1371/journal.pone.0272460))

The exact thresholds are design choices, not scientific limits.

## Escape hatches

```bash
python3 rotkin.py disable   # hooks do nothing (or set ROTKIN_DISABLE=1)
python3 rotkin.py enable
python3 rotkin.py reset     # a fresh pumpkin
python3 rotkin.py status
```

If anything goes wrong inside Rotkin, the hook quietly does nothing. It never breaks Claude Code.

`python3 simulate.py 3` plays a whole life cycle, death and comeback included, without spending a token. Handy for demo videos.

Rotkin isn't anti-AI. It was vibecoded with Claude Code. It just thinks you should blink sometimes.

MIT licensed.
