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
# Upstream shifts only RTL paragraphs whose lineLeft is zero. Once
# Latin names are aligned to the RTL column, this condition fails and those
# names drift away from the common right edge. Align by the rendered lineRight
# regardless of the paragraph's detected direction.
position_anchor = """                if (left == 0) {
                    if (widthpx < nameWidth) {
                        nameLeft += (nameWidth - widthpx);
                    }
                }"""
position_replacement = """                // Use the rendered line boundary for both Arabic and Latin.
                // Preserve Telegram's space reserved for verification icons.
                nameLeft += Math.max(0, Math.round(
                        nameWidth - nameLayout.getLineRight(0)));"""
if s.count(position_anchor) != 1:
    raise SystemExit("Dialog RTL name position anchor changed")
s = s.replace(position_anchor, position_replacement, 1)

# A verified-bot badge occupies the trailing name column. Reserve a
# small additional inset for wide Arabic glyphs and imported font metrics,
# including the two RTL/LTR positioning branches.
if s.count("nameWidth -= dp(21);") != 1 or s.count("nameLeft += dp(21);") != 2:
    raise SystemExit("Telegram verification badge positioning changed")
s = s.replace("nameWidth -= dp(21);", "nameWidth -= dp(27);", 1)
s = s.replace("nameLeft += dp(21);", "nameLeft += dp(27);")
p.write_text(s, encoding="utf-8")
print("Dialog names align to the RTL text column.")
