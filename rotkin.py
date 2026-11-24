#!/usr/bin/env python3
"""ROTkin: a pumpkin that rots if you brainrot, and heals when you think for yourself."""
import fcntl
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

# ---- Tuning knobs (times are in minutes) ----
SPEED = float(os.environ.get("ROTKIN_SPEED", 1))  # >1 makes time fly for demos
REAL_BREAK = 10       # a gap this long is a real break: one heal, and your streaks start over
# Time alone never rots or heals the pumpkin. Reading Claude's reply for 8 minutes isn't a break,
# and a long focused session isn't autopilot.
# Prompts are judged as a stretch, not one by one: the last few prompts form a window,
# and a prompt with your own thinking in it clears the window.
RECENT = 6            # how many recent prompts the window holds
DOOM_RE = re.compile(r"\b(fix it|still broken|(doesn'?t|not|isn'?t) work(ing)?|try again|pls|same error)\b", re.I)
# A pasted error or stack trace
ERROR_RE = re.compile(r"Traceback \(most recent call last\)|^\s*[\w.]*(Error|Exception)\b\s*[:(]|\berror(\[\w+\])?:|"
                      r"^\s+at \S+ \(|npm ERR!|panicked at|\bFAILED\b", re.I | re.M)
# Handing Claude a decision that is yours to make: "should I…", "you decide", "…or not?"
DELEGATE_RE = re.compile(r"\b(should (i|we)\b|should\b[^.?!]*\bor not\b|you (decide|choose|pick)\b|decide for me|pick one for me|"
                         r"make (a|the) (choice|call|decision)|what would you do|which (one )?should|do you (actually |really )?think)", re.I)
# Your own take: a reason, a lean, or a guess about the bug
OWN_RE = re.compile(r"\b(because|i think|i'?m leaning|leaning (to|towards)|i'?d rather|i prefer|my guess|i suspect|"
                    r"maybe it'?s|could it be|what if|the problem is|i noticed|i'?m pretty sure)\b", re.I)
# A "sure, keep going" with nothing of your own in it
STAMP_RE = re.compile(r"^\W*(ok(ay)?|k|yes|yep|yeah|y|sure|continue|go( ahead| on)?|do it|proceed|lgtm|looks good|sounds good|"
                      r"perfect|great|nice|next|keep going|ship it|approved?)\W*$", re.I)
# Telling Claude to carry on with its own plan: "do that", "do phase 2", "next step", "continue with step 3"
GO_RE = re.compile(r"^\W*((ok(ay)?|yes|yeah|sure|so|now|then|alright|pls|please|great|cool)\W+)*"
                   r"(do|continue( on)?( with)?|proceed( with)?|go( ahead)?( with)?|move on( to)?|start( on| with)?|"
                   r"implement|let'?s( do)?|keep going( with)?|on to|next)\W+"
                   r"(that|this|it|those|these|them|the rest|everything|all( of)?( it| them| that)?|the plan|"
                   r"(the )?next( one| step| phase| part| task)?|(phase|step|part|stage|task|option) ?\w+)\b", re.I)
# Asking about what Claude did, or how something works
CURIOUS_RE = re.compile(r"\b(explain|why does|why is|why did|how does|how did|what does|what did (you|it)|what changed|"
                        r"what was changed|walk me through|help me understand|summari[sz]e what|show me (what|the diff|the change))\b", re.I)
DECIDE_ROT = 1        # handing Claude one decision with no lean of your own
STUCK_FREE = 2        # "fix it"s and pasted errors in the window before it rots
STREAK_ROT = 3
LOOP_BREAK_HEAL = 3   # extra heal for breaking a stuck loop with your own idea
NEW_TASK_WORDS = 6    # prompts shorter than this are orders, not thinking; a longer request ends a stuck loop
# Brain-off signals
READ_WPM = 250        # reading speed for Claude's replies
SKIM_SHARE = 0.3      # answering before you could read this share of the reply means you didn't read it
SKIM_MIN_WORDS = 120  # replies shorter than this are quick to read anyway
SKIM_CAP = 90         # seconds; past this you had time to read the parts that matter
SKIM_FREE = 2         # unread replies in the window before it rots
HANDOFF_FREE = 2      # "do that", "next step", "ok" or a short order in the window before it rots
HANDOFF_ROT = 2
PASTE_LINES = 3       # a prompt this many lines long...
PASTE_OWN_WORDS = 5   # ...with fewer of your own words than this is a bare paste
REPEAT_WORDS = 4      # prompts at least this long can count as repeats
REPEAT_SIMILAR = 0.8  # this much word overlap with a recent prompt counts as sending it again
QUOTE_WORDS = 12      # the feed quotes only short one-line prompts, never pastes or long ones
# Big turns: Claude did a lot, so look at it
BUSY_ACTIONS = 5      # tool calls in one turn that make it a busy turn
BIG_TURN = 4000       # or output tokens in one turn
UNCHECKED_BASE = 0.5   # moving on from a big turn without asking what Claude did...
UNCHECKED_PER = 8000  # ...plus 1 per this many tokens Claude wrote in it...
UNCHECKED_CAP = 3     # ...up to this much
EXPLAIN_PER_ACTION = 6   # words Claude should write per tool call in a busy turn...
EXPLAIN_ENOUGH = 150     # ...though this many words is always enough
UNEXPLAINED_ROT = 2
RATIO_LIMIT = 1000    # Claude tokens per word you wrote
RATIO_ROT = 0.5
REAL_BREAK_HEAL = 5
CURIOSITY_HEAL = 1    # small on purpose: asking already cancels the rot for not looking
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
    "Dead": "💀 ROTkin has died. Prompts are now blocked.",
}
SPECK = 5             # rot where the first bruise shows on the pumpkin
EMOJI = {"Fresh": "🎃", "Soft Spot": "🎃", "Moldy": "🍄", "Fruit Flies": "🪰", "Collapsing": "😵", "Dead": "💀"}

HOME = Path(os.environ.get("ROTKIN_HOME", Path.home() / ".rotkin"))
STATE = HOME / "state.json"
DISABLED = HOME / "disabled"
DEATH = "🎃💀 Your pumpkin has died. Touch grass (or explain what Claude built in Think Mode) to revive it."


def fresh():
    return {"rot": 0, "tick": time.time(), "last_prompt": 0, "session_start": 0, "think_at": 0,
            "recent": [], "said": [], "stop_at": 0, "reply_words": 0, "unchecked": 0, "turn_actions": 0,
            "words": 0, "tokens": 0, "counted": {}, "feed": []}


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
    if s["rot"] - amount < SPECK <= s["rot"]:
        log(s, "A tiny bruise appears. Nothing to worry about. Yet.")
    if after != before:
        log(s, WORSE[after] if amount > 0 else f"Healing... back to {after}.")


def end_session(s):
    s.update(session_start=0, recent=[], said=[], unchecked=0, words=0, tokens=0)


def tick(s):
    """Notice a real break since the last time state was read. Idle minutes don't heal by themselves."""
    s["tick"] = time.time()
    if s["session_start"] and minutes_since(s["last_prompt"]) > REAL_BREAK:
        end_session(s)
        add(s, -REAL_BREAK_HEAL)
        log(s, f"Real break taken 🌿 (+{REAL_BREAK_HEAL}, streaks start over)")


def ratio_penalty(s):
    if s["tokens"] > RATIO_LIMIT * max(s["words"], 1):
        add(s, RATIO_ROT)


def own_words(text):
    """Words you wrote yourself, leaving out fenced code and lines that look pasted (code, logs, paths)."""
    text = re.sub(r"```.*?(```|$)", " ", text, flags=re.S)
    prose = [line for line in text.splitlines()
             if line.strip() and not line[:1].isspace()
             and sum(c.isalpha() or c.isspace() for c in line) >= 0.8 * len(line)]
    return len(" ".join(prose).split())


def fingerprint(text):
    """Short hashes of a prompt's words and word pairs. Enough to spot a repeat, but the prompt
    can't be read back from it, so nothing you typed (or pasted, like a key) is kept on disk."""
    words = re.findall(r"[a-z0-9']+", text.lower())
    grams = words + [a + " " + b for a, b in zip(words, words[1:])]
    return sorted({int.from_bytes(hashlib.blake2b(g.encode(), digest_size=4).digest(), "big") for g in grams})


def repeated(s, text):
    if len(text.split()) < REPEAT_WORDS:
        return False
    new = set(fingerprint(text))
    return any(len(new & set(old)) / len(new | set(old)) >= REPEAT_SIMILAR for old in s["said"])


def quotable(text):
    """A short one-line prompt, safe to show in the feed. Longer ones may hold pasted secrets."""
    return len(text.split()) <= QUOTE_WORDS and "\n" not in text.strip() and not ERROR_RE.search(text)


def unread(s, words):
    """You answered before you could have read Claude's last reply."""
    if not s["stop_at"] or s["reply_words"] < SKIM_MIN_WORDS or words >= NEW_TASK_WORDS:
        return False
    need = min(SKIM_CAP, s["reply_words"] / READ_WPM * 60 * SKIM_SHARE)
    return time.time() - s["stop_at"] < need


def kind(s, text):
    """What a prompt says about how you're working, and why: 'own', 'decide', 'stuck', 'skim', 'handoff' or 'plain'."""
    words = len(text.split())
    if OWN_RE.search(text) or CURIOUS_RE.search(text):
        return "own", ""
    if DELEGATE_RE.search(text):
        return "decide", ""
    if DOOM_RE.search(text):
        return "stuck", ""
    if ERROR_RE.search(text):
        return "stuck", "a pasted error"
    if len(text.strip().splitlines()) >= PASTE_LINES and own_words(text) < PASTE_OWN_WORDS:
        return "stuck", "a paste with no words of your own"
    if repeated(s, text):
        return "stuck", "the same prompt again"
    if unread(s, words):
        return "skim", ""
    if STAMP_RE.search(text) or GO_RE.search(text):
        return "handoff", ""
    if words < NEW_TASK_WORDS:
        return "handoff", "a short order"
    return "plain", ""


def on_prompt(s, text):
    """Returns False when the pumpkin is dead and the prompt should be blocked."""
    if s["rot"] >= 100:
        return False
    now = time.time()
    words = len(text.split())
    s["session_start"] = s["session_start"] or now
    s["words"] += words
    k, why = kind(s, text)
    quote = f"'{' '.join(text.split())[:40]}'" if quotable(text) else f"your {words}-word prompt"
    if s["unchecked"]:
        if k == "own":
            log(s, "You looked at what Claude did before moving on 👀")
        else:
            rot = min(UNCHECKED_CAP, UNCHECKED_BASE + s["unchecked"] / UNCHECKED_PER)
            add(s, rot)
            log(s, f"Claude made {s['turn_actions']} moves and wrote {s['unchecked']:,} tokens, and you moved on "
                   f"without asking what it did (+{rot:.1f} rot)")
        s["unchecked"] = 0
    if k == "own":
        stuck = s["recent"].count("stuck")
        s["recent"] = []
        if CURIOUS_RE.search(text):
            add(s, -CURIOSITY_HEAL)
            log(s, f"Curiosity detected 🧠 (+{CURIOSITY_HEAL})")
        else:
            log(s, "Your own take, then Claude's help. That's the way 👍")
        if stuck >= STUCK_FREE:
            add(s, -LOOP_BREAK_HEAL)
            log(s, f"You broke the loop with an idea of your own (+{LOOP_BREAK_HEAL})")
    else:
        s["recent"] = (s["recent"] + [k])[-RECENT:]
        n = s["recent"].count(k)
        if k == "decide" and n > 1:
            add(s, STREAK_ROT)
            log(s, f"{n} decisions handed to Claude lately, none with your own take. Decide first, then ask.")
        elif k == "decide":
            add(s, DECIDE_ROT)
            log(s, f"You asked Claude to decide: {quote}. Next time, say which way you lean.")
        elif k == "stuck" and n > STUCK_FREE:
            add(s, STREAK_ROT)
            log(s, f"Stuck loop: round {n} with no new idea. What's your guess about the bug?")
        elif k == "stuck":
            log(s, f"{quote} ({n} of {STUCK_FREE} free)" if not why else f"Stuck: {why} ({n} of {STUCK_FREE} free)")
        elif k == "skim" and n > SKIM_FREE:
            add(s, STREAK_ROT)
            log(s, f"Answered {n} replies faster than you could read them. Did you read what Claude did?")
        elif k == "skim":
            log(s, f"That was quick for a {s['reply_words']}-word reply ({n} of {SKIM_FREE} free)")
        elif k == "handoff" and n > HANDOFF_FREE:
            add(s, HANDOFF_ROT)
            log(s, f"Hand-off #{n}: {quote}. Claude is steering now. Say what you want and why.")
        elif k == "handoff":
            log(s, f"{quote} ({n} of {HANDOFF_FREE} free)")
        else:  # a real request in your own words is you steering again, not autopilot
            s["recent"] = [x for x in s["recent"] if x not in ("stuck", "skim")]
            log(s, f"A {words}-word prompt. Actual sentences! Respect.")
    s["said"] = (s["said"] + [fingerprint(text)])[-RECENT:]
    s["stop_at"] = 0  # one reply, one answer
    s["last_prompt"] = now
    ratio_penalty(s)
    return True


def on_tokens(s, n):
    """Counts Claude's output for the brain-to-bot ratio."""
    if n:
        s["tokens"] += n
        log(s, f"Claude wrote {n:,} tokens.")
        ratio_penalty(s)


def read_transcript(path):
    """Output tokens in the whole transcript, and for this turn (since your last prompt): its tokens,
    the words of text Claude showed you, and its tool calls.
    A message repeats once per content block, so tokens count each id once."""
    tokens, turn, reply, actions = {}, set(), 0, 0
    for line in open(path):
        entry = json.loads(line)
        content = entry.get("message", {}).get("content")
        blocks = content if isinstance(content, list) else []
        if entry.get("type") == "user":
            if not any(b.get("type") == "tool_result" for b in blocks):
                turn, reply, actions = set(), 0, 0  # a prompt you typed, not a tool result
        elif entry.get("type") == "assistant":
            msg = entry["message"]
            tokens[msg.get("id")] = msg.get("usage", {}).get("output_tokens", 0)
            turn.add(msg.get("id"))
            reply += sum(len(b.get("text", "").split()) for b in blocks if b.get("type") == "text")
            actions += sum(b.get("type") == "tool_use" for b in blocks)
    return sum(tokens.values()), sum(tokens[i] for i in turn), reply, actions


def on_turn(s, new_tokens, turn_tokens, reply_words, actions):
    """Claude finished a turn."""
    s.update(stop_at=time.time(), reply_words=reply_words, turn_actions=actions)
    on_tokens(s, new_tokens)
    busy = actions >= BUSY_ACTIONS
    if busy or turn_tokens >= BIG_TURN:
        s["unchecked"] = turn_tokens  # rots on your next prompt unless you ask about it
    if busy and reply_words < min(EXPLAIN_ENOUGH, EXPLAIN_PER_ACTION * actions):
        add(s, UNEXPLAINED_ROT)
        log(s, f"Claude made {actions} moves and explained them in {reply_words} words. Ask what it did.")


def on_stop(s, session_id, transcript_path):
    total, turn_tokens, reply, actions = read_transcript(transcript_path)
    new = total - s["counted"].get(session_id, 0)
    s["counted"] = dict(list({**s["counted"], session_id: total}.items())[-50:])
    on_turn(s, max(new, 0), turn_tokens, reply, actions)


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
        "stuck": s["recent"].count("stuck"),
        "autopilot": s["recent"].count("skim") + s["recent"].count("handoff"),
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
        s["said"] = [x for x in s["said"] if isinstance(x, list)]  # drop prompt text older versions kept
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
        print("ROTkin disabled. Hooks will do nothing.")
    elif cmd == "enable":
        DISABLED.unlink(missing_ok=True)
        print("ROTkin enabled.")
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
