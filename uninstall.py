#!/usr/bin/env python3
"""Removes only ROTkin's hooks from ~/.claude/settings.json."""
import json

from install import SETTINGS, backup, is_rotkin, save

settings = json.loads(SETTINGS.read_text())
backup()

hooks = settings.get("hooks", {})
for event in list(hooks):
    for group in hooks[event]:
        group["hooks"] = [h for h in group.get("hooks", []) if not is_rotkin(h)]
    hooks[event] = [g for g in hooks[event] if g["hooks"]]
    if not hooks[event]:
        del hooks[event]
if not hooks:
    settings.pop("hooks", None)
if is_rotkin(settings.get("statusLine", {})):
    del settings["statusLine"]

save(settings)
print("ROTkin uninstalled. Your other hooks are untouched. RIP 🎃")
