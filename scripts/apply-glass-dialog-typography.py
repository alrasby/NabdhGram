#!/usr/bin/env python3
"""Align mixed-script dialog names with Telegram's RTL name column."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-dialog-typography.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java"
s = p.read_text(encoding="utf-8")
anchor = "            if (twoLinesForName) {\n                nameLayout = StaticLayoutEx.createStaticLayout("
if s.count(anchor) != 1:
    raise SystemExit("Dialog name layout anchor changed")
s = s.replace(anchor, """            // Keep Latin names on the same trailing edge as Arabic names.
            Layout.Alignment nabdhNameAlignment = LocaleController.isRTL
                    && !android.text.TextDirectionHeuristics.FIRSTSTRONG_RTL.isRtl(
                            nameStringFinal, 0, nameStringFinal.length())
                    ? Layout.Alignment.ALIGN_OPPOSITE : Layout.Alignment.ALIGN_NORMAL;
""" + anchor, 1)
for original in (
    "nameLayout = StaticLayoutEx.createStaticLayout(nameStringFinal, Theme.dialogs_namePaint[paintIndex], ellipsizeWidth, Layout.Alignment.ALIGN_NORMAL",
    "nameLayout = new StaticLayout(nameStringFinal, Theme.dialogs_namePaint[paintIndex], Math.max(ellipsizeWidth, nameWidth), Layout.Alignment.ALIGN_NORMAL",
):
    if s.count(original) != 1:
        raise SystemExit("Dialog name alignment anchor changed")
    s = s.replace(original, original.replace("Layout.Alignment.ALIGN_NORMAL", "nabdhNameAlignment"), 1)
p.write_text(s, encoding="utf-8")
print("Dialog names align to the RTL text column.")
