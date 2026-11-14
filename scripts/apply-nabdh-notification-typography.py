#!/usr/bin/env python3
"""Preserve the beginning of Arabic notification descriptions and honor fonts.

Telegram 13.2.2 NotificationsCheckCell uses an AnimatedTextView with
setEllipsizeByGradient(true). AnimatedTextDrawable draws that gradient at the
RIGHT edge even when text begins from RTL; it therefore fades the first Arabic
characters. Disable ONLY this cell's incorrect fade, retaining native END
ellipsis, switch interaction, icon alignment and height. Rebind selected
regular/medium fonts on recycled notification cells; LaunchActivity handles
explicit font-change remeasure and UI scaling.
"""
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-notification-typography.py TELEGRAM_SOURCE")
path = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Cells/NotificationsCheckCell.java"
s = path.read_text(encoding="utf-8")

def patch(old, new, label):
    global s
    hits = s.count(old)
    if hits != 1:
        raise SystemExit(f"Notification typography {label}: expected one anchor, found {hits}")
    s = s.replace(old, new, 1)

patch("        valueTextView.setEllipsizeByGradient(true);",
      """        // Native AnimatedTextDrawable always fades its RIGHT side.
        // Arabic starts on the right: the gradient hid the first word.
        // Keep native END ellipsis and full leading glyphs in both directions.
        valueTextView.setEllipsizeByGradient(false);""",
      "RTL leading-edge gradient")

patch("""        textView.setText(text);
        if (imageView != null) {""",
      """        // Refresh recycled native rows from the selected font family.
        // Explicit font-change remeasure is owned by LaunchActivity.
        textView.setTypeface(AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        valueTextView.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));
        multilineValueTextView.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));
        textView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);
        multilineValueTextView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);
        textView.setText(text);
        if (imageView != null) {""",
      "selected Arabic family on notification rebind")

path.write_text(s, encoding="utf-8")
print("PASS: notification RTL leading text visible; selected native Arabic fonts rebound")
