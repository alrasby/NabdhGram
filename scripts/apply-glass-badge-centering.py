#!/usr/bin/env python3
"""Center unread count text vertically inside Telegram's badge, including animations."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-badge-centering.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java"
s = p.read_text(encoding="utf-8")
# Telegram's fixed 3dp offset assumes the original font's metrics. Custom
# Arabic/Latin font families can have different ascent and descent values.
replacements = (
    ("countTop + dpf2(3f));\n                    countAnimationStableLayout.draw(canvas);",
     "countTop + (dp(BADGE_SIZE) - countAnimationStableLayout.getHeight()) / 2f);\n                    countAnimationStableLayout.draw(canvas);"),
    ("countTop + dpf2(3f));\n                    countAnimationInLayout.draw(canvas);",
     "countTop + (dp(BADGE_SIZE) - countAnimationInLayout.getHeight()) / 2f);\n                    countAnimationInLayout.draw(canvas);"),
    ("countTop + dpf2(3f));\n                    countLayout.draw(canvas);",
     "countTop + (dp(BADGE_SIZE) - countLayout.getHeight()) / 2f);\n                    countLayout.draw(canvas);"),
    ("countTop + dpf2(3f));\n                    countOldLayout.draw(canvas);",
     "countTop + (dp(BADGE_SIZE) - countOldLayout.getHeight()) / 2f);\n                    countOldLayout.draw(canvas);"),
)
for old, new in replacements:
    if s.count(old) != 1:
        raise SystemExit(f"Badge text drawing anchor changed: {old[:65]}")
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("Unread count badge text centered for all animation states.")
