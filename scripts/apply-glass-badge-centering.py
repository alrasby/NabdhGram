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
     "countTop + nabdhBadgeTextOffset(countAnimationStableLayout));\n                    countAnimationStableLayout.draw(canvas);"),
    ("countTop + dpf2(3f));\n                    countAnimationInLayout.draw(canvas);",
     "countTop + nabdhBadgeTextOffset(countAnimationInLayout));\n                    countAnimationInLayout.draw(canvas);"),
    ("countTop + dpf2(3f));\n                    countLayout.draw(canvas);",
     "countTop + nabdhBadgeTextOffset(countLayout));\n                    countLayout.draw(canvas);"),
    ("countTop + dpf2(3f));\n                    countOldLayout.draw(canvas);",
     "countTop + nabdhBadgeTextOffset(countOldLayout));\n                    countOldLayout.draw(canvas);"),
)
for old, new in replacements:
    if s.count(old) != 1:
        raise SystemExit(f"Badge text drawing anchor changed: {old[:65]}")
    s = s.replace(old, new, 1)
field_anchor = "    private boolean drawCount;"
if s.count(field_anchor) != 1:
    raise SystemExit("Unread badge text helper anchor changed")
s = s.replace(field_anchor, """    // Compute the real text baseline using the chosen font's ascent/descent.
    // StaticLayout height alone includes font padding and visually shifts digits.
    private float nabdhBadgeTextOffset(android.text.StaticLayout layout) {
        if (layout == null || layout.getLineCount() == 0) return dp(3);
        android.graphics.Paint.FontMetrics fm = Theme.dialogs_countTextPaint2.getFontMetrics();
        float glyphMiddle = layout.getLineBaseline(0) + (fm.ascent + fm.descent) / 2f;
        return dp(BADGE_SIZE) / 2f - glyphMiddle;
    }

""" + field_anchor, 1)
p.write_text(s, encoding="utf-8")
print("Unread count badge text centered for all animation states.")
