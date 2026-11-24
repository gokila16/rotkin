# 🎃 ROTkin

[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/gokila16.rotkin?label=VS%20Code%20Marketplace)](https://marketplace.visualstudio.com/items?itemName=gokila16.rotkin)

**A pumpkin that rots if you brainrot.**

It watches how you vibecode with Claude Code, and heals when you take breaks and think for yourself.

We all know the loop. Claude writes 400 lines, something breaks, you type "fix it". Then "still broken". Then "pls". Two hours later you haven't stood up, and you couldn't explain what your own code does.

ROTkin keeps score. It never rots because you use AI, or because you've been at it a long time, only because of how: every stuck "fix it" loop, every decision you hand to Claude, every "do that" and every pile of changes you wave through without asking what Claude did makes it a little moldier. Let it die and Claude Code stops taking your prompts until you go outside and touch actual grass.

Python standard library only. No accounts, nothing leaves your machine, and it never saves what you type: repeats are spotted from short hashes, and the feed quotes only short one-line prompts.

## Install

```bash
git clone https://github.com/gokila16/rotkin && cd rotkin
python3 install.py    # adds two hooks and a status line to ~/.claude/settings.json (backed up first)
python3 server.py     # then open http://localhost:8765
```

`python3 uninstall.py` removes only ROTkin's entries.

Prefer VS Code? [Install ROTkin from the Marketplace](https://marketplace.visualstudio.com/items?itemName=gokila16.rotkin) (or run `code --install-extension gokila16.rotkin`). It puts the pumpkin in your sidebar and starts the server for you.

## How it rots

- **Stuck loops:** "fix it", "still broken", "same error", a pasted error or log with almost no words of your own, or sending the same prompt again. Two are free, then +3 each until you break the loop.
- **Not reading the reply:** answering a long reply faster than you could have read it (30% of reading time at 250 words a minute, using only the text Claude showed you, not its code edits). Two are free, then +3 each.
- **Handing over the wheel:** "ok", "do that", "do phase 2", "next step", "continue with…", or any prompt under 6 words. That's an order, not a thought. Two are free, then +2 each.
- **Not looking at what Claude did:** after a big turn (5+ tool calls or 4,000+ tokens), a next prompt that doesn't ask about it ("what did you change?", "why did you…") or bring your own take rots 0.5, plus 1 per 8,000 tokens Claude wrote, up to 3. The longer the response, the more it costs.
- **Claude didn't explain itself:** a busy turn explained in fewer than 6 words per tool call (150 is always enough). +2.
- **Handing over your decisions:** "should I…", "you decide", "which one should we…" with no lean of your own. +1, and +3 for each more within your last 6 prompts.
- **Brain-to-bot ratio:** a little rot whenever Claude writes over 1,000 tokens per word you wrote

ROTkin reads the stretch of the thread, not single messages. Add your own take ("I'm leaning sqlite because…", "maybe it's the cookie domain") or ask about Claude's work and every streak clears: no rot, and breaking a stuck loop heals 3. A new real request also clears stuck and skimming streaks, but not hand-offs. Time alone never rots or heals it: a long focused session is fine, and sitting idle doesn't undo anything. An occasional "yes" is fine. Over two hours with no breaks, someone who writes real requests and asks why now and then stays Fresh, someone who never looks at what Claude did turns Moldy, and a full autopilot session ("do that", "fix it", pasted errors, answered within seconds) kills it in about 70 minutes.

## How it heals

- **Take a real break:** 10 minutes away heals 5 once and starts your streaks over. Idle minutes don't heal by themselves, since reading a long reply isn't a break.
- **Ask why:** prompts like "explain", "why did you", "what changed" or "walk me through" heal 1, cancel the rot for not looking at Claude's work and clear your streaks.
- **🌱 Touch Grass:** point your webcam at real grass for −40. Your keyboard doesn't count.
- **🧠 Think Mode:** without looking at the code, explain what Claude just built and why, in 40 words of your own. −15, once every 30 minutes.

A small bruise shows from 5 rot, so you can see it start. It goes **Fresh → Soft Spot → Moldy → Fruit Flies → Collapsing → Dead**. All the numbers are at the top of `rotkin.py` if you want to be nicer to yourself.

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

If anything goes wrong inside ROTkin, the hook quietly does nothing. It never breaks Claude Code.

`python3 simulate.py 3` plays a whole life cycle, death and comeback included, without spending a token. Handy for demo videos.

ROTkin isn't anti-AI. It was vibecoded with Claude Code. It just thinks you should blink sometimes.

MIT licensed.
