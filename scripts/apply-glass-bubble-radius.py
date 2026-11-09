#!/usr/bin/env python3
"""Set a subtly rounder default bubble shape, preserving saved user preferences."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-bubble-radius.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/messenger/SharedConfig.java"
s = p.read_text(encoding="utf-8")
anchors = (
    ('public static int bubbleRadius = 17;', 'public static int bubbleRadius = 19;'),
    ('bubbleRadius = preferences.getInt("bubbleRadius", 17);',
     'bubbleRadius = preferences.getInt("bubbleRadius", 19);'),
)
for old, new in anchors:
    if s.count(old) != 1:
        raise SystemExit(f"Bubble radius anchor changed: {old}")
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("Glass bubble default radius applied; saved preference retained.")
