#!/usr/bin/env python3
"""Removes only Rotkin's hooks from ~/.claude/settings.json."""
import json
import shutil
import time
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "settings.json"

settings = json.loads(SETTINGS.read_text())
shutil.copy(SETTINGS, SETTINGS.with_name(f"settings.backup-{int(time.time())}.json"))

hooks = settings.get("hooks", {})
for event in list(hooks):
    for group in hooks[event]:
        group["hooks"] = [h for h in group.get("hooks", []) if "rotkin.py" not in h.get("command", "")]
    hooks[event] = [g for g in hooks[event] if g["hooks"]]
    if not hooks[event]:
        del hooks[event]
if not hooks:
    settings.pop("hooks", None)
if "rotkin.py" in settings.get("statusLine", {}).get("command", ""):
    del settings["statusLine"]

SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
print("Rotkin uninstalled. Your other hooks are untouched. RIP 🎃")
