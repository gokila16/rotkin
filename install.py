#!/usr/bin/env python3
"""Adds ROTkin's hooks to ~/.claude/settings.json, keeping everything already there.

Usage: python3 install.py [path/to/rotkin.py]
The path defaults to the rotkin.py next to this file. Running it again replaces
ROTkin's old entries, so it also moves the hooks to a new path.
"""
import json
import os
import shlex
import shutil
import sys
import time
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "settings.json"
HOOKS = {"UserPromptSubmit": "prompt", "Stop": "stop"}
KEEP_BACKUPS = 3


def is_rotkin(entry):
    return "rotkin.py" in entry.get("command", "")


def backup():
    """Copy settings.json aside, keeping only the newest few of ROTkin's backups."""
    if not SETTINGS.exists():
        return
    path = SETTINGS.with_name(f"settings.backup-{int(time.time())}.json")
    shutil.copy2(SETTINGS, path)
    for old in sorted(SETTINGS.parent.glob("settings.backup-*.json"))[:-KEEP_BACKUPS]:
        old.unlink()
    print(f"Backed up settings to {path}")


def save(settings):
    """Write settings.json in one step, so a crash can't leave it half-written."""
    SETTINGS.parent.mkdir(exist_ok=True)
    tmp = SETTINGS.with_name(f".settings.rotkin-{os.getpid()}.tmp")
    tmp.write_text(json.dumps(settings, indent=2) + "\n")
    if SETTINGS.exists():
        shutil.copymode(SETTINGS, tmp)
    os.replace(tmp, SETTINGS)


def main(args):
    rotkin = Path(args[0] if args else Path(__file__).with_name("rotkin.py")).resolve()
    settings = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    backup()

    # Quoted for the shell, so an odd folder name can't break the command or run part of itself.
    run = f"{shlex.quote(sys.executable)} {shlex.quote(str(rotkin))}"
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

    save(settings)
    print("🎃 ROTkin installed. Run `python3 server.py` and open http://localhost:8765")


if __name__ == "__main__":
    main(sys.argv[1:])
