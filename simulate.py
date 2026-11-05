#!/usr/bin/env python3
"""Plays a fake vibecoding session so you can film Rotkin die and come back.

usage: python3 simulate.py [seconds between steps, default 1.5]
"""
import sys
import time

import rotkin

PAUSE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
# A bad session: a prompt every 2 minutes, one real request then four "fix it"s, Claude replying to each.
BAD_SESSION = ["Add pagination to the orders endpoint and keep the existing filters working",
               "fix it", "still broken", "try again", "same error"]
REPLY_TOKENS = 4000
THOUGHT = ("Claude moved the session cookie onto the API domain, because the frontend on localhost never sent it "
           "and every request went out without auth. The cookie domain now comes from config, and there is one "
           "test that logs in and fetches the profile, so I can see it working instead of asking for random fixes.")


def skip(s, minutes):
    """Pretend `minutes` passed by moving every timestamp into the past."""
    shift = minutes * 60 / rotkin.SPEED
    for key in ("tick", "last_prompt", "session_start", "doom_last", "think_at"):
        if s[key]:
            s[key] -= shift
    rotkin.tick(s)


def step(caption, event, *args):
    result = rotkin.apply(event, *args)
    v = rotkin.apply(rotkin.view)
    print(f"{caption:<46} rot {v['rot']:5.1f}  {v['stage']}" + ("  [BLOCKED]" if result is False else ""))
    time.sleep(PAUSE)


rotkin.apply(rotkin.reset)
print("Monday, 9am. A fresh pumpkin.\n")

minute = 0
while rotkin.apply(rotkin.on_prompt, BAD_SESSION[minute // 2 % len(BAD_SESSION)]):
    rotkin.apply(rotkin.on_tokens, REPLY_TOKENS)
    rotkin.apply(skip, 2)
    minute += 2
    if minute % 10 == 0:
        step(f"Bad session, {minute} min in", rotkin.view)

step("> one more try", rotkin.on_prompt, "one more try")
step("Think Mode: 'idk it broke'", rotkin.on_think, "idk it broke")
step("Touched grass", rotkin.on_grass)
step("> why does the cookie domain matter here?", rotkin.on_prompt, "why does the cookie domain matter here?")
step("Coffee break (11 min)", skip, 11)
step("Think Mode: explained what Claude built", rotkin.on_think, THOUGHT)
step("Lunch (15 min)", skip, 15)
