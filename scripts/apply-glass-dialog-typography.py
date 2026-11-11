#!/usr/bin/env python3
"""Conservative mixed-script dialog name geometry for Telegram's native RTL layout.

Do not replace Telegram's paragraph alignment or move nameLeft by unbounded
line-right offsets: that pushed long mixed Arabic/Latin titles across avatars.
Only reserve an extra 6dp for verification badges using upstream positioning.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-dialog-typography.py TELEGRAM_SOURCE")

path = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java"
source = path.read_text(encoding="utf-8")
# Keep native ALIGN_NORMAL and its original conditional RTL nameLeft
# adjustment. It knows the glyph offset, avatar and reserved metadata width.
if source.count("nameWidth -= dp(21);") != 1:
    raise SystemExit("Verified nameWidth reservation changed")
if source.count("nameLeft += dp(21);") != 2:
    raise SystemExit("Verified name positioning changed")
source = source.replace("nameWidth -= dp(21);", "nameWidth -= dp(27);", 1)
source = source.replace("nameLeft += dp(21);", "nameLeft += dp(27);")
path.write_text(source, encoding="utf-8")
print("PASS: native mixed RTL layout preserved; verification badges reserve extra 6dp")
