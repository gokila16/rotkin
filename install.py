#!/usr/bin/env python3
"""Adds Rotkin's hooks to ~/.claude/settings.json, keeping everything already there.

Usage: python3 install.py [path/to/rotkin.py]
The path defaults to the rotkin.py next to this file. Running it again replaces
Rotkin's old entries, so it also moves the hooks to a new path.
"""
import json
import shutil
import sys
import time
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "settings.json"
ROTKIN = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("rotkin.py")).resolve()
HOOKS = {"UserPromptSubmit": "prompt", "Stop": "stop"}


def is_rotkin(entry):
    return "rotkin.py" in entry.get("command", "")


settings = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
if SETTINGS.exists():
    backup = SETTINGS.with_name(f"settings.backup-{int(time.time())}.json")
    shutil.copy(SETTINGS, backup)
    print(f"Backed up settings to {backup}")

run = f'"{sys.executable}" "{ROTKIN}"'
hooks = settings.setdefault("hooks", {})
for event, kind in HOOKS.items():
    groups = []
    for group in hooks.get(event, []):
        group["hooks"] = [h for h in group.get("hooks", []) if not is_rotkin(h)]
        if group["hooks"]:
            groups.append(group)
    groups.append({"hooks": [{"type": "command", "command": f"{run} hook {kind}", "timeout": 5}]})
    hooks[event] = groups

# Pumpkin in the status line, unless you already have your own.
if "statusLine" not in settings or is_rotkin(settings["statusLine"]):
    settings["statusLine"] = {"type": "command", "command": f"{run} line"}

SETTINGS.parent.mkdir(exist_ok=True)
SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
print("🎃 Rotkin installed. Run `python3 server.py` and open http://localhost:8765")
