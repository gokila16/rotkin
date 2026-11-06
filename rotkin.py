#!/usr/bin/env python3
"""Rotkin: a pumpkin that rots while you vibecode and heals when you think for yourself."""
import fcntl
import json
import os
import re
import sys
import time
from pathlib import Path

# ---- Tuning knobs (times are in minutes) ----
SPEED = float(os.environ.get("ROTKIN_SPEED", 1))  # >1 makes time fly for demos
BREAK_AFTER = 5       # a gap this long starts healing
REAL_BREAK = 10       # a gap this long ends the session
GRACE = 25            # free minutes of continuous session
SESSION_ROT = 0.5     # rot per minute after the grace period
DOOM_RE = re.compile(r"\b(fix it|still broken|(doesn'?t|not|isn'?t) work(ing)?|try again|pls|same error)\b", re.I)
# Handing Claude a decision that is yours to make: "should I…", "you decide", "…or not?"
DELEGATE_RE = re.compile(r"\b(should (i|we)\b|should\b[^.?!]*\bor not\b|you (decide|choose|pick)\b|decide for me|pick one for me|"
                         r"make (a|the) (choice|call|decision)|what would you do|which (one )?should|do you (actually |really )?think)", re.I)
DELEGATE_ROT = 2
CURIOUS_RE = re.compile(r"\b(explain|why does|why is|how does|what does|walk me through|help me understand)\b", re.I)
DOOM_WINDOW = 3       # doom prompts this close together build a streak
DOOM_FREE = 3         # streak length you get away with
DOOM_ROT = 2
RATIO_LIMIT = 1000    # Claude tokens per word you wrote
RATIO_ROT = 0.5
IDLE_HEAL = 2         # per idle minute past BREAK_AFTER
REAL_BREAK_HEAL = 10
CURIOSITY_HEAL = 3
GRASS_HEAL = 40
THINK_HEAL = 15
THINK_WORDS = 40
THINK_COOLDOWN = 30
STAGES = [(100, "Dead"), (80, "Collapsing"), (60, "Fruit Flies"), (40, "Moldy"), (20, "Soft Spot"), (0, "Fresh")]
WORSE = {
    "Soft Spot": "A soft spot appears. Maybe stretch?",
    "Moldy": "Mold detected. When did you last blink?",
    "Fruit Flies": "Fruit flies have moved in. They brought friends.",
    "Collapsing": "Structural integrity: questionable.",
    "Dead": "💀 Rotkin has died. Prompts are now blocked.",
}
EMOJI = {"Fresh": "🎃", "Soft Spot": "🎃", "Moldy": "🍄", "Fruit Flies": "🪰", "Collapsing": "😵", "Dead": "💀"}

HOME = Path(os.environ.get("ROTKIN_HOME", Path.home() / ".rotkin"))
STATE = HOME / "state.json"
DISABLED = HOME / "disabled"
DEATH = "🎃💀 Your pumpkin has died. Touch grass (or explain what Claude built in Think Mode) to revive it."


def fresh():
    return {"rot": 0, "tick": time.time(), "last_prompt": 0, "session_start": 0, "doom_last": 0,
            "think_at": 0, "doom_streak": 0, "words": 0, "tokens": 0, "counted": {}, "feed": []}


def minutes_since(t):
    return (time.time() - t) * SPEED / 60


def stage(rot):
    return next(name for floor, name in STAGES if rot >= floor)


def log(s, msg):
    s["feed"] = (s["feed"] + [{"t": time.time(), "msg": msg}])[-30:]


def add(s, amount):
    before = stage(s["rot"])
    s["rot"] = min(100, max(0, s["rot"] + amount))
    after = stage(s["rot"])
    if after != before:
        log(s, WORSE[after] if amount > 0 else f"Healing... back to {after}.")


def end_session(s):
    s.update(session_start=0, doom_streak=0, words=0, tokens=0)


def tick(s):
    """Apply time-based rot and healing since the last time state was read."""
    dt = minutes_since(s["tick"])
    s["tick"] = time.time()
    idle = minutes_since(s["last_prompt"])
    if idle > BREAK_AFTER:
        add(s, -IDLE_HEAL * min(dt, idle - BREAK_AFTER))
        if idle > REAL_BREAK and s["session_start"]:
            end_session(s)
            add(s, -REAL_BREAK_HEAL)
            log(s, "Real break taken 🌿")
    elif s["session_start"]:
        overtime = minutes_since(s["session_start"]) - GRACE
        add(s, SESSION_ROT * max(0, min(dt, overtime)))


def ratio_penalty(s):
    if s["tokens"] > RATIO_LIMIT * max(s["words"], 1):
        add(s, RATIO_ROT)


def on_prompt(s, text):
    """Returns False when the pumpkin is dead and the prompt should be blocked."""
    if s["rot"] >= 100:
        return False
    now = time.time()
    words = len(text.split())
    s["session_start"] = s["session_start"] or now
    s["words"] += words
    if DELEGATE_RE.search(text):
        add(s, DELEGATE_ROT)
        log(s, f"You asked Claude to make your call: '{text[:40]}'. Decide first, then ask.")
    elif CURIOUS_RE.search(text):
        s["doom_streak"] = 0
        add(s, -CURIOSITY_HEAL)
        log(s, f"Curiosity detected 🧠 (+{CURIOSITY_HEAL})")
    elif DOOM_RE.search(text):
        streak = minutes_since(s["doom_last"]) <= DOOM_WINDOW
        s["doom_streak"] = s["doom_streak"] + 1 if streak else 1
        s["doom_last"] = now
        log(s, f"Doom prompt detected: '{text[:40]}' (x{s['doom_streak']})")
        if s["doom_streak"] > DOOM_FREE:
            add(s, DOOM_ROT)
    else:
        s["doom_streak"] = 0
        log(s, f"A {words}-word prompt. Actual sentences! Respect.")
    s["last_prompt"] = now
    ratio_penalty(s)
    return True


def on_tokens(s, n):
    """Counts Claude's output for the brain-to-bot ratio. Volume alone never rots the pumpkin."""
    if n:
        s["tokens"] += n
        log(s, f"Claude wrote {n:,} tokens.")
        ratio_penalty(s)


def transcript_tokens(path):
    """Output tokens in a transcript. A message repeats once per content block, so count each id once."""
    tokens = {}
    for line in open(path):
        entry = json.loads(line)
        if entry.get("type") == "assistant":
            msg = entry["message"]
            tokens[msg.get("id")] = msg.get("usage", {}).get("output_tokens", 0)
    return sum(tokens.values())


def on_stop(s, session_id, transcript_path):
    total = transcript_tokens(transcript_path)
    new = total - s["counted"].get(session_id, 0)
    s["counted"] = dict(list({**s["counted"], session_id: total}.items())[-50:])
    on_tokens(s, max(new, 0))


def on_grass(s):
    add(s, -GRASS_HEAL)
    end_session(s)
    log(s, "🌱 Grass touched! Photosynthesis restored.")


def on_think(s, text):
    words = len(text.split())
    if words < THINK_WORDS:
        return False, f"Only {words} words. Your pumpkin needs at least {THINK_WORDS} of your own."
    wait = THINK_COOLDOWN - minutes_since(s["think_at"])
    if wait > 0:
        return False, f"Big brain is recharging. Try again in {wait:.0f} min."
    s["think_at"] = time.time()
    s["words"] += words
    add(s, -THINK_HEAL)
    log(s, "🧠 You explained it yourself. The rubber duck is proud.")
    return True, "Thinking healed your pumpkin!"


def view(s):
    return {
        "rot": round(s["rot"], 1),
        "stage": stage(s["rot"]),
        "session_minutes": round(minutes_since(s["session_start"])) if s["session_start"] else 0,
        "tokens": s["tokens"],
        "words": s["words"],
        "ratio": round(s["tokens"] / max(s["words"], 1)),
        "doom_streak": s["doom_streak"],
        "feed": s["feed"][::-1],
    }


def apply(event, *args):
    """Load state, run one event on it, save, and return the event's result.
    The lock stops the server and the hooks from writing at the same time."""
    HOME.mkdir(exist_ok=True)
    HOME.chmod(0o700)  # the feed holds bits of your prompts, so keep it private
    with open(HOME / "lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        s = {**fresh(), **json.loads(STATE.read_text())} if STATE.exists() else fresh()
        tick(s)
        result = event(s, *args)
        STATE.write_text(json.dumps(s))
    return result


def reset(s):
    s.clear()
    s.update(fresh())
    log(s, "🎃 A fresh pumpkin has arrived. Don't ruin it.")


def hook(kind):
    if os.environ.get("ROTKIN_DISABLE") == "1" or DISABLED.exists():
        return 0
    event = json.load(sys.stdin)
    if kind == "prompt" and not apply(on_prompt, event.get("prompt", "")):
        print(DEATH, file=sys.stderr)
        return 2
    if kind == "stop":
        apply(on_stop, event.get("session_id", ""), event["transcript_path"])
    return 0


def main(args):
    cmd = args[0] if args else "status"
    if cmd == "hook":
        try:
            code = hook(args[1])
        except Exception:
            code = 0  # never break Claude Code
        sys.exit(code)
    elif cmd == "disable":
        HOME.mkdir(exist_ok=True)
        DISABLED.touch()
        print("Rotkin disabled. Hooks will do nothing.")
    elif cmd == "enable":
        DISABLED.unlink(missing_ok=True)
        print("Rotkin enabled.")
    elif cmd == "reset":
        apply(reset)
        print("Fresh pumpkin!")
    elif cmd == "line":
        v = apply(view)
        print(f"{EMOJI[v['stage']]} {v['stage']} · {v['rot']:.0f} rot")
    elif cmd == "status":
        v = apply(view)
        print(f"{v['stage']}: rot {v['rot']}/100, {v['tokens']:,} tokens, ratio 1 : {v['ratio']}")
    else:
        print("usage: rotkin.py [status | line | reset | disable | enable]")


if __name__ == "__main__":
    main(sys.argv[1:])
